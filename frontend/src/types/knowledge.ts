export interface KnowledgeDocumentResponse {
    id: string;
    user_id: string;
    filename: string;
    original_filename: string;
    content_type: string;
    file_size: number;
    page_count: number;
    chunk_count: number;
    status: string;
    source: string;
    uploaded_at: string;
}

export interface RetrievalResult {
    chunk_id: string;
    document_id: string;
    page_number: number;
    chunk_index: number;
    text: string;
    score: number;
}

export interface DatasetResponse {
    name: string;
    display_name: string;
    description: string;
    source: string;
    is_ingested: boolean;
    document_count: number;
    chunk_count: number;
    ingested_at: string | null;
}

export interface DatasetIngestionResponse {
    ingested: string[];
    skipped: string[];
    failed: string[][];
    message: string;
}
