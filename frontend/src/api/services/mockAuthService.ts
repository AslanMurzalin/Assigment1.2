import type { AuthResponse, IAuthService, User } from '../../types';

const STORAGE_USERS_KEY = 'link_saver_users';
const STORAGE_CURRENT_USER_KEY = 'link_saver_current_user';
const STORAGE_TOKEN_KEY = 'link_saver_auth_token';

const delay = (ms = 250) => new Promise((resolve) => setTimeout(resolve, ms));

interface StoredUser extends User {
  passwordHash: string;
}

export class MockAuthService implements IAuthService {
  private getUsers(): StoredUser[] {
    const raw = localStorage.getItem(STORAGE_USERS_KEY);
    if (!raw) {
      // Default demo user
      const defaultUser: StoredUser = {
        id: 'user-demo-1',
        email: 'demo@linksaver.io',
        passwordHash: 'password123',
        createdAt: new Date().toISOString(),
      };
      localStorage.setItem(STORAGE_USERS_KEY, JSON.stringify([defaultUser]));
      return [defaultUser];
    }
    try {
      return JSON.parse(raw);
    } catch {
      return [];
    }
  }

  private saveUsers(users: StoredUser[]): void {
    localStorage.setItem(STORAGE_USERS_KEY, JSON.stringify(users));
  }

  async signup(email: string, password: string): Promise<AuthResponse> {
    await delay(300);
    const trimmedEmail = email.trim().toLowerCase();
    const users = this.getUsers();

    if (users.some((u) => u.email === trimmedEmail)) {
      throw new Error('A user with this email address already exists');
    }

    if (password.length < 6) {
      throw new Error('Password must be at least 6 characters long');
    }

    const newUser: StoredUser = {
      id: `user-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`,
      email: trimmedEmail,
      passwordHash: password, // In mock service, simple representation
      createdAt: new Date().toISOString(),
    };

    users.push(newUser);
    this.saveUsers(users);

    const token = `mock-jwt-token-${newUser.id}-${Date.now()}`;
    const userSafe: User = {
      id: newUser.id,
      email: newUser.email,
      createdAt: newUser.createdAt,
    };

    localStorage.setItem(STORAGE_TOKEN_KEY, token);
    localStorage.setItem(STORAGE_CURRENT_USER_KEY, JSON.stringify(userSafe));

    return { user: userSafe, token };
  }

  async login(email: string, password: string): Promise<AuthResponse> {
    await delay(250);
    const trimmedEmail = email.trim().toLowerCase();
    const users = this.getUsers();
    const found = users.find((u) => u.email === trimmedEmail);

    if (!found || found.passwordHash !== password) {
      throw new Error('Invalid email or password');
    }

    const token = `mock-jwt-token-${found.id}-${Date.now()}`;
    const userSafe: User = {
      id: found.id,
      email: found.email,
      createdAt: found.createdAt,
    };

    localStorage.setItem(STORAGE_TOKEN_KEY, token);
    localStorage.setItem(STORAGE_CURRENT_USER_KEY, JSON.stringify(userSafe));

    return { user: userSafe, token };
  }

  async getCurrentUser(): Promise<User | null> {
    await delay(100);
    const raw = localStorage.getItem(STORAGE_CURRENT_USER_KEY);
    const token = localStorage.getItem(STORAGE_TOKEN_KEY);
    if (!raw || !token) return null;
    try {
      return JSON.parse(raw);
    } catch {
      return null;
    }
  }

  async logout(): Promise<void> {
    await delay(100);
    localStorage.removeItem(STORAGE_TOKEN_KEY);
    localStorage.removeItem(STORAGE_CURRENT_USER_KEY);
  }
}

export const mockAuthService = new MockAuthService();
