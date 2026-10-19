import React, { createContext, useContext, useEffect, useState } from 'react';
import type { IAuthService, User } from '../types';
import { mockAuthService } from '../api/services/mockAuthService';

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: React.ReactNode;
  authService?: IAuthService;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({
  children,
  authService = mockAuthService,
}) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    const initAuth = async () => {
      try {
        const currentUser = await authService.getCurrentUser();
        const storedToken = localStorage.getItem('link_saver_auth_token');
        if (currentUser && storedToken) {
          setUser(currentUser);
          setToken(storedToken);
        }
      } catch (err) {
        console.error('Failed to restore auth session:', err);
      } finally {
        setIsLoading(false);
      }
    };
    initAuth();
  }, [authService]);

  const login = async (email: string, password: string) => {
    setIsLoading(true);
    try {
      const resp = await authService.login(email, password);
      setUser(resp.user);
      setToken(resp.token);
    } finally {
      setIsLoading(false);
    }
  };

  const signup = async (email: string, password: string) => {
    setIsLoading(true);
    try {
      const resp = await authService.signup(email, password);
      setUser(resp.user);
      setToken(resp.token);
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    setIsLoading(true);
    try {
      await authService.logout();
      setUser(null);
      setToken(null);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isLoading,
        isAuthenticated: !!user && !!token,
        login,
        signup,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
