import { useMemo } from "react";
import { Marked } from "marked";
import { markedHighlight } from "marked-highlight";
import hljs from "highlight.js";

const marked = new Marked(
    markedHighlight({
        highlight(code: string, lang: string) {
            if (lang && hljs.getLanguage(lang)) {
                try {
                    return hljs.highlight(code, { language: lang })
                        .value;
                } catch {
                    // fall through
                }
            }
            return hljs.highlightAuto(code).value;
        },
    }),
    {
        gfm: true,
        breaks: true,
    },
);

/**
 * Render a markdown string as safe HTML with syntax-highlighted code blocks.
 */
export function renderMarkdown(content: string): string {
    return marked.parse(content, { async: false }) as string;
}

// ---------------------------------------------------------------------------
// React component wrapper
// ---------------------------------------------------------------------------

interface MarkdownProps {
    content: string;
    className?: string;
}

/**
 * Renders Markdown text as styled HTML with syntax highlighting.
 */
export default function Markdown({
    content,
    className = "",
}: MarkdownProps) {
    const html = useMemo(() => renderMarkdown(content), [content]);

    return (
        <div
            className={`prose prose-invert max-w-none text-sm leading-7 ${className}`}
            dangerouslySetInnerHTML={{ __html: html }}
        />
    );
}
