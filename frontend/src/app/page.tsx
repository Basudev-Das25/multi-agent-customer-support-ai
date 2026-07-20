"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function Home() {
    const router = useRouter();

    useEffect(() => {
        const token = localStorage.getItem("access_token");

        if (token) {
            router.replace("/dashboard");
        } else {
            router.replace("/login");
        }
    }, [router]);

    return (
        <main className="flex min-h-screen items-center justify-center px-6">
            <div className="text-center animate-fade-in-up">
                <h1 className="text-3xl font-bold bg-gradient-to-r from-accent to-accent-cool bg-clip-text text-transparent">
                    Multi-Agent Customer Support AI
                </h1>

                <p className="mt-3 text-foreground-muted animate-pulse-soft">
                    Redirecting...
                </p>
            </div>
        </main>
    );
}
