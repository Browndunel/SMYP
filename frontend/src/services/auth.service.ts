import { api } from "./api";
import type { SignInResponse } from "../types";

function normalizeAuthResponse(
  response: SignInResponse | string,
): SignInResponse {
  return typeof response === "string" ? { token: response } : response;
}

export const authService = {
  signIn: async (email: string, password: string): Promise<SignInResponse> =>
    normalizeAuthResponse(await api.signIn(email, password)),

  signUp: async (email: string, password: string): Promise<SignInResponse> =>
    normalizeAuthResponse(await api.signUp(email, password)),
};
