
import {
  createContext,
  useContext,
  useEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";

import { authService } from "../services/authService";
import { setApiAccessToken } from "../services/api";

import type {
  LoginRequest,
  User,
} from "../types/auth";

interface AuthContextType {
  user: User | null;
  accessToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginRequest) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(
  undefined
);

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const sessionRestoreStarted = useRef(false);

  useEffect(() => {
    // Receive renewed access tokens from the Axios interceptor.
    const handleTokenRefreshed = (event: Event) => {
      const customEvent = event as CustomEvent<{
        accessToken: string;
      }>;

      setAccessToken(customEvent.detail.accessToken);
    };

    // Clear the session if the refresh token is no longer valid.
    const handleSessionExpired = () => {
      setApiAccessToken(null);
      setAccessToken(null);
      setUser(null);
    };

    window.addEventListener(
      "auth:token-refreshed",
      handleTokenRefreshed
    );

    window.addEventListener(
      "auth:session-expired",
      handleSessionExpired
    );

    return () => {
      window.removeEventListener(
        "auth:token-refreshed",
        handleTokenRefreshed
      );

      window.removeEventListener(
        "auth:session-expired",
        handleSessionExpired
      );
    };
  }, []);

  // Restore the session when the application starts.
  useEffect(() => {
    if (sessionRestoreStarted.current) {
      return;
    }

    sessionRestoreStarted.current = true;

    const restoreSession = async () => {
      try {
        const response = await authService.refreshSession();

        setApiAccessToken(response.access_token);
        setAccessToken(response.access_token);
        setUser(response.user);
      } catch {
        setApiAccessToken(null);
        setAccessToken(null);
        setUser(null);
      } finally {
        setIsLoading(false);
      }
    };

    void restoreSession();
  }, []);

  const login = async (
    credentials: LoginRequest
  ): Promise<void> => {
    setIsLoading(true);

    try {
      const response = await authService.login(credentials);

      setApiAccessToken(response.access_token);
      setAccessToken(response.access_token);
      setUser(response.user);
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async (): Promise<void> => {
    try {
      await authService.logout();
    } finally {
      setApiAccessToken(null);
      setAccessToken(null);
      setUser(null);
    }
  };

  const value: AuthContextType = {
    user,
    accessToken,
    isAuthenticated: Boolean(user && accessToken),
    isLoading,
    login,
    logout,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error(
      "useAuth must be used within an AuthProvider"
    );
  }

  return context;
}
