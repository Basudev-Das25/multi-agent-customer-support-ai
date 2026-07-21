"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

import { parseApiError } from "@/lib/api-helpers";
import { registerSchema } from "@/lib/validations";
import { register as registerUser } from "@/services/auth";
import {
    EyeIcon,
    EyeOffIcon,
    KeyIcon,
    LoaderIcon,
    MailIcon,
    SparklesIcon,
    UserIcon,
} from "@/components/shared/Icons";

export default function RegisterPage() {
    const router = useRouter();

    const [name, setName] = useState("");
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [showPassword, setShowPassword] = useState(false);

    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [success, setSuccess] = useState("");

    async function handleSubmit(event: FormEvent<HTMLFormElement>) {
        event.preventDefault();

        setLoading(true);
        setError("");
        setSuccess("");

        try {
            const parsed = registerSchema.safeParse({
                name,
                email,
                password,
            });
            if (!parsed.success) {
                const first = parsed.error.issues[0];
                setError(first?.message ?? "Invalid input.");
                setLoading(false);
                return;
            }

            await registerUser(parsed.data);

            setSuccess("Registration successful! Redirecting to login...");

            setTimeout(() => {
                router.push("/login");
            }, 1500);
        } catch (err) {
            setError(parseApiError(err, "Registration failed."));
        } finally {
            setLoading(false);
        }
    }

    return (
        <main className="relative flex min-h-screen items-center justify-center px-6 overflow-hidden">
            {/* Background orbs */}
            <div className="auth-orb auth-orb-1" />
            <div className="auth-orb auth-orb-2" />
            <div className="auth-orb auth-orb-3" />

            <div className="relative z-10 w-full max-w-md rounded-2xl glass-heavy p-8 shadow-[0_0_40px_rgba(167,139,250,0.08)] animate-scale-in">
                {/* Logo */}
                <div className="mb-8 flex flex-col items-center text-center">
                    <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-accent-muted text-accent shadow-[0_0_30px_rgba(167,139,250,0.2)] animate-float">
                        <SparklesIcon className="h-7 w-7" />
                    </div>
                    <p className="mt-4 text-sm font-semibold uppercase tracking-[0.2em] text-accent">
                        Customer Support AI
                    </p>
                    <h1 className="mt-2 text-3xl font-bold text-foreground">
                        Create Account
                    </h1>
                    <p className="mt-2 text-sm text-foreground-muted">
                        Register to access the AI support platform.
                    </p>
                </div>

                <form onSubmit={handleSubmit} className="space-y-5">
                    <div className="animate-fade-in-up" style={{ animationDelay: "50ms" }}>
                        <label htmlFor="name" className="mb-2 block text-sm text-foreground-muted">
                            Full Name
                        </label>
                        <div className="relative">
                            <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-foreground-dim">
                                <UserIcon className="h-4 w-4" />
                            </span>
                            <input
                                id="name"
                                type="text"
                                autoComplete="name"
                                required
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                                className="w-full rounded-lg border border-white/10 bg-background-elevated pl-10 pr-4 py-3 text-foreground outline-none transition-all duration-200 focus:border-accent focus:shadow-[0_0_0_3px_rgba(167,139,250,0.15)] placeholder:text-foreground-dim"
                                placeholder="John Doe"
                            />
                        </div>
                    </div>

                    <div className="animate-fade-in-up" style={{ animationDelay: "100ms" }}>
                        <label htmlFor="email" className="mb-2 block text-sm text-foreground-muted">
                            Email
                        </label>
                        <div className="relative">
                            <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-foreground-dim">
                                <MailIcon className="h-4 w-4" />
                            </span>
                            <input
                                id="email"
                                type="email"
                                autoComplete="email"
                                required
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                className="w-full rounded-lg border border-white/10 bg-background-elevated pl-10 pr-4 py-3 text-foreground outline-none transition-all duration-200 focus:border-accent focus:shadow-[0_0_0_3px_rgba(167,139,250,0.15)] placeholder:text-foreground-dim"
                                placeholder="john@example.com"
                            />
                        </div>
                    </div>

                    <div className="animate-fade-in-up" style={{ animationDelay: "150ms" }}>
                        <label htmlFor="password" className="mb-2 block text-sm text-foreground-muted">
                            Password
                        </label>
                        <div className="relative">
                            <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-foreground-dim">
                                <KeyIcon className="h-4 w-4" />
                            </span>
                            <input
                                id="password"
                                type={showPassword ? "text" : "password"}
                                autoComplete="new-password"
                                required
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                className="w-full rounded-lg border border-white/10 bg-background-elevated pl-10 pr-10 py-3 text-foreground outline-none transition-all duration-200 focus:border-accent focus:shadow-[0_0_0_3px_rgba(167,139,250,0.15)] placeholder:text-foreground-dim"
                                placeholder="••••••••"
                            />
                            <button
                                type="button"
                                onClick={() => setShowPassword(!showPassword)}
                                className="absolute right-3 top-1/2 -translate-y-1/2 text-foreground-dim transition-colors hover:text-foreground"
                                aria-label={showPassword ? "Hide password" : "Show password"}
                            >
                                {showPassword ? <EyeOffIcon className="h-4 w-4" /> : <EyeIcon className="h-4 w-4" />}
                            </button>
                        </div>
                    </div>

                    {error && (
                        <div className="animate-fade-in-up rounded-lg bg-danger-muted px-4 py-3 text-sm text-danger">
                            {error}
                        </div>
                    )}

                    {success && (
                        <div className="animate-fade-in-up rounded-lg bg-success-muted px-4 py-3 text-sm text-success">
                            {success}
                        </div>
                    )}

                    <button
                        type="submit"
                        disabled={loading}
                        className="btn-press flex w-full items-center justify-center gap-2 rounded-lg bg-accent py-3 font-semibold text-background transition-all duration-200 hover:bg-accent-hover hover:shadow-[0_0_20px_rgba(167,139,250,0.3)] disabled:opacity-50 active:scale-[0.97]"
                    >
                        {loading ? (
                            <>
                                <LoaderIcon className="h-4 w-4" />
                                Creating Account...
                            </>
                        ) : (
                            "Register"
                        )}
                    </button>
                </form>

                <div className="mt-6 text-center text-sm text-foreground-muted">
                    Already have an account?{" "}
                    <Link
                        href="/login"
                        className="font-medium text-accent transition-colors duration-200 hover:text-accent-hover"
                    >
                        Sign In
                    </Link>
                </div>
            </div>
        </main>
    );
}
