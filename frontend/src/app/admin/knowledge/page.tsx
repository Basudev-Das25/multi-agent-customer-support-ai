"use client";

import {
    useCallback,
    useEffect,
    useRef,
    useState,
} from "react";
import { useRouter } from "next/navigation";

import { parseApiError } from "@/lib/api-helpers";
import {
    deleteDocument,
    ingestDatasets,
    listDatasets,
    listDocuments,
    searchDocuments,
    uploadDocument,
} from "@/services/knowledge";
import { getCurrentUser } from "@/services/auth";
import { useAuthStore } from "@/store/auth";
import type {
    DatasetResponse,
    KnowledgeDocumentResponse,
    RetrievalResult,
} from "@/types/knowledge";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatFileSize(bytes: number): string {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatDate(iso: string): string {
    return new Date(iso).toLocaleDateString(undefined, {
        year: "numeric",
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
    });
}

// ---------------------------------------------------------------------------
// Confirm Dialog
// ---------------------------------------------------------------------------

function ConfirmDialog({
    open,
    title,
    message,
    onConfirm,
    onCancel,
    loading,
}: {
    open: boolean;
    title: string;
    message: string;
    onConfirm: () => void;
    onCancel: () => void;
    loading: boolean;
}) {
    if (!open) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 px-4 animate-overlay-in">
            <div className="w-full max-w-sm rounded-2xl glass-heavy p-6 shadow-xl animate-dialog-enter">
                <h3 className="text-lg font-semibold text-foreground">{title}</h3>
                <p className="mt-2 text-sm text-foreground-muted">{message}</p>
                <div className="mt-6 flex justify-end gap-3">
                    <button
                        type="button"
                        onClick={onCancel}
                        disabled={loading}
                        className="btn-press rounded-xl border border-white/10 px-4 py-2 text-sm font-medium text-foreground-muted transition-all duration-200 hover:bg-surface-hover disabled:opacity-50 active:scale-[0.97]"
                    >
                        Cancel
                    </button>
                    <button
                        type="button"
                        onClick={onConfirm}
                        disabled={loading}
                        className="btn-press rounded-xl bg-danger px-4 py-2 text-sm font-bold text-white transition-all duration-200 hover:bg-danger/80 disabled:opacity-50 active:scale-[0.97]"
                    >
                        {loading ? "Deleting…" : "Delete"}
                    </button>
                </div>
            </div>
        </div>
    );
}

// ---------------------------------------------------------------------------
// Upload Zone
// ---------------------------------------------------------------------------

function UploadZone({
    onUploaded,
    disabled,
}: {
    onUploaded: () => void;
    disabled: boolean;
}) {
    const inputRef = useRef<HTMLInputElement>(null);
    const [dragOver, setDragOver] = useState(false);
    const [uploading, setUploading] = useState(false);
    const [progress, setProgress] = useState(0);
    const [error, setError] = useState("");

    async function handleFile(file: File | undefined) {
        if (!file) return;
        if (file.type !== "application/pdf") {
            setError("Only PDF files are accepted.");
            return;
        }

        setError("");
        setUploading(true);
        setProgress(0);

        try {
            await uploadDocument(
                file,
                (pct) => setProgress(pct),
            );
            setProgress(100);
            onUploaded();
        } catch (err) {
            setError(
                parseApiError(err, "Upload failed. Please try again."),
            );
        } finally {
            setUploading(false);
            // Reset file input so the same file can be re-selected
            if (inputRef.current) inputRef.current.value = "";
        }
    }

    return (
        <div>
            <label
                onDragOver={(e) => {
                    e.preventDefault();
                    setDragOver(true);
                }}
                onDragLeave={() => setDragOver(false)}
                onDrop={(e) => {
                    e.preventDefault();
                    setDragOver(false);
                    const file = e.dataTransfer.files?.[0];
                    handleFile(file);
                }}
                className={`flex cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed p-8 text-center transition-all duration-200 ${
                    dragOver
                        ? "border-accent bg-accent-muted scale-[1.01]"
                        : "border-white/10 hover:border-accent/40 hover:bg-surface/30"
                } ${disabled || uploading ? "pointer-events-none opacity-50" : ""}`}
            >
                <span className="text-3xl text-accent animate-float">↑</span>
                <p className="mt-3 text-sm font-medium text-foreground">
                    {uploading
                        ? `Uploading… ${progress}%`
                        : "Drop a PDF here, or click to browse"}
                </p>
                <p className="mt-1 text-xs text-foreground-dim">
                    Only PDF files are accepted
                </p>
            </label>

            <input
                ref={inputRef}
                type="file"
                accept="application/pdf"
                className="hidden"
                onChange={(e) => handleFile(e.target.files?.[0])}
            />

            {uploading && (
                <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-surface">
                    <div
                        className="h-full rounded-full bg-accent transition-all duration-500 ease-out"
                        style={{ width: `${progress}%` }}
                    />
                </div>
            )}

            {error && (
                <p className="mt-3 animate-fade-in-up rounded-xl border border-danger/30 bg-danger-muted px-4 py-3 text-sm text-danger">
                    {error}
                </p>
            )}
        </div>
    );
}

