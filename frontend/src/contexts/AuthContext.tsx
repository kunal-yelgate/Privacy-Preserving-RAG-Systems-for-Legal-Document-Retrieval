"use client";

/**
 * AuthContext — Centralizes login state and eliminates the race condition between
 * Navbar login and page-level API calls. All pages use useAuth() to wait for
 * authReady before making authenticated requests.
 */
import React, { createContext, useContext, useEffect, useState, useCallback } from "react";
import { api } from "@/lib/api/client";
import { User } from "@/types";

interface AuthContextValue {
  user: User | null;
  authReady: boolean;
  backendOnline: boolean;
  retryAuth: () => void;
}

const AuthContext = createContext<AuthContextValue>({
  user: null,
  authReady: false,
  backendOnline: false,
  retryAuth: () => {},
});

export function useAuth() {
  return useContext(AuthContext);
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [authReady, setAuthReady] = useState(false);
  const [backendOnline, setBackendOnline] = useState(false);

  const initAuth = useCallback(async () => {
    setAuthReady(false);
    try {
      // Only attempt login if we don't have a valid token in sessionStorage
      if (!api.getToken()) {
        await api.login("admin", "AdminSecureOffline2026!");
      }
      const me = await api.getMe();
      setUser(me);
      setBackendOnline(true);
    } catch (err: any) {
      // Login failed (wrong credentials or backend offline) — clear stale token
      console.warn("[AuthContext] Backend auth failed:", err?.message);
      api.setToken(null);
      setUser(null);
      setBackendOnline(false);
    } finally {
      // Always mark ready so pages can render their own error state
      setAuthReady(true);
    }
  }, []);

  useEffect(() => {
    initAuth();
  }, [initAuth]);

  return (
    <AuthContext.Provider value={{ user, authReady, backendOnline, retryAuth: initAuth }}>
      {children}
    </AuthContext.Provider>
  );
}
