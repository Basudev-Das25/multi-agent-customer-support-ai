import api from "@/services/api";
import type {
    DatasetIngestionResponse,
    DatasetResponse,
    KnowledgeDocumentResponse,
    RetrievalResult,
} from "@/types/knowledge";

export async function uploadDocument(
    file: File,
    onProgress?: (percent: number) => void,
): Promise<KnowledgeDocumentResponse> {
    const formData = new FormData();
    formData.append("file", file);

    const response = await api.post<KnowledgeDocumentResponse>(
        "/knowledge/upload",
        formData,
        {
            headers: { "Content-Type": "multipart/form-data" },
            onUploadProgress: onProgress
                ? (event) => {
                      if (event.total) {
                          onProgress(
                              Math.round(
                                  (event.loaded * 100) / event.total,
                              ),
                          );
                      }
                  }
                : undefined,
        },
    );

    return response.data;
}

export async function listDocuments(): Promise<
    KnowledgeDocumentResponse[]
> {
    const response =
        await api.get<KnowledgeDocumentResponse[]>("/knowledge");
    return response.data;
}

export async function searchDocuments(
    query: string,
): Promise<RetrievalResult[]> {
    const response = await api.get<RetrievalResult[]>(
        "/knowledge/search",
        { params: { query } },
    );
    return response.data;
}

export async function deleteDocument(
    documentId: string,
): Promise<void> {
    await api.delete(`/knowledge/${documentId}`);
}

export async function listDatasets(): Promise<
    DatasetResponse[]
> {
    const response =
        await api.get<DatasetResponse[]>("/knowledge/datasets");
    return response.data;
}

export async function ingestDatasets(
    dataset?: string,
    force: boolean = false,
): Promise<DatasetIngestionResponse> {
    const response = await api.post<DatasetIngestionResponse>(
        "/knowledge/ingest-datasets",
        { dataset: dataset || null, force },
    );
    return response.data;
}
