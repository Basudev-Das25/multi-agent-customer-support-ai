import { apiRequest } from "@/services/api";
import type { Conversation, ConversationSummary } from "@/types/chat";

export const listConversations = () =>
  apiRequest<ConversationSummary[]>("/chat/conversations");

export const getConversation = (conversationId: string) =>
  apiRequest<Conversation>(`/chat/conversations/${conversationId}`);

export const sendMessage = (content: string, conversationId?: string) =>
  apiRequest<Conversation>("/chat/messages", {
    method: "POST",
    body: JSON.stringify({ content, conversation_id: conversationId }),
  });
