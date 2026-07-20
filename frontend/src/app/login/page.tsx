"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";

import { parseApiError } from "@/lib/api-helpers";
import { loginSchema } from "@/lib/validations";
import { useAuth } from "@/hooks/useAuth";

export default function LoginPage() {
    const { signIn } = useAuth();

    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    async function handleSubmit(event: FormEvent<HTMLFormElement>) {
        event.preventDefault();
        setError("");
        setLoading(true);

        try {
            // Client-side validation using zod
            const parsed = loginSchema.safeParse({ email, password });
            if (!parsed.success) {
                const first = parsed.error.issues[0];
                setError(first?.message ?? "Invalid input.");
                setLoading(false);
                return;
            }

            await signIn(parsed.data.email, parsed.data.password);
        } catch (err) {
            setError(parseApiError(err, "Unable to login."));
        } finally {
            setLoading(false);
        }
    }

    return (
        <main className="flex min-h-screen items-center justify-center px-6">
            <div className="w-full max-w-md rounded-2xl glass-heavy p-8 shadow-[0_0_40px_rgba(167,139,250,0.08)] animate-scale-in">

                <div className="mb-8">
                    <p className="text-sm font-semibold uppercase tracking-[0.2em] text-accent">
                        Customer Support AI
                    </p>

                    <h1 className="mt-2 text-3xl font-bold text-foreground">
                        Welcome Back
                    </h1>

                    <p className="mt-2 text-sm text-foreground-muted">
                        Sign in to continue.
                    </p>
                </div>

                <form
                    onSubmit={handleSubmit}
                    className="space-y-5"
                >

                    <div className="animate-fade-in-up" style={{ animationDelay: "50ms" }}>
                        <label
                            htmlFor="email"
                            className="mb-2 block text-sm text-foreground-muted"
                        >
                            Email
                        </label>

                        <input
                            id="email"
                            type="email"
                            autoComplete="email"
                            required
                            value={email}
                            onChange={(e) =>
                                setEmail(e.target.value)
                            }
                            className="w-full rounded-lg border border-white/10 bg-background-elevated px-4 py-3 text-foreground outline-none transition-all duration-200 focus:border-accent focus:shadow-[0_0_0_3px_rgba(167,139,250,0.15)] placeholder:text-foreground-dim"
                            placeholder="john@example.com"
                        />
                    </div>

                    <div className="animate-fade-in-up" style={{ animationDelay: "100ms" }}>
                        <label
                            htmlFor="password"
                            className="mb-2 block text-sm text-foreground-muted"
                        >
                            Password
                        </label>

                        <input
                            id="password"
                            type="password"
                            autoComplete="current-password"
                            required
                            value={password}
                            onChange={(e) =>
                                setPassword(e.target.value)
                            }
                            className="w-full rounded-lg border border-white/10 bg-background-elevated px-4 py-3 text-foreground outline-none transition-all duration-200 focus:border-accent focus:shadow-[0_0_0_3px_rgba(167,139,250,0.15)] placeholder:text-foreground-dim"
                            placeholder="••••••••"
                        />
                    </div>

                    {error && (
                        <div className="animate-fade-in-up rounded-lg bg-danger-muted px-4 py-3 text-sm text-danger">
                            {error}
                        </div>
                    )}

                    <button
                        type="submit"
                        disabled={loading}
                        className="btn-press w-full rounded-lg bg-accent py-3 font-semibold text-background transition-all duration-200 hover:bg-accent-hover hover:shadow-[0_0_20px_rgba(167,139,250,0.3)] disabled:opacity-50 active:scale-[0.97]"
                    >
                        {loading
                            ? "Signing In..."
                            : "Sign In"}
                    </button>

                </form>

                <div className="mt-6 text-center text-sm text-foreground-muted">
                    Don&apos;t have an account?{" "}
                    <Link
                        href="/register"
                        className="font-medium text-accent transition-colors duration-200 hover:text-accent-hover"
                    >
                        Register
                    </Link>
                </div>

            </div>
        </main>
    );
}
