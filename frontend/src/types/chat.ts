export type MessageRole = "user" | "assistant";

export interface SourceInfo {
    document_id: string;
    document_name: string;
    text_preview: string;
    score: number;
    page_number: number;
}

export interface ChatMessageMetadata {
    agent_name: string;
    sources: SourceInfo[];
}

export interface ChatMessage {
    id: string;
    role: MessageRole;
    content: string;
    created_at: string;
    metadata?: ChatMessageMetadata;
}

export interface Conversation {
    id: string;
    title: string;
    messages: ChatMessage[];
    created_at: string;
    updated_at: string;
}

export interface ConversationSummary {
    id: string;
    title: string;
    updated_at: string;
}
