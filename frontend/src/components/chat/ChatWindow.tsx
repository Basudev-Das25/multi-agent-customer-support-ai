"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Markdown from "@/components/shared/Markdown";
import {
    BotIcon,
    ChevronDownIcon,
    CopyIcon,
    CheckIcon,
    LightbulbIcon,
    SparklesIcon,
    UserIcon,
} from "@/components/shared/Icons";
import type {
    ChatMessage,
    ChatMessageMetadata,
    Conversation,
} from "@/types/chat";

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
            /* clipboard not available */
        }
    }, [text]);

    return (
        <button
            type="button"
            onClick={handleClick}
            aria-label="Copy message"
            className="rounded-md p-1.5 text-foreground-dim opacity-0 transition-all duration-200 group-hover/message:opacity-100 hover:bg-surface-hover hover:text-foreground focus:opacity-100 focus:outline-none focus:ring-2 focus:ring-accent/60"
        >
            {copied ? <CheckIcon /> : <CopyIcon />}
        </button>
    );
}

// ---------------------------------------------------------------------------
// Avatar
// ---------------------------------------------------------------------------

function Avatar({ role }: { role: "user" | "assistant" }) {
    return (
        <div
            className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${
                role === "user"
                    ? "bg-accent-muted text-accent"
                    : "bg-surface text-foreground-muted"
            }`}
            aria-hidden="true"
        >
            {role === "user" ? (
                <UserIcon className="h-4 w-4" />
            ) : (
                <BotIcon className="h-4 w-4" />
            )}
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
        <time dateTime={iso} className="text-[11px] text-foreground-dim">
            {label}
        </time>
    );
}

// ---------------------------------------------------------------------------
// Loading dots
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
                <ChevronDownIcon
                    className={`ml-auto transition-transform duration-200 ${
                        expanded ? "rotate-180" : ""
                    }`}
                />
            </button>

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
// Source card
// ---------------------------------------------------------------------------

function SourceCard({
    source,
}: {
    source: { document_name: string; text_preview: string; score: number };
}) {
    const [showFull, setShowFull] = useState(false);
    const displayName = source.document_name.split(" / ").pop() ?? source.document_name;
    const dataset = source.document_name.split(" / ")[0] ?? "";

    return (
        <div className="rounded-lg border border-white/[0.06] bg-background-elevated/50 px-3 py-2">
            <div className="flex items-center justify-between gap-2">
                <div className="min-w-0 flex-1">
                    <p className="truncate text-[11px] font-medium text-foreground">
                        {displayName}
                    </p>
                    {dataset && (
                        <p className="text-[10px] text-foreground-dim">{dataset}</p>
                    )}
                </div>
                <span className="shrink-0 rounded-full bg-accent-muted px-1.5 py-0.5 text-[9px] font-semibold text-accent">
                    {source.score.toFixed(2)}
                </span>
            </div>
            <p
                className={`mt-1 text-[11px] leading-4 text-foreground-muted ${
                    showFull ? "" : "line-clamp-2"
                }`}
            >
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
// Suggested prompt chips
// ---------------------------------------------------------------------------

const SUGGESTED_PROMPTS = [
    { icon: "💳", label: "How do I get a refund?" },
    { icon: "🔧", label: "I'm having login issues" },
    { icon: "📦", label: "Tell me about your products" },
    { icon: "📋", label: "What's your refund policy?" },
];

function SuggestedPrompts({
    onSelect,
}: {
    onSelect: (prompt: string) => void;
}) {
    return (
        <div className="mt-6 flex flex-wrap justify-center gap-2 animate-fade-in-up" style={{ animationDelay: "200ms" }}>
            {SUGGESTED_PROMPTS.map((prompt) => (
                <button
                    key={prompt.label}
                    type="button"
                    onClick={() => onSelect(prompt.label)}
                    className="glass flex items-center gap-2 rounded-full px-4 py-2.5 text-sm text-foreground-muted transition-all duration-200 hover:border-accent/30 hover:bg-accent-muted hover:text-foreground hover:scale-[1.02] active:scale-[0.98]"
                >
                    <span>{prompt.icon}</span>
                    <span>{prompt.label}</span>
                </button>
            ))}
        </div>
    );
}

// ---------------------------------------------------------------------------
// Empty state
// ---------------------------------------------------------------------------

function EmptyState({ onSelectPrompt }: { onSelectPrompt?: (p: string) => void }) {
    return (
        <div className="my-auto pt-20 text-center animate-fade-in-up">
            <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-accent-muted text-accent animate-float shadow-[0_0_30px_rgba(167,139,250,0.2)]">
                <SparklesIcon className="h-8 w-8" />
            </div>
            <h2 className="mt-5 text-2xl font-semibold text-foreground">
                How can we help?
            </h2>
            <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-foreground-muted">
                Ask about billing, product features, technical issues,
                complaints, or company policies.
            </p>
            {onSelectPrompt && <SuggestedPrompts onSelect={onSelectPrompt} />}
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
            className={`group/message animate-message-in flex gap-3 ${
                isUser ? "justify-end" : "justify-start"
            }`}
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
                <div className="mb-1 flex items-center justify-between gap-3">
                    <p className="text-[11px] font-bold uppercase tracking-wider opacity-60">
                        {isUser ? "You" : "Support AI"}
                    </p>
                    <div className="flex items-center gap-1.5">
                        <Timestamp iso={message.created_at} />
                        <CopyButton text={message.content} />
                    </div>
                </div>

                {isUser ? (
                    <p className="whitespace-pre-wrap text-sm leading-6">
                        {message.content}
                    </p>
                ) : (
                    <Markdown content={message.content} />
                )}

                {!isUser && message.metadata && (
                    <SourcesPanel metadata={message.metadata} />
                )}
            </div>

            {isUser && <Avatar role="user" />}
        </article>
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

    const handleScroll = useCallback(() => {
        const el = containerRef.current;
        if (!el) return;
        const atBottom =
            el.scrollHeight - el.scrollTop - el.clientHeight < 60;
        setUserScrolledUp(!atBottom);
    }, []);

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
                <div className="flex items-center gap-2">
                    <SparklesIcon className="h-4 w-4 text-accent" />
                    <p className="text-xs font-semibold uppercase tracking-[0.18em] text-accent">
                        Customer support assistant
                    </p>
                </div>
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
                    {!hasMessages && !isLoading && (
                        <EmptyState
                            onSelectPrompt={(p) => {
                                const textarea = document.querySelector(
                                    "textarea[aria-label='Chat message']",
                                ) as HTMLTextAreaElement | null;
                                if (textarea) {
                                    const nativeSetter =
                                        Object.getOwnPropertyDescriptor(
                                            window.HTMLTextAreaElement.prototype,
                                            "value",
                                        )?.set;
                                    nativeSetter?.call(textarea, p);
                                    textarea.dispatchEvent(
                                        new Event("input", { bubbles: true }),
                                    );
                                }
                            }}
                        />
                    )}

                    {hasMessages &&
                        messages.map((message) => (
                            <MessageBubble
                                key={message.id}
                                message={message}
                            />
                        ))}

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

                    {error && (
                        <div
                            className="animate-fade-in-up rounded-xl border border-danger/30 bg-danger-muted px-4 py-3 text-sm text-danger"
                            role="alert"
                        >
                            {error}
                        </div>
                    )}

                    <div ref={bottomRef} />

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
