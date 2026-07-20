import { useRouter } from "next/navigation";

import { parseApiError } from "@/lib/api-helpers";
import { getCurrentUser, login } from "@/services/auth";
import { useAuthStore } from "@/store/auth";

const AUTH_TOKEN_KEY = "access_token";

export function useAuth() {
    const router = useRouter();

    const setToken = useAuthStore((state) => state.setToken);
    const setUser = useAuthStore((state) => state.setUser);

    async function signIn(email: string, password: string) {
        const response = await login({ email, password });

        localStorage.setItem(
            AUTH_TOKEN_KEY,
            response.access_token,
        );

        setToken(response.access_token);

        // Fetch the full user profile so role etc. are available immediately.
        try {
            const user = await getCurrentUser();
            setUser(user);
        } catch {
            // Non-critical — user can still access the dashboard.
        }

        router.push("/dashboard");
    }

    function signOut() {
        localStorage.removeItem(AUTH_TOKEN_KEY);
        setToken(null);
        setUser(null);
        router.push("/login");
    }

    return { signIn, signOut };
}

export { parseApiError };