// ---------------------------------------------------------------------------
// Search Bar
// ---------------------------------------------------------------------------

function SearchBar({
    onResults,
    onClear,
}: {
    onResults: (results: RetrievalResult[]) => void;
    onClear: () => void;
}) {
    const [query, setQuery] = useState("");
    const [searching, setSearching] = useState(false);
    const timerRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

    useEffect(() => {
        return () => clearTimeout(timerRef.current);
    }, []);

    function handleChange(value: string) {
        setQuery(value);
        clearTimeout(timerRef.current);

        if (!value.trim()) {
            onClear();
            return;
        }

        timerRef.current = setTimeout(async () => {
            setSearching(true);
            try {
                const results = await searchDocuments(value.trim());
                onResults(results);
            } catch {
                // Silently fail — search is non-critical
            } finally {
                setSearching(false);
            }
        }, 400);
    }

    return (
        <div className="relative">
            <input
                type="text"
                value={query}
                onChange={(e) => handleChange(e.target.value)}
                placeholder="Search knowledge base…"
                className="w-full rounded-xl border border-white/10 bg-background-elevated px-4 py-3 pl-10 text-sm text-foreground outline-none transition-all duration-200 placeholder:text-foreground-dim focus:border-accent focus:shadow-[0_0_0_3px_rgba(167,139,250,0.15)]"
            />
            <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-foreground-dim">
                {searching ? "…" : "⌕"}
            </span>
        </div>
    );
}

// ---------------------------------------------------------------------------
// Datasets Tab
// ---------------------------------------------------------------------------

