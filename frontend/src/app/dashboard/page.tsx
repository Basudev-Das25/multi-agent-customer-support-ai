"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { parseApiError } from "@/lib/api-helpers";
import { getCurrentUser } from "@/services/auth";
import { useAuthStore } from "@/store/auth";
import ChatInput from "@/components/chat/ChatInput";
import ChatWindow from "@/components/chat/ChatWindow";
import ConversationSidebar from "@/components/chat/ConversationSidebar";
import {
    getConversation,
    listConversations,
    sendMessage,
} from "@/services/chat";
import type {
    Conversation,
    ConversationSummary,
} from "@/types/chat";

export default function DashboardPage() {
    const router = useRouter();
    const token = useAuthStore((state) => state.token);
    const user = useAuthStore((state) => state.user);
    const setToken = useAuthStore((state) => state.setToken);
    const setUser = useAuthStore((state) => state.setUser);

    const [conversations, setConversations] = useState<
        ConversationSummary[]
    >([]);
    const [conversation, setConversation] =
        useState<Conversation | null>(null);
    const [error, setError] = useState("");
    const [isLoadingHistory, setIsLoadingHistory] = useState(true);
    const [isSending, setIsSending] = useState(false);
    const [sidebarOpen, setSidebarOpen] = useState(false);

    // Auth gate + profile load
    useEffect(() => {
        const stored = localStorage.getItem("access_token");
        if (!stored) {
            router.replace("/login");
            return;
        }

        if (!token) setToken(stored);

        if (!user) {
            getCurrentUser()
                .then((profile) => setUser(profile))
                .catch(() => router.replace("/login"));
        }
    }, []); // eslint-disable-line react-hooks/exhaustive-deps

    const loadConversations = useCallback(async () => {
        setIsLoadingHistory(true);
        try {
            setConversations(await listConversations());
        } catch (requestError) {
            setError(
                parseApiError(
                    requestError,
                    "Unable to load conversation history.",
                ),
            );
        } finally {
            setIsLoadingHistory(false);
        }
    }, []);

    useEffect(() => {
        if (token && user) {
            const timeout = window.setTimeout(
                () => {
                    void loadConversations();
                },
                0,
            );
            return () => window.clearTimeout(timeout);
        }
    }, [token, user, loadConversations]);

    async function selectConversation(conversationId: string) {
        setError("");
        setSidebarOpen(false);
        try {
            setConversation(
                await getConversation(conversationId),
            );
        } catch (requestError) {
            setError(
                parseApiError(
                    requestError,
                    "Unable to open this conversation.",
                ),
            );
        }
    }

    async function handleSend(message: string) {
        setIsSending(true);
        setError("");
        try {
            const updatedConversation = await sendMessage(
                message,
                conversation?.id,
            );
            setConversation(updatedConversation);
            await loadConversations();
        } catch (requestError) {
            setError(
                parseApiError(
                    requestError,
                    "Unable to send your message.",
                ),
            );
        } finally {
            setIsSending(false);
        }
    }

    function logout() {
        localStorage.removeItem("access_token");
        setToken(null);
        setUser(null);
        router.replace("/login");
    }

    return (
        <main className="h-dvh overflow-hidden">
            <div className="flex h-full min-h-0 flex-col md:flex-row">
                {/* Mobile sidebar toggle */}
                <div className="flex items-center gap-3 glass-heavy border-b border-white/[0.08] px-4 py-3 md:hidden">
                    <button
                        type="button"
                        onClick={() => setSidebarOpen(true)}
                        aria-label="Open conversation list"
                        className="rounded-lg p-2 text-foreground-muted transition-all duration-200 hover:bg-surface-hover hover:text-foreground"
                    >
                        <svg
                            className="h-5 w-5"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                            strokeWidth={2}
                        >
                            <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                d="M4 6h16M4 12h16M4 18h16"
                            />
                        </svg>
                    </button>

                    <p className="text-sm font-semibold text-foreground">
                        {conversation?.title ?? "New conversation"}
                    </p>
                </div>

                <ConversationSidebar
                    conversations={conversations}
                    activeConversationId={conversation?.id ?? null}
                    onSelectConversation={selectConversation}
                    onNewConversation={() => {
                        setConversation(null);
                        setError("");
                        setSidebarOpen(false);
                    }}
                    onLogout={logout}
                    isLoading={isLoadingHistory}
                    isAdmin={user?.role === "admin"}
                    open={sidebarOpen}
                    onClose={() => setSidebarOpen(false)}
                />

                <div className="flex min-h-0 flex-1 flex-col">
                    <ChatWindow
                        conversation={conversation}
                        error={error}
                        isLoading={isSending}
                    />
                    <ChatInput
                        onSend={handleSend}
                        disabled={isSending}
                    />
                </div>
            </div>
        </main>
    );
}
