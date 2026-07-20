"use client";

import { useCallback, useEffect, useRef } from "react";
import Link from "next/link";

import type { ConversationSummary } from "@/types/chat";

interface ConversationSidebarProps {
    conversations: ConversationSummary[];
    activeConversationId: string | null;
    onSelectConversation: (conversationId: string) => void;
    onNewConversation: () => void;
    onLogout: () => void;
    isLoading?: boolean;
    isAdmin?: boolean;
    open?: boolean;
    onClose?: () => void;
}

// ---------------------------------------------------------------------------
// Skeleton placeholder (shimmer)
// ---------------------------------------------------------------------------

function Skeleton() {
    return (
        <div className="space-y-2 px-1">
            {[1, 2, 3].map((n) => (
                <div
                    key={n}
                    className="h-16 shimmer rounded-xl"
                />
            ))}
        </div>
    );
}

// ---------------------------------------------------------------------------
// Conversation item
// ---------------------------------------------------------------------------

function ConversationItem({
    conversation,
    isActive,
    onSelect,
    onClose,
}: {
    conversation: ConversationSummary;
    isActive: boolean;
    onSelect: (id: string) => void;
    onClose?: () => void;
}) {
    const handleClick = useCallback(() => {
        onSelect(conversation.id);
        onClose?.();
    }, [conversation.id, onSelect, onClose]);

    const handleKeyDown = useCallback(
        (event: React.KeyboardEvent) => {
            if (event.key === "Enter" || event.key === " ") {
                event.preventDefault();
                handleClick();
            }
        },
        [handleClick],
    );

    return (
        <button
            type="button"
            onClick={handleClick}
            onKeyDown={handleKeyDown}
            role="listitem"
            aria-current={isActive ? "page" : undefined}
            className={`w-full rounded-xl px-3 py-3 text-left transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-accent/60 ${
                isActive
                    ? "bg-accent/15 text-accent shadow-lg shadow-accent/10 border border-accent/20"
                    : "text-foreground-muted hover:bg-surface-hover hover:translate-x-1"
            }`}
        >
            <p className="truncate text-sm font-semibold">
                {conversation.title}
            </p>
            <p className="mt-1 text-xs opacity-65">
                {new Date(
                    conversation.updated_at,
                ).toLocaleDateString(undefined, {
                    month: "short",
                    day: "numeric",
                })}
            </p>
        </button>
    );
}

// ---------------------------------------------------------------------------
// ConversationSidebar (main export)
// ---------------------------------------------------------------------------

