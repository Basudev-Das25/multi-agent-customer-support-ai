import api from "@/services/api";
import type {
    Conversation,
    ConversationSummary,
} from "@/types/chat";

export const listConversations = async () => {
    const response = await api.get<ConversationSummary[]>(
        "/chat/conversations"
    );

    return response.data;
};

export const getConversation = async (
    conversationId: string
) => {
    const response = await api.get<Conversation>(
        `/chat/conversations/${conversationId}`
    );

    return response.data;
};

export const sendMessage = async (
    content: string,
    conversationId?: string
) => {
    const response = await api.post<Conversation>(
        "/chat/messages",
        {
            content,
            conversation_id: conversationId,
        }
    );

    return response.data;
};