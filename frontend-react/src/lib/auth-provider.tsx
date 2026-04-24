import { useEffect, useMemo, useState } from 'react';
import type { ReactNode } from 'react';

import {
  fetchMe,
  login as loginRequest,
  logout as logoutRequest,
  migrateAnonymousData,
  register as registerRequest,
} from '@/lib/api';
import { AuthContext, type AuthContextValue } from '@/lib/auth';
import { clearPaperMarks, getAllPaperMarks, getUserId } from '@/lib/storage';
import type { AuthUser } from '@/types';

async function migrateLegacyLocalData(): Promise<void> {
  const anonymousUserId = getUserId();
  const paperMarks = getAllPaperMarks();
  try {
    await migrateAnonymousData(anonymousUserId, paperMarks);
    clearPaperMarks();
  } catch (error) {
    console.warn('Failed to migrate legacy local data', error);
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const refresh = async () => {
    try {
      const payload = await fetchMe();
      setUser(payload.user);
    } catch {
      setUser(null);
    }
  };

  useEffect(() => {
    void refresh().finally(() => setIsLoading(false));
  }, []);

  const value = useMemo<AuthContextValue>(() => ({
    user,
    isLoading,
    login: async (email: string, password: string) => {
      const payload = await loginRequest(email, password);
      setUser(payload.user);
      await migrateLegacyLocalData();
    },
    register: async (email: string, password: string, invitationCode: string) => {
      const payload = await registerRequest(email, password, invitationCode);
      setUser(payload.user);
      await migrateLegacyLocalData();
    },
    logout: async () => {
      await logoutRequest();
      setUser(null);
    },
    refresh,
  }), [isLoading, user]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