export default function ConversationSidebar({
    conversations,
    activeConversationId,
    onSelectConversation,
    onNewConversation,
    onLogout,
    isLoading,
    isAdmin,
    open = true,
    onClose,
}: ConversationSidebarProps) {
    const asideRef = useRef<HTMLElement>(null);

    // Close sidebar on Escape key
    useEffect(() => {
        const el = asideRef.current;
        if (!el) return;

        function handleKey(event: KeyboardEvent) {
            if (event.key === "Escape" && onClose) onClose();
        }
        el.addEventListener("keydown", handleKey);
        return () => el.removeEventListener("keydown", handleKey);
    }, [onClose]);

    // Focus trap: focus first focusable element when opened
    const newBtnRef = useRef<HTMLButtonElement>(null);
    useEffect(() => {
        if (open) {
            // Small delay so the transition completes
            const t = setTimeout(
                () => newBtnRef.current?.focus(),
                100,
            );
            return () => clearTimeout(t);
        }
    }, [open]);

    return (
        <>
            {/* Mobile overlay */}
            {open && onClose && (
                <div
                    className="fixed inset-0 z-30 bg-black/50 animate-overlay-in md:hidden"
                    onClick={onClose}
                    aria-hidden="true"
                />
            )}

            <aside
                ref={asideRef}
                role="navigation"
                aria-label="Conversation history"
                className={`flex h-full min-h-0 w-full flex-col border-b border-white/[0.08] glass-heavy transition-all duration-300 ease-out md:w-80 md:border-b-0 md:border-r md:border-white/[0.08] ${
                    onClose === undefined
                        ? ""
                        : open
                          ? "fixed inset-y-0 left-0 z-40 w-80 translate-x-0 md:relative md:z-auto md:translate-x-0"
                          : "fixed inset-y-0 left-0 z-40 w-80 -translate-x-full md:relative md:z-auto md:translate-x-0"
                }`}
            >
                {/* Header */}
                <div className="border-b border-white/[0.08] p-5">
                    <div className="flex items-start justify-between gap-3">
                        <div>
                            <p className="text-xs font-bold uppercase tracking-[0.22em] text-accent">
                                Support AI
                            </p>
                            <h1 className="mt-1 text-xl font-semibold text-foreground">
                                Workspace
                            </h1>
                        </div>
                        <span className="animate-pulse-soft rounded-full border border-accent/20 bg-accent-muted px-2.5 py-1 text-xs font-medium text-accent">
                            Online
                        </span>
                    </div>

                    <button
                        ref={newBtnRef}
                        type="button"
                        onClick={() => {
                            onNewConversation();
                            onClose?.();
                        }}
                        aria-label="Start new conversation"
                        className="btn-press mt-5 flex w-full items-center justify-center gap-2 rounded-xl bg-accent px-4 py-3 text-sm font-bold text-background transition-all duration-200 hover:bg-accent-hover hover:shadow-[0_0_20px_rgba(167,139,250,0.3)] focus:outline-none focus:ring-2 focus:ring-accent-hover active:scale-[0.97]"
                    >
                        <span className="text-lg leading-none" aria-hidden="true">
                            +
                        </span>
                        New conversation
                    </button>
                </div>

                {/* Admin link */}
                {isAdmin && (
                    <div className="border-b border-white/[0.08] px-4 py-3">
                        <Link
                            href="/admin/knowledge"
                            onClick={onClose}
                            className="flex items-center gap-2 rounded-xl px-3 py-2 text-sm font-medium text-foreground-muted transition-all duration-200 hover:bg-surface-hover hover:text-accent focus:outline-none focus:ring-2 focus:ring-accent/60"
                        >
                            <span className="text-base" aria-hidden="true">
                                ⚙
                            </span>
                            Knowledge Base
                        </Link>
                    </div>
                )}

                {/* Conversation list */}
                <div
                    className="min-h-0 flex-1 overflow-y-auto p-3"
                    role="list"
                    aria-label="Conversation history"
                >
                    <p className="px-2 pb-2 text-xs font-semibold uppercase tracking-wider text-foreground-dim">
                        History
                    </p>

                    {isLoading ? (
                        <Skeleton />
                    ) : conversations.length === 0 ? (
                        <p className="px-2 py-8 text-center text-sm text-foreground-dim">
                            Your previous conversations will appear
                            here.
                        </p>
                    ) : (
                        <div className="space-y-1 stagger-list">
                            {conversations.map((c) => (
                                <ConversationItem
                                    key={c.id}
                                    conversation={c}
                                    isActive={
                                        activeConversationId === c.id
                                    }
                                    onSelect={onSelectConversation}
                                    onClose={onClose}
                                />
                            ))}
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="border-t border-white/[0.08] p-4">
                    <button
                        type="button"
                        onClick={onLogout}
                        aria-label="Sign out"
                        className="btn-press w-full rounded-xl border border-white/10 px-4 py-2.5 text-sm font-semibold text-foreground-muted transition-all duration-200 hover:border-danger/60 hover:bg-danger-muted hover:text-danger focus:outline-none focus:ring-2 focus:ring-danger/60 active:scale-[0.97]"
                    >
                        Sign out
                    </button>
                </div>
            </aside>
        </>
    );
}
