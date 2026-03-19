import type { SignInResponse } from "../types";

export const API_URL = (
  import.meta.env.VITE_API_URL || "http://localhost:5000"
).replace(/\/$/, "");

async function fetcher<T>(path: string, options?: RequestInit): Promise<T> {
  const isFormData = options?.body instanceof FormData;

  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      ...(isFormData ? {} : { "Content-Type": "application/json" }),
      ...options?.headers,
    },
  });

  if (res.status === 204) return undefined as T;

  const body = await res.json().catch(() => ({}));
  if (!res.ok)
    throw new Error(body.message ?? body.error ?? `Erreur ${res.status}`);

  return body as T;
}

export const api = {
  signIn: (email: string, password: string) =>
    fetcher<SignInResponse | string>("/api/sign-in", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  signUp: (email: string, password: string) =>
    fetcher<SignInResponse | string>("/api/sign-up", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  getDocuments: (token: string) =>
    fetcher<unknown[]>("/api/documents", {
      headers: { Authorization: `Bearer ${token}` },
    }),

  uploadDocument: (file: File, token: string) => {
    const formData = new FormData();
    formData.append("uploadedDocument", file);
    return fetcher<unknown>("/api/upload", {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: formData,
    });
  },

  deleteDocument: (id: string, token: string) =>
    fetcher<void>(`/api/documents/${id}`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    }),
};
