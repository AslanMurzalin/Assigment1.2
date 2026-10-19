export type SiteType = 'youtube' | 'generic';

export interface User {
  id: string;
  email: string;
  createdAt: string;
}

export interface Link {
  id: string;
  userId: string;
  url: string;
  title: string;
  description: string;
  siteType: SiteType;
  userNotes: string;
  tags: string[];
  createdAt: string;
  updatedAt?: string;
}

export interface FilterParams {
  q?: string;
  tag?: string;
}

export interface CreateLinkInput {
  url: string;
  userNotes?: string;
  tags?: string[];
}

export interface UpdateLinkInput {
  userNotes?: string;
  tags?: string[];
}

export interface AuthResponse {
  user: User;
  token: string;
}

export interface IAuthService {
  signup(email: string, password: string): Promise<AuthResponse>;
  login(email: string, password: string): Promise<AuthResponse>;
  getCurrentUser(): Promise<User | null>;
  logout(): Promise<void>;
}

export interface DownloadProgress {
  loaded: number;
  total?: number;
  percent?: number;
  speed?: number;
  estimated?: number;
}

export interface ILinkService {
  getLinks(filters?: FilterParams): Promise<Link[]>;
  getLinkById(id: string): Promise<Link>;
  createLink(input: CreateLinkInput): Promise<Link>;
  updateLink(id: string, input: UpdateLinkInput): Promise<Link>;
  deleteLink(id: string): Promise<void>;
  downloadVideo(
    id: string,
    onProgress?: (progress: DownloadProgress) => void
  ): Promise<{ downloadUrl: string; filename: string }>;
}
