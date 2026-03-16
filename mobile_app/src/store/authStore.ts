import { create } from 'zustand';
import { AuthUser } from '../types/domain';

interface AuthState {
  user: AuthUser | null;
  accessToken: string | null;
  setSession: (payload: { user: AuthUser; accessToken: string }) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  accessToken: null,
  setSession: ({ user, accessToken }) => set({ user, accessToken }),
  logout: () => set({ user: null, accessToken: null }),
}));
