"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Markdown from "@/components/shared/Markdown";
import type { ChatMessage, ChatMessageMetadata, Conversation, SourceInfo } from "@/types/chat";

interface ChatWindowProps {
    conversation: Conversation | null;
    error?: string;
    isLoading?: boolean;
}

// ---------------------------------------------------------------------------
// Agent badge colors
// ---------------------------------------------------------------------------

const AGENT_COLORS: Record<string, string> = {
    faq: "bg-accent-muted text-accent",
    billing: "bg-accent-warm-muted text-accent-warm",
    technical: "bg-accent-cool-muted text-accent-cool",
    product: "bg-success-muted text-success",
    complaint: "bg-danger-muted text-danger",
};

function getAgentColor(name: string): string {
    return AGENT_COLORS[name] ?? "bg-surface text-foreground-muted";
}

function getAgentLabel(name: string): string {
    const labels: Record<string, string> = {
        faq: "FAQ Agent",
        billing: "Billing Agent",
        technical: "Technical Agent",
        product: "Product Agent",
        complaint: "Complaint Agent",
    };
    return labels[name] ?? name;
}

// ---------------------------------------------------------------------------
// Copy button
// ---------------------------------------------------------------------------

function CopyButton({ text }: { text: string }) {
    const [copied, setCopied] = useState(false);
    const handleClick = useCallback(async () => {
        try {
            await navigator.clipboard.writeText(text);
            setCopied(true);
            setTimeout(() => setCopied(false), 1500);
        } catch {
            // Clipboard not available
        }
    }, [text]);

    return (
        <button
            type="button"
            onClick={handleClick}
            aria-label="Copy message"
            className="rounded-md p-1.5 text-foreground-dim opacity-0 transition-all duration-200 group-hover/message:opacity-100 hover:bg-surface-hover hover:text-foreground focus:opacity-100 focus:outline-none focus:ring-2 focus:ring-accent/60"
        >
            {copied ? (
                <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                </svg>
            ) : (
                <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
                    <path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1" />
                </svg>
            )}
        </button>
    );
}

// ---------------------------------------------------------------------------
// Avatar
// ---------------------------------------------------------------------------

function Avatar({ role }: { role: "user" | "assistant" }) {
    return (
        <div
            className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs font-bold ${
                role === "user"
                    ? "bg-accent-muted text-accent"
                    : "bg-surface text-foreground-muted"
            }`}
            aria-hidden="true"
        >
            {role === "user" ? "U" : "AI"}
        </div>
    );
}

// ---------------------------------------------------------------------------
// Timestamp
// ---------------------------------------------------------------------------

function Timestamp({ iso }: { iso: string }) {
    const date = new Date(iso);
    const label = date.toLocaleTimeString(undefined, {
        hour: "2-digit",
        minute: "2-digit",
    });
    return (
        <time
            dateTime={iso}
            className="text-[11px] text-foreground-dim"
        >
            {label}
        </time>
    );
}

// ---------------------------------------------------------------------------
// Loading dots (typing animation — smoother pulse)
// ---------------------------------------------------------------------------

function LoadingDots() {
    return (
        <span className="inline-flex gap-1" aria-label="Assistant is typing">
            <i className="h-1.5 w-1.5 rounded-full bg-accent typing-dot-1" />
            <i className="h-1.5 w-1.5 rounded-full bg-accent typing-dot-2" />
            <i className="h-1.5 w-1.5 rounded-full bg-accent typing-dot-3" />
        </span>
    );
}

// ---------------------------------------------------------------------------
// Sources panel (collapsible)
// ---------------------------------------------------------------------------

function SourcesPanel({ metadata }: { metadata: ChatMessageMetadata }) {
    const [expanded, setExpanded] = useState(false);
    const { agent_name, sources } = metadata;

    if (!sources || sources.length === 0) return null;

    return (
        <div className="mt-3 border-t border-white/[0.06] pt-3 animate-fade-in-up">
            {/* Agent badge + source count */}
            <button
                type="button"
                onClick={() => setExpanded(!expanded)}
                className="flex w-full items-center gap-2 text-left transition-all duration-200 hover:opacity-80"
            >
                <span
                    className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold ${getAgentColor(agent_name)}`}
                >
                    {getAgentLabel(agent_name)}
                </span>
                <span className="text-[11px] text-foreground-dim">
                    {sources.length} source{sources.length !== 1 ? "s" : ""}
                </span>
                <svg
                    className={`ml-auto h-3 w-3 text-foreground-dim transition-transform duration-200 ${expanded ? "rotate-180" : ""}`}
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={2}
                >
                    <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                </svg>
            </button>

            {/* Expanded source list */}
            {expanded && (
                <div className="mt-2 space-y-2 stagger-list">
                    {sources.map((source) => (
                        <SourceCard key={source.document_id} source={source} />
                    ))}
                </div>
            )}
        </div>
    );
}

