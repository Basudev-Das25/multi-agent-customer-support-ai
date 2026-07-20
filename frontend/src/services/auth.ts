import api from "./api";
import type {
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    User,
} from "@/types/auth";

export async function login(data: LoginRequest) {
    const response = await api.post<LoginResponse>(
        "/auth/login",
        data,
    );
    return response.data;
}

export async function register(data: RegisterRequest) {
    const response = await api.post<User>(
        "/auth/register",
        data,
    );
    return response.data;
}

export async function getCurrentUser(): Promise<User> {
    const response = await api.get<User>("/auth/me");
    return response.data;
}
