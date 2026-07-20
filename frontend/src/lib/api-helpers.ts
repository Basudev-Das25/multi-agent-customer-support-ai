import { AxiosError } from "axios";

/**
 * Extract a human-readable error message from an API error.
 *
 * Backend errors arrive as `{ detail: "message" }` (FastAPI convention).
 * Axios wraps them in `err.response.data.detail`. Falls back to a generic
 * message when the shape is unrecognised or the error isn't from Axios.
 */
export function parseApiError(error: unknown, fallback: string): string {
    if (error instanceof AxiosError && error.response?.data) {
        const detail = (error.response.data as Record<string, unknown>).detail;
        if (typeof detail === "string" && detail.length > 0) {
            return detail;
        }
    }
    if (error instanceof Error) {
        return error.message;
    }
    return fallback;
}