// ---------------------------------------------------------------------------
// Source card (individual source)
// ---------------------------------------------------------------------------

function SourceCard({ source }: { source: SourceInfo }) {
    const [showFull, setShowFull] = useState(false);

    // Clean up document name — extract the meaningful part
    const displayName = source.document_name
        .split(" / ")
        .pop() ?? source.document_name;

    const dataset = source.document_name.split(" / ")[0] ?? "";

    return (
        <div className="rounded-lg border border-white/[0.06] bg-background-elevated/50 px-3 py-2">
            <div className="flex items-center justify-between gap-2">
                <div className="min-w-0 flex-1">
                    <p className="truncate text-[11px] font-medium text-foreground">
                        {displayName}
                    </p>
                    {dataset && (
                        <p className="text-[10px] text-foreground-dim">
                            {dataset}
                        </p>
                    )}
                </div>
                <span className="shrink-0 rounded-full bg-accent-muted px-1.5 py-0.5 text-[9px] font-semibold text-accent">
                    {source.score.toFixed(2)}
                </span>
            </div>

            <p className={`mt-1 text-[11px] leading-4 text-foreground-muted ${showFull ? "" : "line-clamp-2"}`}>
                {source.text_preview}
            </p>

            {source.text_preview.length > 100 && (
                <button
                    type="button"
                    onClick={() => setShowFull(!showFull)}
                    className="mt-0.5 text-[10px] text-accent hover:text-accent-hover transition-colors"
                >
                    {showFull ? "Show less" : "Show more"}
                </button>
            )}
        </div>
    );
}

// ---------------------------------------------------------------------------
// Message bubble
// ---------------------------------------------------------------------------

function MessageBubble({ message }: { message: ChatMessage }) {
    const isUser = message.role === "user";

    return (
        <article
            className={`group/message animate-message-in flex gap-3 ${isUser ? "justify-end" : "justify-start"}`}
            aria-label={`${isUser ? "Your" : "Support AI"} message`}
        >
            {!isUser && <Avatar role="assistant" />}

            <div
                className={`max-w-[88%] rounded-2xl px-4 py-3 shadow-sm md:max-w-[75%] transition-all duration-200 ${
                    isUser
                        ? "rounded-br-md bg-gradient-to-br from-accent to-accent-active text-background"
                        : "rounded-bl-md border border-white/10 bg-surface/60 backdrop-blur-sm text-foreground"
                }`}
            >
                {/* Header row */}
                <div className="mb-1 flex items-center justify-between gap-3">
                    <p className="text-[11px] font-bold uppercase tracking-wider opacity-60">
                        {isUser ? "You" : "Support AI"}
                    </p>
                    <div className="flex items-center gap-1.5">
                        <Timestamp iso={message.created_at} />
                        <CopyButton text={message.content} />
                    </div>
                </div>

                {/* Content */}
                {isUser ? (
                    <p className="whitespace-pre-wrap text-sm leading-6">
                        {message.content}
                    </p>
                ) : (
                    <Markdown content={message.content} />
                )}

                {/* Sources panel (assistant messages only) */}
                {!isUser && message.metadata && (
                    <SourcesPanel metadata={message.metadata} />
                )}
            </div>

            {isUser && <Avatar role="user" />}
        </article>
    );
}

