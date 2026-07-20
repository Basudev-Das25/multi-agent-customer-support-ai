import { create } from "zustand";
import type { User } from "@/types/auth";

interface AuthStore {
    token: string | null;
    user: User | null;

    setToken: (token: string | null) => void;
    setUser: (user: User | null) => void;
    logout: () => void;
}

export const useAuthStore = create<AuthStore>((set) => ({
    token: null,
    user: null,

    setToken: (token) => set({ token }),
    setUser: (user) => set({ user }),

    logout: () => set({ token: null, user: null }),
}));

/** Convenience selector — true when the authenticated user holds the admin role. */
export const isAdmin = (): boolean => {
    const { user } = useAuthStore.getState();
    return user?.role === "admin";
};
