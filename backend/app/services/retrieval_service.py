from bson import ObjectId

from app.database.collections import get_knowledge_chunks_collection
from app.schemas.retrieval import RetrievalResult
from app.services.embedding_service import embedding_service
from app.services.vector_service import vector_service


class RetrievalService:
    """
    Retrieves relevant chunks for a user query.
    """

    async def retrieve(
        self,
        *,
        query: str,
        user_id: str,
        k: int = 5,
    ) -> list[RetrievalResult]:

        query_embedding = embedding_service.embed(query)

        search_results = vector_service.search(
            query_embedding,
            k=k,
        )

        if not search_results:
            return []

        collection = get_knowledge_chunks_collection()

        expanded_chunks: dict[str, RetrievalResult] = {}

        for result in search_results:

            document = await collection.find_one(
                {
                    "_id": ObjectId(result.chunk_id),
                    "user_id": user_id,
                }
            )

            if document is None:
                continue

            cursor = collection.find(
                {
                    "document_id": document["document_id"],
                    "page_number": document["page_number"],
                    "chunk_index": {
                        "$gte": document["chunk_index"] - 1,
                        "$lte": document["chunk_index"] + 1,
                    },
                    "user_id": user_id,
                }
            )

            neighbours = await cursor.to_list(length=None)

            for chunk in neighbours:

                chunk_id = str(chunk["_id"])

                score = result.score if chunk_id == result.chunk_id else 0.0

                expanded_chunks[chunk_id] = RetrievalResult(
                    chunk_id=chunk_id,
                    document_id=chunk["document_id"],
                    page_number=chunk["page_number"],
                    chunk_index=chunk["chunk_index"],
                    text=chunk["text"],
                    score=score,
                )

        retrieval_results = sorted(
            expanded_chunks.values(),
            key=lambda chunk: (
                chunk.page_number,
                chunk.chunk_index,
            ),
        )

        return retrieval_results

    async def build_context(
        self,
        *,
        query: str,
        user_id: str,
        k: int = 5,
    ) -> str:

        chunks = await self.retrieve(
            query=query,
            user_id=user_id,
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


retrieval_service = RetrievalService()