function DatasetsTab() {
    const [datasets, setDatasets] = useState<DatasetResponse[]>([]);
    const [loading, setLoading] = useState(true);
    const [ingesting, setIngesting] = useState<string | null>(null);
    const [ingestingAll, setIngestingAll] = useState(false);
    const [error, setError] = useState("");
    const [success, setSuccess] = useState("");

    const loadDatasets = useCallback(async () => {
        setLoading(true);
        setError("");
        try {
            setDatasets(await listDatasets());
        } catch (err) {
            setError(parseApiError(err, "Unable to load datasets."));
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        const t = setTimeout(() => { loadDatasets(); }, 0);
        return () => clearTimeout(t);
    }, [loadDatasets]);

    async function handleIngestSingle(name: string) {
        setIngesting(name);
        setError("");
        setSuccess("");
        try {
            const result = await ingestDatasets(name);
            setSuccess(result.message);
            await loadDatasets();
        } catch (err) {
            setError(parseApiError(err, "Ingestion failed."));
        } finally {
            setIngesting(null);
        }
    }

    async function handleIngestAll() {
        setIngestingAll(true);
        setError("");
        setSuccess("");
        try {
            const result = await ingestDatasets();
            setSuccess(result.message);
            await loadDatasets();
        } catch (err) {
            setError(parseApiError(err, "Ingestion failed."));
        } finally {
            setIngestingAll(false);
        }
    }

    const uningestedCount = datasets.filter((d) => !d.is_ingested).length;

    return (
        <div>
            {/* Actions bar */}
            <div className="flex flex-wrap items-center justify-between gap-3">
                <p className="text-sm text-foreground-dim">
                    {datasets.filter((d) => d.is_ingested).length} of{" "}
                    {datasets.length} datasets ingested
                </p>

                <button
                    type="button"
                    onClick={handleIngestAll}
                    disabled={ingestingAll || uningestedCount === 0}
                    className="btn-press rounded-xl bg-accent px-4 py-2 text-sm font-bold text-background transition-all duration-200 hover:bg-accent-hover hover:shadow-[0_0_20px_rgba(167,139,250,0.3)] disabled:opacity-50 active:scale-[0.97]"
                >
                    {ingestingAll
                        ? "Ingesting…"
                        : `Ingest All${uningestedCount > 0 ? ` (${uningestedCount})` : ""}`}
                </button>
            </div>

            {/* Messages */}
            {error && (
                <div className="mt-4 animate-fade-in-up rounded-xl border border-danger/30 bg-danger-muted px-4 py-3 text-sm text-danger">
                    {error}
                </div>
            )}
            {success && (
                <div className="mt-4 animate-fade-in-up rounded-xl border border-success/30 bg-success-muted px-4 py-3 text-sm text-success">
                    {success}
                </div>
            )}

            {/* Dataset cards */}
            {loading ? (
                <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                    {[1, 2, 3].map((n) => (
                        <div key={n} className="h-44 shimmer rounded-2xl" />
                    ))}
                </div>
            ) : (
                <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3 stagger-list">
                    {datasets.map((ds) => (
                        <div
                            key={ds.name}
                            className="flex flex-col rounded-2xl border border-white/10 bg-surface/40 p-5 backdrop-blur-sm transition-all duration-200 hover:border-accent/20 hover:bg-surface/60"
                        >
                            {/* Status badge */}
                            <div className="flex items-start justify-between gap-2">
                                <span
                                    className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium ${
                                        ds.is_ingested
                                            ? "bg-success-muted text-success"
                                            : "bg-accent-warm-muted text-accent-warm"
                                    }`}
                                >
                                    <span
                                        className={`h-1.5 w-1.5 rounded-full ${
                                            ds.is_ingested ? "bg-success" : "bg-accent-warm"
                                        }`}
                                    />
                                    {ds.is_ingested ? "Ingested" : "Not Ingested"}
                                </span>
                            </div>

                            {/* Info */}
                            <h3 className="mt-3 text-sm font-semibold text-foreground leading-snug">
                                {ds.display_name}
                            </h3>
                            <p className="mt-1.5 flex-1 text-xs leading-5 text-foreground-muted line-clamp-2">
                                {ds.description}
                            </p>

                            {/* Stats */}
                            {ds.is_ingested && (
                                <div className="mt-3 flex gap-4 text-xs text-foreground-dim">
                                    <span>{ds.document_count} docs</span>
                                    <span>{ds.chunk_count} chunks</span>
                                    {ds.ingested_at && (
                                        <span>{formatDate(ds.ingested_at)}</span>
                                    )}
                                </div>
                            )}

                            {/* Action */}
                            <button
                                type="button"
                                onClick={() => handleIngestSingle(ds.name)}
                                disabled={ingesting !== null || ingestingAll}
                                className="btn-press mt-4 w-full rounded-xl border border-white/10 px-3 py-2 text-xs font-semibold text-foreground-muted transition-all duration-200 hover:border-accent/40 hover:bg-accent-muted hover:text-accent disabled:opacity-50 active:scale-[0.97]"
                            >
                                {ingesting === ds.name
                                    ? "Ingesting…"
                                    : ds.is_ingested
                                      ? "Re-Ingest"
                                      : "Ingest"}
                            </button>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------

export default function AdminKnowledgePage() {
    const router = useRouter();
    const setUser = useAuthStore((state) => state.setUser);
    const token = useAuthStore((state) => state.token);
    const user = useAuthStore((state) => state.user);

    const [activeTab, setActiveTab] = useState<"documents" | "datasets">("documents");

    const [documents, setDocuments] = useState<
        KnowledgeDocumentResponse[]
    >([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    const [deleteTarget, setDeleteTarget] = useState<string | null>(
        null,
    );
    const [deleting, setDeleting] = useState(false);

    const [searchResults, setSearchResults] = useState<
        RetrievalResult[] | null
    >(null);

    // --------------------------------------------------
    // Auth gate + role check
    // --------------------------------------------------
    useEffect(() => {
        const stored = localStorage.getItem("access_token");
        if (!stored) {
            router.replace("/login");
            return;
        }

        if (!token) {
            useAuthStore.getState().setToken(stored);
        }

        if (!user) {
            getCurrentUser()
                .then((profile) => {
                    setUser(profile);
                    if (profile.role !== "admin") {
                        router.replace("/dashboard");
                    }
                })
                .catch(() => router.replace("/login"));
        } else if (user.role !== "admin") {
            router.replace("/dashboard");
        }
    }, []); // eslint-disable-line react-hooks/exhaustive-deps

    // --------------------------------------------------
    // Load documents
    // --------------------------------------------------
    const loadDocuments = useCallback(async () => {
        setLoading(true);
        setError("");
        try {
            const docs = await listDocuments();
            setDocuments(docs);
        } catch (err) {
            setError(
                parseApiError(
                    err,
                    "Unable to load documents.",
                ),
            );
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        if (user?.role === "admin") {
            const timer = setTimeout(() => { loadDocuments(); }, 0);
            return () => clearTimeout(timer);
        }
    }, [user, loadDocuments]);

    // --------------------------------------------------
    // Delete
    // --------------------------------------------------
    async function confirmDelete() {
        if (!deleteTarget) return;
        setDeleting(true);
        try {
            await deleteDocument(deleteTarget);
            setDeleteTarget(null);
            await loadDocuments();
        } catch (err) {
            setError(
                parseApiError(
                    err,
                    "Unable to delete document.",
                ),
            );
            setDeleteTarget(null);
        } finally {
            setDeleting(false);
        }
    }

    // --------------------------------------------------
    // Guard: only admins see this page
    // --------------------------------------------------
    if (!user || user.role !== "admin") {
        return (
            <main className="flex min-h-screen items-center justify-center text-foreground-muted">
                <p className="animate-pulse-soft">Checking access…</p>
            </main>
        );
    }

    // --------------------------------------------------
    // Render
    // --------------------------------------------------
    const isSearching = searchResults !== null;

    return (
        <main className="min-h-screen">
            <div className="mx-auto max-w-6xl px-4 py-8 md:px-8 animate-fade-in">
                {/* Header */}
                <div className="flex flex-wrap items-start justify-between gap-4">
                    <div>
                        <p className="text-xs font-bold uppercase tracking-[0.22em] text-accent">
                            Admin
                        </p>
                        <h1 className="mt-1 text-2xl font-bold text-foreground">
                            Knowledge Base
                        </h1>
                    </div>

                    <div className="flex gap-3">
                        <button
                            type="button"
                            onClick={() => router.push("/dashboard")}
                            className="btn-press rounded-xl border border-white/10 px-4 py-2 text-sm font-medium text-foreground-muted transition-all duration-200 hover:bg-surface-hover active:scale-[0.97]"
                        >
                            ← Chat
                        </button>

                        <button
                            type="button"
                            onClick={() =>
                                router.replace("/login")
                            }
                            className="btn-press rounded-xl border border-white/10 px-4 py-2 text-sm font-medium text-foreground-muted transition-all duration-200 hover:border-danger/60 hover:bg-danger-muted hover:text-danger active:scale-[0.97]"
                        >
                            Sign out
                        </button>
                    </div>
                </div>

                {/* Tabs */}
                <div className="mt-6 flex gap-1 rounded-xl border border-white/10 bg-surface/40 p-1 w-fit">
                    <button
                        type="button"
                        onClick={() => setActiveTab("documents")}
                        className={`rounded-lg px-4 py-2 text-sm font-medium transition-all duration-200 ${
                            activeTab === "documents"
                                ? "bg-accent text-background shadow-md shadow-accent/20"
                                : "text-foreground-muted hover:text-foreground hover:bg-surface-hover"
                        }`}
                    >
                        📄 Documents
                    </button>
                    <button
                        type="button"
                        onClick={() => setActiveTab("datasets")}
                        className={`rounded-lg px-4 py-2 text-sm font-medium transition-all duration-200 ${
                            activeTab === "datasets"
                                ? "bg-accent text-background shadow-md shadow-accent/20"
                                : "text-foreground-muted hover:text-foreground hover:bg-surface-hover"
                        }`}
                    >
                        📦 Datasets
                    </button>
                </div>

                {/* Tab content */}
                {activeTab === "documents" && (
                    <div>
                        {/* Upload zone */}
                        <section className="mt-6">
                            <UploadZone
                                onUploaded={loadDocuments}
                                disabled={loading}
                            />
                        </section>

                        {/* Search */}
                        <section className="mt-6">
                            <SearchBar
                                onResults={(results) =>
                                    setSearchResults(results)
                                }
                                onClear={() => setSearchResults(null)}
                            />
                        </section>

                        {/* Error banner */}
                        {error && (
                            <div className="mt-6 animate-fade-in-up rounded-xl border border-danger/30 bg-danger-muted px-4 py-3 text-sm text-danger">
                                {error}
                            </div>
                        )}

                        {/* Refresh + summary */}
                        <div className="mt-6 flex items-center justify-between">
                            <p className="text-sm text-foreground-dim">
                                {isSearching
                                    ? `${searchResults!.length} result(s)`
                                    : `${documents.length} document(s)`}
                            </p>

                            <button
                                type="button"
                                onClick={loadDocuments}
                                disabled={loading}
                                className="btn-press rounded-xl border border-white/10 px-3 py-1.5 text-xs font-medium text-foreground-dim transition-all duration-200 hover:bg-surface-hover disabled:opacity-50 active:scale-[0.97]"
                            >
                                ↻ Refresh
                            </button>
                        </div>

                        {/* Search results */}
                        {isSearching && searchResults!.length > 0 && (
                            <section className="mt-4 space-y-3 stagger-list">
                                {searchResults!.map((r) => (
                                    <article
                                        key={r.chunk_id}
                                        className="rounded-xl border border-white/10 bg-surface/60 p-4 backdrop-blur-sm"
                                    >
                                        <div className="flex items-center gap-3 text-xs text-foreground-dim">
                                            <span>
                                                Document: {r.document_id.slice(0, 8)}…
                                            </span>
                                            <span>Page {r.page_number}</span>
                                            <span>
                                                Score: {r.score.toFixed(3)}
                                            </span>
                                        </div>
                                        <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-foreground">
                                            {r.text}
                                        </p>
                                    </article>
                                ))}
                            </section>
                        )}

                        {isSearching && searchResults!.length === 0 && (
                            <p className="mt-8 text-center text-sm text-foreground-dim">
                                No results found for your query.
                            </p>
                        )}

                        {/* Document table */}
                        {!isSearching && (
                            <section className="mt-4">
                                {loading ? (
                                    <div className="space-y-3">
                                        {[1, 2, 3].map((n) => (
                                            <div
                                                key={n}
                                                className="h-20 shimmer rounded-xl"
                                            />
                                        ))}
                                    </div>
                                ) : documents.length === 0 ? (
                                    <div className="py-16 text-center animate-fade-in-up">
                                        <span className="text-4xl text-accent animate-float inline-block">
                                            📄
                                        </span>
                                        <h2 className="mt-4 text-lg font-semibold text-foreground">
                                            No documents yet
                                        </h2>
                                        <p className="mt-1 text-sm text-foreground-dim">
                                            Upload a PDF or ingest a dataset to get started.
                                        </p>
                                    </div>
                                ) : (
                                    <div className="overflow-x-auto">
                                        {/* Desktop table */}
                                        <table className="hidden w-full text-left text-sm md:table">
                                            <thead>
                                                <tr className="border-b border-white/[0.08] text-xs uppercase tracking-wider text-foreground-dim">
                                                    <th className="py-3 pr-4 font-medium">
                                                        File
                                                    </th>
                                                    <th className="py-3 pr-4 font-medium">
                                                        Source
                                                    </th>
                                                    <th className="py-3 pr-4 font-medium">
                                                        Uploaded
                                                    </th>
                                                    <th className="py-3 pr-4 font-medium">
                                                        Status
                                                    </th>
                                                    <th className="py-3 pr-4 font-medium">
                                                        Pages
                                                    </th>
                                                    <th className="py-3 pr-4 font-medium">
                                                        Chunks
                                                    </th>
                                                    <th className="py-3 pr-4 font-medium">
                                                        Size
                                                    </th>
                                                    <th className="py-3 font-medium">
                                                        Actions
                                                    </th>
                                                </tr>
                                            </thead>
                                            <tbody className="stagger-list">
                                                {documents.map((doc) => (
                                                    <tr
                                                        key={doc.id}
                                                        className="border-b border-white/[0.06] transition-all duration-200 hover:bg-surface-hover/40"
                                                    >
                                                        <td className="py-3 pr-4">
                                                            <p className="truncate font-medium text-foreground max-w-56"
                                                                title={doc.original_filename}
                                                            >
                                                                {doc.original_filename}
                                                            </p>
                                                        </td>
                                                        <td className="py-3 pr-4">
                                                            <span
                                                                className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${
                                                                    doc.source === "upload"
                                                                        ? "bg-accent-cool-muted text-accent-cool"
                                                                        : "bg-accent-muted text-accent"
                                                                }`}
                                                            >
                                                                {doc.source === "upload" ? "PDF Upload" : doc.source}
                                                            </span>
                                                        </td>
                                                        <td className="py-3 pr-4 text-foreground-muted">
                                                            {formatDate(
                                                                doc.uploaded_at,
                                                            )}
                                                        </td>
                                                        <td className="py-3 pr-4">
                                                            <span
                                                                className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-medium ${
                                                                    doc.status ===
                                                                    "processed"
                                                                        ? "bg-success-muted text-success"
                                                                        : "bg-accent-warm-muted text-accent-warm"
                                                                }`}
                                                            >
                                                                {doc.status}
                                                            </span>
                                                        </td>
                                                        <td className="py-3 pr-4 text-foreground-muted">
                                                            {doc.page_count}
                                                        </td>
                                                        <td className="py-3 pr-4 text-foreground-muted">
                                                            {doc.chunk_count}
                                                        </td>
                                                        <td className="py-3 pr-4 text-foreground-muted">
                                                            {formatFileSize(
                                                                doc.file_size,
                                                            )}
                                                        </td>
                                                        <td className="py-3">
                                                            <button
                                                                type="button"
                                                                onClick={() =>
                                                                    setDeleteTarget(
                                                                        doc.id,
                                                                    )
                                                                }
                                                                className="btn-press rounded-lg px-3 py-1.5 text-xs font-medium text-danger transition-all duration-200 hover:bg-danger-muted active:scale-[0.97]"
                                                            >
                                                                Delete
                                                            </button>
                                                        </td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>

                                        {/* Mobile cards */}
                                        <div className="space-y-3 stagger-list md:hidden">
                                            {documents.map((doc) => (
                                                <div
                                                    key={doc.id}
                                                    className="rounded-xl border border-white/10 bg-surface/40 p-4 backdrop-blur-sm"
                                                >
                                                    <div className="flex items-start justify-between gap-3">
                                                        <p className="truncate font-medium text-foreground">
                                                            {doc.original_filename}
                                                        </p>
                                                        <span
                                                            className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-medium ${
                                                                doc.status ===
                                                                "processed"
                                                                    ? "bg-success-muted text-success"
                                                                    : "bg-accent-warm-muted text-accent-warm"
                                                            }`}
                                                        >
                                                            {doc.status}
                                                        </span>
                                                    </div>
                                                    <div className="mt-1">
                                                        <span
                                                            className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${
                                                                doc.source === "upload"
                                                                    ? "bg-accent-cool-muted text-accent-cool"
                                                                    : "bg-accent-muted text-accent"
                                                            }`}
                                                        >
                                                            {doc.source === "upload" ? "PDF Upload" : doc.source}
                                                        </span>
                                                    </div>
                                                    <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-foreground-dim">
                                                        <span>
                                                            {formatDate(
                                                                doc.uploaded_at,
                                                            )}
                                                        </span>
                                                        <span>
                                                            {doc.page_count} page
                                                            {doc.page_count !== 1
                                                                ? "s"
                                                                : ""}
                                                        </span>
                                                        <span>
                                                            {doc.chunk_count} chunk
                                                            {doc.chunk_count !== 1
                                                                ? "s"
                                                                : ""}
                                                        </span>
                                                        <span>
                                                            {formatFileSize(
                                                                doc.file_size,
                                                            )}
                                                        </span>
                                                    </div>
                                                    <div className="mt-3">
                                                        <button
                                                            type="button"
                                                            onClick={() =>
                                                                setDeleteTarget(
                                                                    doc.id,
                                                                )
                                                            }
                                                            className="btn-press rounded-lg px-3 py-1.5 text-xs font-medium text-danger transition-all duration-200 hover:bg-danger-muted active:scale-[0.97]"
                                                        >
                                                            Delete
                                                        </button>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </section>
                        )}
                    </div>
                )}

                {activeTab === "datasets" && (
                    <DatasetsTab />
                )}
            </div>

            {/* Delete confirmation dialog */}
            <ConfirmDialog
                open={deleteTarget !== null}
                title="Delete document"
                message="Are you sure? This permanently removes the document, its chunks, and its search vectors."
                onConfirm={confirmDelete}
                onCancel={() => setDeleteTarget(null)}
                loading={deleting}
            />
        </main>
    );
}
