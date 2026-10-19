import { apiClient } from '../client';
import type { AuthResponse, IAuthService, User } from '../../types';

const STORAGE_CURRENT_USER_KEY = 'link_saver_current_user';
const STORAGE_TOKEN_KEY = 'link_saver_auth_token';

interface BackendUserRead {
  id: string;
  email: string;
  created_at: string;
}

interface BackendToken {
  access_token: string;
  token_type: string;
}

const mapUser = (backendUser: BackendUserRead): User => ({
  id: backendUser.id,
  email: backendUser.email,
  createdAt: backendUser.created_at,
});

export class HttpAuthService implements IAuthService {
  async signup(email: string, password: string): Promise<AuthResponse> {
    try {
      await apiClient.post<BackendUserRead>('/api/v1/auth/signup', {
        email: email.trim(),
        password,
      });

      // Automatically log in after registration
      return await this.login(email, password);
    } catch (error: any) {
      const msg = error.response?.data?.detail || error.message || 'Failed to sign up';
      throw new Error(msg);
    }
  }

  async login(email: string, password: string): Promise<AuthResponse> {
    try {
      const loginResp = await apiClient.post<BackendToken>('/api/v1/auth/login', {
        email: email.trim(),
        password,
      });

      const token = loginResp.data.access_token;
      localStorage.setItem(STORAGE_TOKEN_KEY, token);

      // Fetch user profile
      const userResp = await apiClient.get<BackendUserRead>('/api/v1/auth/me', {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      const user = mapUser(userResp.data);
      localStorage.setItem(STORAGE_CURRENT_USER_KEY, JSON.stringify(user));

      return { user, token };
    } catch (error: any) {
      const msg = error.response?.data?.detail || error.message || 'Failed to log in';
      throw new Error(msg);
    }
  }

  async getCurrentUser(): Promise<User | null> {
    const token = localStorage.getItem(STORAGE_TOKEN_KEY);
    if (!token) return null;

    try {
      const userResp = await apiClient.get<BackendUserRead>('/api/v1/auth/me');
      const user = mapUser(userResp.data);
      localStorage.setItem(STORAGE_CURRENT_USER_KEY, JSON.stringify(user));
      return user;
    } catch {
      localStorage.removeItem(STORAGE_TOKEN_KEY);
      localStorage.removeItem(STORAGE_CURRENT_USER_KEY);
      return null;
    }
  }

  async logout(): Promise<void> {
    localStorage.removeItem(STORAGE_TOKEN_KEY);
    localStorage.removeItem(STORAGE_CURRENT_USER_KEY);
  }
}

export const httpAuthService = new HttpAuthService();
