import React, { createContext, useContext, useEffect, useState } from 'react';
import { api } from '../api/client';
import { UserProfile } from '../types/api';

interface AuthContextType {
  user: UserProfile | null;
  isAuthenticated: boolean;
  demoMode: boolean;
  loading: boolean;
  error: string | null;
  loginAsDemo: (role: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshSession: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [demoMode, setDemoMode] = useState<boolean>(true);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const refreshSession = async () => {
    try {
      setLoading(true);
      setError(null);
      const session = await api.getSession();
      setUser(session.user);
      setDemoMode(session.demo_mode);
      if (!session.authenticated && session.demo_mode) {
        // Auto-login as analyst for smooth local developer demo experience
        const loginData = await api.demoLogin('analyst');
        setUser(loginData.user);
      }
    } catch (err: any) {
      setError(err.message || 'Session lookup failed');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refreshSession();
  }, []);

  const loginAsDemo = async (role: string) => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.demoLogin(role);
      setUser(res.user);
    } catch (err: any) {
      setError(err.message || 'Demo login failed');
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    try {
      await api.logout();
      setUser(null);
    } catch (err: any) {
      setError(err.message || 'Logout failed');
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        demoMode,
        loading,
        error,
        loginAsDemo,
        logout,
        refreshSession,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within an AuthProvider');
  return ctx;
};