// ---------------------------------------------------------------------------
// Empty state
// ---------------------------------------------------------------------------

function EmptyState() {
    return (
        <div className="my-auto pt-20 text-center animate-fade-in-up">
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-accent-muted text-2xl text-accent animate-float">
                ✦
            </div>
            <h2 className="mt-5 text-2xl font-semibold text-foreground">
                How can we help?
            </h2>
            <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-foreground-muted">
                Ask about billing, product features, technical issues,
                complaints, or company policies.
            </p>
        </div>
    );
}

// ---------------------------------------------------------------------------
// ChatWindow (main export)
// ---------------------------------------------------------------------------

export default function ChatWindow({
    conversation,
    error,
    isLoading,
}: ChatWindowProps) {
    const containerRef = useRef<HTMLDivElement>(null);
    const bottomRef = useRef<HTMLDivElement>(null);
    const [userScrolledUp, setUserScrolledUp] = useState(false);

    // Detect when user scrolls away from bottom
    const handleScroll = useCallback(() => {
        const el = containerRef.current;
        if (!el) return;
        const threshold = 60;
        const atBottom =
            el.scrollHeight - el.scrollTop - el.clientHeight < threshold;
        setUserScrolledUp(!atBottom);
    }, []);

    // Auto-scroll on new messages unless user scrolled up.
    // Also scroll to bottom when a new message is being sent (isLoading toggles).
    useEffect(() => {
        if (!userScrolledUp || isLoading) {
            bottomRef.current?.scrollIntoView({ behavior: "smooth" });
        }
    }, [conversation?.messages.length, isLoading, userScrolledUp]);

    const messages = conversation?.messages ?? [];
    const hasMessages = messages.length > 0;

    return (
        <section
            className="flex min-h-0 flex-1 flex-col bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-surface via-background to-background"
            aria-label="Chat messages"
        >
            {/* Header */}
            <header className="glass-light border-b border-white/[0.08] px-5 py-4 backdrop-blur md:px-8 animate-fade-in">
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-accent">
                    Customer support assistant
                </p>
                <h2 className="mt-1 truncate text-lg font-semibold text-foreground">
                    {conversation?.title ?? "New conversation"}
                </h2>
            </header>

            {/* Messages */}
            <div
                ref={containerRef}
                onScroll={handleScroll}
                className="min-h-0 flex-1 overflow-y-auto px-5 py-7 md:px-10"
                role="log"
                aria-label="Messages"
                aria-live="polite"
            >
                <div className="mx-auto flex max-w-4xl flex-col gap-5">
                    {!hasMessages && !isLoading && <EmptyState />}

                    {hasMessages &&
                        messages.map((message) => (
                            <MessageBubble
                                key={message.id}
                                message={message}
                            />
                        ))}

                    {/* Typing indicator */}
                    {isLoading && (
                        <div className="flex justify-start animate-message-in">
                            <div className="flex items-center gap-2">
                                <Avatar role="assistant" />
                                <div className="rounded-2xl rounded-bl-md border border-white/10 bg-surface/60 px-4 py-3 text-sm text-foreground-muted">
                                    <LoadingDots />
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Error banner */}
                    {error && (
                        <div
                            className="animate-fade-in-up rounded-xl border border-danger/30 bg-danger-muted px-4 py-3 text-sm text-danger"
                            role="alert"
                        >
                            {error}
                        </div>
                    )}

                    {/* Scroll anchor */}
                    <div ref={bottomRef} />

                    {/* Scroll-to-bottom hint */}
                    {userScrolledUp && hasMessages && (
                        <div className="flex justify-center animate-fade-in-up">
                            <button
                                type="button"
                                onClick={() => {
                                    bottomRef.current?.scrollIntoView({
                                        behavior: "smooth",
                                    });
                                    setUserScrolledUp(false);
                                }}
                                className="glass rounded-full px-3 py-1 text-xs text-foreground-muted transition-all duration-200 hover:text-foreground"
                                aria-label="Scroll to bottom"
                            >
                                ↓ New messages
                            </button>
                        </div>
                    )}
                </div>
            </div>
        </section>
    );
}
