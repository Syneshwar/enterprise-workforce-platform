import axios, {
  type InternalAxiosRequestConfig,
} from "axios";

import type { TokenResponse } from "../types/auth";

function getCsrfToken(): string | null {
  const csrfCookie = document.cookie
    .split(";")
    .map((cookie) => cookie.trim())
    .find((cookie) => cookie.startsWith("csrf_token="));

  if (!csrfCookie) {
    return null;
  }

  try {
    return decodeURIComponent(
      csrfCookie.substring("csrf_token=".length)
    );
  } catch {
    return null;
  }
}

const api = axios.create({
  baseURL: import.meta.env.VITE_AUTH_API_URL,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 15000,
  withCredentials: true,
});

// Keep the access token in memory, not localStorage.
let accessToken: string | null = null;

// Share one refresh request when multiple API calls fail together.
let refreshPromise: Promise<string> | null = null;

interface RetryableRequestConfig
  extends InternalAxiosRequestConfig {
  _retry?: boolean;
}

export function setApiAccessToken(token: string | null): void {
  accessToken = token;
}

// Attach the current access token to protected API requests.
api.interceptors.request.use((config) => {
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`;
  }

  const method = config.method?.toLowerCase();

  const unsafeMethods = ["post", "put", "patch", "delete"];

  if (method && unsafeMethods.includes(method)) {
    const csrfToken = getCsrfToken();

    if (csrfToken) {
      config.headers.set("X-CSRF-Token", csrfToken);
    }
  }

  return config;
});

// Renew the access token after an unauthorized response.
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest =
      error.config as RetryableRequestConfig | undefined;

    if (!originalRequest || error.response?.status !== 401) {
      return Promise.reject(error);
    }

    const url = originalRequest.url ?? "";

    // Never try to refresh when authentication endpoints fail.
    const excludedEndpoints = [
      "/auth/login",
      "/auth/register",
      "/auth/refresh",
      "/auth/logout",
    ];

    if (
      excludedEndpoints.some((endpoint) =>
        url.includes(endpoint)
      ) ||
      originalRequest._retry
    ) {
      return Promise.reject(error);
    }

    originalRequest._retry = true;

    try {
      if (!refreshPromise) {
        refreshPromise = api
          .post<TokenResponse>("/auth/refresh")
          .then((response) => {
            const newToken = response.data.access_token;

            setApiAccessToken(newToken);

            window.dispatchEvent(
              new CustomEvent("auth:token-refreshed", {
                detail: { accessToken: newToken },
              })
            );

            return newToken;
          })
          .catch((refreshError) => {
            setApiAccessToken(null);

            window.dispatchEvent(
              new Event("auth:session-expired")
            );

            throw refreshError;
          })
          .finally(() => {
            refreshPromise = null;
          });
      }

      const newToken = await refreshPromise;

      originalRequest.headers.Authorization =
        `Bearer ${newToken}`;

      // Retry the original request with the renewed token.
      return api(originalRequest);
    } catch (refreshError) {
      return Promise.reject(refreshError);
    }
  }
);

export default api;