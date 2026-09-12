import {
  createUserWithEmailAndPassword,
  signInWithEmailAndPassword,
  signInWithPopup,
  signInAnonymously,
  signOut as firebaseSignOut,
  sendPasswordResetEmail as firebaseSendPasswordResetEmail,
  onAuthStateChanged as firebaseOnAuthStateChanged,
  updateProfile,
  User as FirebaseUser,
} from 'firebase/auth';
import { auth, googleProvider } from './firebase';
import { UserProfile } from '../types';

/**
 * Maps a Firebase User object to the TaskMate UserProfile domain model.
 * Strict rule: user_id always mirrors the verified Firebase UID.
 */
export function mapFirebaseUser(user: FirebaseUser): UserProfile {
  return {
    id: user.uid,
    name: user.displayName || (user.email ? user.email.split('@')[0] : 'User'),
    email: user.email || '',
    avatar:
      user.photoURL ||
      `https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=150&auto=format&fit=crop&q=80`,
    preferences: {
      dailyGoal: 5,
      defaultPriority: 'medium',
    },
  };
}

export const authService = {
  /**
   * Returns current authenticated user profile, or null if unauthenticated.
   */
  getCurrentUser(): UserProfile | null {
    const fbUser = auth.currentUser;
    return fbUser ? mapFirebaseUser(fbUser) : null;
  },

  /**
   * Retrieves a real Firebase ID token (JWT) for inclusion in backend requests:
   * Authorization: Bearer <ID_TOKEN>
   */
  async getIdToken(forceRefresh: boolean = false): Promise<string | null> {
    const fbUser = auth.currentUser;
    if (!fbUser) return null;
    return await fbUser.getIdToken(forceRefresh);
  },

  /**
   * Sign in an existing user using Firebase Email/Password provider.
   */
  async signInWithEmail(email: string, pass: string): Promise<UserProfile> {
    const cred = await signInWithEmailAndPassword(auth, email, pass);
    return mapFirebaseUser(cred.user);
  },

  /**
   * Register a new user using Firebase Email/Password provider.
   */
  async signUpWithEmail(name: string, email: string, pass: string): Promise<UserProfile> {
    const cred = await createUserWithEmailAndPassword(auth, email, pass);
    if (name && name.trim()) {
      await updateProfile(cred.user, { displayName: name.trim() });
    }
    return mapFirebaseUser(cred.user);
  },

  /**
   * Sign in using Google OAuth popup provider.
   */
  async signInWithGoogle(): Promise<UserProfile> {
    const cred = await signInWithPopup(auth, googleProvider);
    return mapFirebaseUser(cred.user);
  },

  /**
   * Sign in using Firebase Anonymous Authentication for demo / evaluation.
   * Produces a real verified Firebase UID and JWT token.
   */
  async signInWithDemo(): Promise<UserProfile> {
    const cred = await signInAnonymously(auth);
    return mapFirebaseUser(cred.user);
  },

  /**
   * Sign out the current authenticated user from Firebase.
   */
  async signOut(): Promise<void> {
    await firebaseSignOut(auth);
  },

  /**
   * Trigger Firebase password reset email.
   */
  async sendPasswordResetEmail(email: string): Promise<{ success: boolean; message: string }> {
    await firebaseSendPasswordResetEmail(auth, email);
    return {
      success: true,
      message: 'Password reset instructions have been sent to your email address.',
    };
  },

  /**
   * Real-time Firebase Authentication state observer.
   */
  onAuthStateChanged(callback: (user: UserProfile | null) => void): () => void {
    return firebaseOnAuthStateChanged(auth, (fbUser) => {
      callback(fbUser ? mapFirebaseUser(fbUser) : null);
    });
  },
};
