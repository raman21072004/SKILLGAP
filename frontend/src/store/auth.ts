import { create } from "zustand";
import { authApi } from "@/services/api";
import type { User } from "@/types/api";

interface AuthState {
  user: User | null;
  status: "unknown" | "authenticated" | "anonymous";
  restore: () => Promise<void>;
  login: (email: string, password: string) => Promise<void>;
  register: (name: string, email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  setUser: (u: User | null) => void;
}

// Only the user profile is kept in memory; the session token stays in an httpOnly cookie.
export const useAuth = create<AuthState>((set) => ({
  user: null,
  status: "unknown",
  restore: async () => {
    try {
      const user = await authApi.me();
      set({ user, status: "authenticated" });
    } catch {
      set({ user: null, status: "anonymous" });
    }
  },
  login: async (email, password) => {
    const user = await authApi.login(email, password);
    set({ user, status: "authenticated" });
  },
  register: async (name, email, password) => {
    const user = await authApi.register(name, email, password);
    set({ user, status: "authenticated" });
  },
  logout: async () => {
    try {
      await authApi.logout();
    } finally {
      set({ user: null, status: "anonymous" });
    }
  },
  setUser: (user) => set({ user, status: user ? "authenticated" : "anonymous" }),
}));
