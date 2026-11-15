import api from "./api";

import type {
  LoginRequest,
  RegisterRequest,
  TokenResponse,
  User,
} from "../types/auth";

export const authService = {
  async register(data: RegisterRequest): Promise<User> {
    const response = await api.post<User>(
      "/auth/register",
      data
    );

    return response.data;
  },

  async login(data: LoginRequest): Promise<TokenResponse> {
    const response = await api.post<TokenResponse>(
      "/auth/login",
      data
    );

    return response.data;
  },

  async refreshSession(): Promise<TokenResponse> {
    const response = await api.post<TokenResponse>(
      "/auth/refresh"
    );

    return response.data;
  },

  async getCurrentUser(): Promise<User> {
  const response = await api.get<User>("/auth/me");
  return response.data;
  },

  async logout(): Promise<void> {
    await api.post("/auth/logout");
  },
};