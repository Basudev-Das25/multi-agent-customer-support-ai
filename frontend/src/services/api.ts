import axios from "axios";

const AUTH_TOKEN_KEY = "access_token";

const api = axios.create({
    baseURL:
        process.env.NEXT_PUBLIC_API_URL ??
        "http://localhost:8000/api/v1",
    headers: {
        "Content-Type": "application/json",
    },
});

api.interceptors.request.use((config) => {
    const token =
        typeof window !== "undefined"
            ? localStorage.getItem(AUTH_TOKEN_KEY)
            : null;

    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
});

/** Track whether a 401 redirect is already in progress to avoid loops. */
let isRedirectingToLogin = false;

api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (
            !isRedirectingToLogin &&
            axios.isAxiosError(error) &&
            error.response?.status === 401
        ) {
            isRedirectingToLogin = true;
            localStorage.removeItem(AUTH_TOKEN_KEY);
            window.location.href = "/login";
        }
        return Promise.reject(error);
    },
);

export default api;
