import { UserProfile } from '../types';
import { INITIAL_USER } from '../data/mockData';

const AUTH_STORAGE_KEY = 'taskmate_auth_user';

export interface AuthState {
  user: UserProfile | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

type AuthListener = (user: UserProfile | null) => void;
const listeners: Set<AuthListener> = new Set();

function notifyListeners(user: UserProfile | null) {
  listeners.forEach((listener) => listener(user));
}

export const authService = {
  getCurrentUser(): UserProfile | null {
    try {
      const stored = localStorage.getItem(AUTH_STORAGE_KEY);
      if (stored) {
        return JSON.parse(stored);
      }
    } catch {
      // Fallback
    }
    return INITIAL_USER;
  },

  async signInWithEmail(email: string, _password: string): Promise<UserProfile> {
    // Simulate brief network latency for realistic SaaS feel
    await new Promise((resolve) => setTimeout(resolve, 400));
    
    const user: UserProfile = {
      id: `user_${email.replace(/[^a-zA-Z0-9]/g, '')}`,
      name: email.split('@')[0].replace('.', ' ').replace(/\b\w/g, (l) => l.toUpperCase()),
      email,
      avatar: `https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80`,
      preferences: {
        dailyGoal: 5,
        defaultPriority: 'medium',
      },
    };
    localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(user));
    notifyListeners(user);
    return user;
  },

  async signUpWithEmail(name: string, email: string, _password: string): Promise<UserProfile> {
    await new Promise((resolve) => setTimeout(resolve, 400));
    
    const user: UserProfile = {
      id: `user_${Date.now()}`,
      name: name.trim() || 'Productivity Explorer',
      email,
      avatar: `https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80`,
      preferences: {
        dailyGoal: 5,
        defaultPriority: 'medium',
      },
    };
    localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(user));
    notifyListeners(user);
    return user;
  },

  async signInWithDemo(): Promise<UserProfile> {
    await new Promise((resolve) => setTimeout(resolve, 250));
    const user = INITIAL_USER;
    localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(user));
    notifyListeners(user);
    return user;
  },

  async signOut(): Promise<void> {
    await new Promise((resolve) => setTimeout(resolve, 200));
    localStorage.removeItem(AUTH_STORAGE_KEY);
    notifyListeners(null);
  },

  async sendPasswordResetEmail(_email: string): Promise<{ success: boolean; message: string }> {
    await new Promise((resolve) => setTimeout(resolve, 400));
    return {
      success: true,
      message: 'Password reset instructions have been sent to your email address.',
    };
  },

  onAuthStateChanged(callback: AuthListener): () => void {
    listeners.add(callback);
    callback(this.getCurrentUser());
    return () => {
      listeners.delete(callback);
    };
  },
};
