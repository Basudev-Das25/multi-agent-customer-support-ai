from app.schemas.chat import SourceInfo
from app.schemas.retrieval import RetrievalResult
from app.services.embedding_service import embedding_service
from app.services.storage import ChunkStorage, LocalChunkStorage
from app.services.vector_service import vector_service


class RetrievalService:
    """
    Retrieves relevant chunks for a user query.
    """

    def __init__(self, chunk_storage: ChunkStorage | None = None) -> None:
        """Initialize retrieval with the canonical global chunk storage."""

        self.chunk_storage = (
            chunk_storage if chunk_storage is not None else LocalChunkStorage()
        )

    async def retrieve(
        self,
        *,
        query: str,
        k: int = 5,
    ) -> list[RetrievalResult]:

        query_embedding = embedding_service.embed(query)

        search_results = vector_service.search(
            query_embedding,
            k=k,
        )

        if not search_results:
            return []

        expanded_chunks: dict[tuple[str, str], RetrievalResult] = {}
        direct_hit_chunks: set[tuple[str, str]] = set()

        for result in search_results:
            neighbours = await self.chunk_storage.get_chunk_window(
                document_id=result.document_id,
                chunk_id=result.chunk_id,
                before=1,
                after=1,
            )

            for chunk in neighbours:
                if chunk.id is None:
                    continue

                chunk_key = (chunk.document_id, chunk.id)
                is_direct_hit = chunk.id == result.chunk_id
                score = result.score if is_direct_hit else 0.0
                existing = expanded_chunks.get(chunk_key)

                if is_direct_hit:
                    direct_hit_chunks.add(chunk_key)
                elif chunk_key in direct_hit_chunks:
                    continue

                if existing is not None and not is_direct_hit:
                    continue

                expanded_chunks[chunk_key] = RetrievalResult(
                    chunk_id=chunk.id,
                    document_id=chunk.document_id,
                    page_number=chunk.page_number,
                    chunk_index=chunk.chunk_index,
                    text=chunk.text,
                    score=score,
                )

        retrieval_results = sorted(
            expanded_chunks.values(),
            key=lambda chunk: (
                chunk.document_id,
                chunk.page_number,
                chunk.chunk_index,
            ),
        )

        return retrieval_results

    async def build_context(
        self,
        *,
        query: str,
        k: int = 5,
    ) -> str:

        chunks = await self.retrieve(
            query=query,
            k=k,
        )

        if not chunks:
            return ""

        context = []

        current_page = None

        for chunk in chunks:

            if chunk.page_number != current_page:

                current_page = chunk.page_number

                context.append(f"\n=== Page {current_page} ===\n")

            context.append(chunk.text)

        return "\n\n".join(context)

    async def build_response(
        self,
        *,
        query: str,
        k: int = 5,
    ) -> tuple[str, list[SourceInfo]]:
        """
        Build context string and source metadata for a query.

        Returns (context_string, list_of_source_info).
        """

        chunks = await self.retrieve(query=query, k=k)

        if not chunks:
            return "", []

        # Build context string (same as build_context)
        context_parts: list[str] = []
        current_page = None
        for chunk in chunks:
            if chunk.page_number != current_page:
                current_page = chunk.page_number
                context_parts.append(f"\n=== Page {current_page} ===\n")
            context_parts.append(chunk.text)
        context = "\n\n".join(context_parts)

        # Build source info — look up document names from MongoDB
        source_info = await self._resolve_sources(chunks)

        return context, source_info

    async def _resolve_sources(
        self,
        chunks: list[RetrievalResult],
    ) -> list[SourceInfo]:
        """Map retrieval results to SourceInfo with document names."""

        from app.database.collections import get_knowledge_collection

        # Collect unique document IDs
        doc_ids = list({c.document_id for c in chunks})

        # Batch lookup document names
        collection = get_knowledge_collection()
        from bson import ObjectId

        doc_names: dict[str, str] = {}
        valid_ids = [ObjectId(did) for did in doc_ids if ObjectId.is_valid(did)]
        if valid_ids:
            cursor = collection.find(
                {"_id": {"$in": valid_ids}},
                {"original_filename": 1},
            )
            async for doc in cursor:
                doc_names[str(doc["_id"])] = doc.get("original_filename", "Unknown")

        # Build SourceInfo for each chunk
        # (deduplicated by document_id, keeping best score)
        seen_docs: dict[str, SourceInfo] = {}
        for chunk in chunks:
            doc_id = chunk.document_id
            if doc_id not in seen_docs or chunk.score > seen_docs[doc_id].score:
                seen_docs[doc_id] = SourceInfo(
                    document_id=doc_id,
                    document_name=doc_names.get(doc_id, "Unknown document"),
                    text_preview=chunk.text[:200]
                    + ("..." if len(chunk.text) > 200 else ""),
                    score=chunk.score,
                    page_number=chunk.page_number,
                )

        return sorted(seen_docs.values(), key=lambda s: s.score, reverse=True)


retrieval_service = RetrievalService()
