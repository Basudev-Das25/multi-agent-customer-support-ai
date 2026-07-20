import { z } from "zod";

export const loginSchema = z.object({
    email: z.string().email("Enter a valid email address."),
    password: z
        .string()
        .min(8, "Password must be at least 8 characters.")
        .max(128, "Password must be at most 128 characters."),
});

export type LoginInput = z.infer<typeof loginSchema>;

export const registerSchema = z.object({
    name: z
        .string()
        .min(1, "Name is required.")
        .max(100, "Name must be at most 100 characters."),
    email: z.string().email("Enter a valid email address."),
    password: z
        .string()
        .min(8, "Password must be at least 8 characters.")
        .max(128, "Password must be at most 128 characters."),
});

export type RegisterInput = z.infer<typeof registerSchema>;
