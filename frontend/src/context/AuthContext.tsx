import React, { createContext, useContext, useEffect, useState } from 'react';
import type { IAuthService, User } from '../types';
import { httpAuthService } from '../api/services/httpAuthService';

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
  authService = httpAuthService,
}) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    const handleUnauthorized = () => {
      setUser(null);
      setToken(null);
    };

    window.addEventListener('auth:unauthorized', handleUnauthorized);

    const initAuth = async () => {
      try {
        const currentUser = await authService.getCurrentUser();
        const storedToken = localStorage.getItem('link_saver_auth_token');
        if (currentUser && storedToken) {
          setUser(currentUser);
          setToken(storedToken);
        } else {
          setUser(null);
          setToken(null);
        }
      } catch (err) {
        console.error('Failed to restore auth session:', err);
        setUser(null);
        setToken(null);
      } finally {
        setIsLoading(false);
      }
    };

    initAuth();

    return () => {
      window.removeEventListener('auth:unauthorized', handleUnauthorized);
    };
  }, [authService]);

  const login = async (email: string, password: string) => {
    const resp = await authService.login(email, password);
    setUser(resp.user);
    setToken(resp.token);
  };

  const signup = async (email: string, password: string) => {
    const resp = await authService.signup(email, password);
    setUser(resp.user);
    setToken(resp.token);
  };

  const logout = async () => {
    try {
      await authService.logout();
    } finally {
      setUser(null);
      setToken(null);
    }
  };

  const value: AuthContextType = {
    user,
    token,
    isLoading,
    isAuthenticated: Boolean(user && token),
    login,
    signup,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
