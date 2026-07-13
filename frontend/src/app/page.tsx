"use client";

import { FormEvent, useEffect, useState } from "react";

import { getConversation, listConversations, sendMessage } from "@/services/chat";
import type { Conversation, ConversationSummary } from "@/types/chat";

export default function Home() {
  const [token, setToken] = useState(() =>
    typeof window === "undefined"
      ? ""
      : window.localStorage.getItem("access_token") ?? "",
  );
  const [draftToken, setDraftToken] = useState("");
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [conversation, setConversation] = useState<Conversation | null>(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (!token) return;
    listConversations()
      .then(setConversations)
      .catch((requestError: Error) => setError(requestError.message));
  }, [token]);

  async function connect(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const newToken = draftToken.trim();
    window.localStorage.setItem("access_token", newToken);
    setError("");
    setToken(newToken);
  }

  async function submitMessage(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!message.trim()) return;
    setIsLoading(true);
    setError("");
    try {
      const updated = await sendMessage(message.trim(), conversation?.id);
      setConversation(updated);
      setConversations(await listConversations());
      setMessage("");
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Unable to send message.");
    } finally {
      setIsLoading(false);
    }
  }

  if (!token) {
    return <main className="flex min-h-screen items-center justify-center bg-slate-950 p-6 text-slate-100"><form className="w-full max-w-lg space-y-5 rounded-2xl bg-slate-900 p-8" onSubmit={connect}><p className="text-sm font-semibold uppercase tracking-[0.2em] text-cyan-400">Support AI</p><h1 className="text-3xl font-bold">Connect your session</h1><p className="text-slate-300">Paste the bearer token returned by the login API.</p><textarea className="min-h-28 w-full rounded-lg border border-slate-700 bg-slate-950 p-3 font-mono text-xs" value={draftToken} onChange={(event) => setDraftToken(event.target.value)} required /><button className="w-full rounded-lg bg-cyan-400 px-4 py-3 font-semibold text-slate-950" type="submit">Open chat</button></form></main>;
  }

  return <main className="grid min-h-screen bg-slate-950 text-slate-100 md:grid-cols-[280px_1fr]"><aside className="border-b border-slate-800 p-5 md:border-b-0 md:border-r"><div className="mb-7 flex items-center justify-between"><div><p className="text-xs font-semibold uppercase tracking-[0.2em] text-cyan-400">Support AI</p><h1 className="text-xl font-bold">Conversations</h1></div><button className="rounded-md bg-cyan-400 px-3 py-2 text-sm font-semibold text-slate-950" onClick={() => setConversation(null)}>New</button></div><div className="space-y-2">{conversations.map((item) => <button className="w-full rounded-lg bg-slate-900 p-3 text-left text-sm hover:bg-slate-800" key={item.id} onClick={() => getConversation(item.id).then(setConversation)}><p className="truncate font-medium">{item.title}</p><p className="mt-1 text-xs text-slate-400">{new Date(item.updated_at).toLocaleString()}</p></button>)}</div></aside><section className="flex min-h-[70vh] flex-col"><div className="border-b border-slate-800 px-6 py-5"><h2 className="font-semibold">{conversation?.title ?? "New conversation"}</h2></div><div className="flex-1 space-y-4 p-6">{conversation?.messages.map((item) => <div className={`max-w-2xl rounded-2xl px-4 py-3 ${item.role === "user" ? "ml-auto bg-cyan-400 text-slate-950" : "bg-slate-800"}`} key={item.id}>{item.content}</div>)}{!conversation && <p className="mt-24 text-center text-slate-400">Start a conversation with the support team.</p>}{error && <p className="rounded-lg bg-red-950 p-3 text-sm text-red-200">{error}</p>}</div><form className="flex gap-3 border-t border-slate-800 p-5" onSubmit={submitMessage}><textarea className="min-h-12 flex-1 resize-none rounded-xl border border-slate-700 bg-slate-900 p-3" placeholder="Describe your issue..." value={message} onChange={(event) => setMessage(event.target.value)} /><button className="rounded-xl bg-cyan-400 px-5 font-semibold text-slate-950 disabled:opacity-50" disabled={isLoading || !message.trim()} type="submit">{isLoading ? "Sending..." : "Send"}</button></form></section></main>;
}
