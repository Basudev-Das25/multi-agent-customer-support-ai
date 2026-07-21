"use client";

import { FormEvent, useCallback, useEffect, useRef, useState } from "react";
import { LoaderIcon, PaperAirplaneIcon } from "@/components/shared/Icons";

interface ChatInputProps {
    onSend: (message: string) => Promise<void>;
    disabled?: boolean;
}

export default function ChatInput({ onSend, disabled }: ChatInputProps) {
    const [message, setMessage] = useState("");
    const [sending, setSending] = useState(false);
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    useEffect(() => {
        const el = textareaRef.current;
        if (el) {
            el.style.height = "auto";
            el.style.height = `${Math.min(el.scrollHeight, 144)}px`;
        }
    }, [message]);

    const handleSubmit = useCallback(
        async (event: FormEvent<HTMLFormElement>) => {
            event.preventDefault();
            const content = message.trim();
            if (!content || sending || disabled) return;

            try {
                setSending(true);
                await onSend(content);
                setMessage("");
                if (textareaRef.current) {
                    textareaRef.current.style.height = "auto";
                }
            } finally {
                setSending(false);
            }
        },
        [message, sending, disabled, onSend],
    );

    const handleKeyDown = useCallback(
        (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
            if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                event.currentTarget.form?.requestSubmit();
            }
        },
        [],
    );

    const canSend = !disabled && !sending && message.trim();

    return (
        <form
            onSubmit={handleSubmit}
            className="glass-heavy border-t border-white/[0.08] px-5 py-4 backdrop-blur md:px-8"
        >
            <div className="mx-auto flex max-w-4xl items-end gap-3 rounded-2xl border border-white/10 bg-surface p-2 shadow-xl shadow-black/10 transition-all duration-200 focus-within:border-accent focus-within:shadow-[0_0_0_3px_rgba(167,139,250,0.15)]">
                <textarea
                    ref={textareaRef}
                    value={message}
                    onChange={(event) => setMessage(event.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Message Support AI..."
                    rows={1}
                    disabled={disabled || sending}
                    aria-label="Chat message"
                    className="max-h-36 min-h-11 flex-1 resize-none bg-transparent px-3 py-2.5 text-sm leading-6 text-foreground outline-none placeholder:text-foreground-dim disabled:cursor-not-allowed"
                />

                <button
                    type="submit"
                    disabled={!canSend}
                    aria-label="Send message"
                    className="btn-press flex h-9 w-9 items-center justify-center rounded-xl bg-accent text-background transition-all duration-200 hover:bg-accent-hover hover:shadow-[0_0_20px_rgba(167,139,250,0.3)] disabled:cursor-not-allowed disabled:opacity-40 active:scale-90"
                >
                    {sending ? (
                        <LoaderIcon className="h-4 w-4" />
                    ) : (
                        <PaperAirplaneIcon className="h-4 w-4" />
                    )}
                </button>
            </div>

            <p className="mx-auto mt-2 max-w-4xl px-2 text-xs text-foreground-dim">
                Enter to send · Shift + Enter for a new line
            </p>
        </form>
    );
}
