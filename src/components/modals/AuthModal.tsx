import React, { useState } from 'react';
import { useApp } from '../../context/AppContext';
import { X, CheckSquare, Mail, Lock, User, ArrowRight, Sparkles } from 'lucide-react';

export const AuthModal: React.FC = () => {
  const {
    isAuthModalOpen,
    authModalMode,
    openAuthModal,
    closeAuthModal,
    signInWithEmail,
    signUpWithEmail,
    signInDemoUser,
    showToast,
  } = useApp();

  const [name, setName] = useState('');
  const [email, setEmail] = useState('alex.morgan@example.com');
  const [password, setPassword] = useState('••••••••');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isAuthModalOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (authModalMode === 'signin') {
        await signInWithEmail(email, password);
      } else if (authModalMode === 'signup') {
        if (!name.trim()) {
          throw new Error('Please enter your full name');
        }
        await signUpWithEmail(name, email, password);
      } else if (authModalMode === 'forgot') {
        await new Promise((r) => setTimeout(r, 400));
        showToast(`Reset instructions sent to ${email}`, 'info');
        closeAuthModal();
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      id="auth-modal-backdrop"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-stone-900/40 backdrop-blur-xs animate-in fade-in duration-150"
    >
      <div
        id="auth-modal-card"
        className="bg-white rounded-3xl p-6 sm:p-8 border border-stone-200 shadow-2xl max-w-md w-full space-y-6 animate-in zoom-in-95 duration-150"
      >
        {/* Header */}
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-10 h-10 rounded-xl bg-indigo-600 text-white flex items-center justify-center shadow-xs">
              <CheckSquare className="w-5 h-5 stroke-[2.2]" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-stone-900">
                {authModalMode === 'signin' && 'Welcome back to TaskMate'}
                {authModalMode === 'signup' && 'Create your TaskMate account'}
                {authModalMode === 'forgot' && 'Reset your password'}
              </h3>
              <p className="text-xs text-stone-500">
                {authModalMode === 'signin' && 'Sign in to access your AI assistant and tasks'}
                {authModalMode === 'signup' && 'Start organizing your productivity with AI'}
                {authModalMode === 'forgot' && 'Enter your email to receive recovery link'}
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={closeAuthModal}
            className="p-1.5 rounded-lg text-stone-400 hover:text-stone-700 hover:bg-stone-100 transition-colors cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {error && (
          <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-700 font-medium">
            {error}
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4 text-xs">
          {authModalMode === 'signup' && (
            <div>
              <label className="block text-xs font-semibold text-stone-700 mb-1.5">
                Full Name
              </label>
              <div className="relative">
                <User className="w-4 h-4 text-stone-400 absolute left-3.5 top-3" />
                <input
                  type="text"
                  required
                  placeholder="Alex Morgan"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 bg-stone-50 border border-stone-200 rounded-xl text-stone-900 focus:bg-white focus:border-indigo-600 focus:outline-hidden transition-colors"
                />
              </div>
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-stone-700 mb-1.5">
              Email Address
            </label>
            <div className="relative">
              <Mail className="w-4 h-4 text-stone-400 absolute left-3.5 top-3" />
              <input
                type="email"
                required
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 bg-stone-50 border border-stone-200 rounded-xl text-stone-900 focus:bg-white focus:border-indigo-600 focus:outline-hidden transition-colors"
              />
            </div>
          </div>

          {authModalMode !== 'forgot' && (
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="text-xs font-semibold text-stone-700">
                  Password
                </label>
                {authModalMode === 'signin' && (
                  <button
                    type="button"
                    onClick={() => openAuthModal('forgot')}
                    className="text-[11px] text-indigo-600 hover:text-indigo-700 font-medium cursor-pointer"
                  >
                    Forgot password?
                  </button>
                )}
              </div>
              <div className="relative">
                <Lock className="w-4 h-4 text-stone-400 absolute left-3.5 top-3" />
                <input
                  type="password"
                  required
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 bg-stone-50 border border-stone-200 rounded-xl text-stone-900 focus:bg-white focus:border-indigo-600 focus:outline-hidden transition-colors"
                />
              </div>
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs shadow-xs transition-all active:scale-95 disabled:opacity-50 cursor-pointer flex items-center justify-center gap-2"
          >
            <span>
              {loading
                ? 'Processing...'
                : authModalMode === 'signin'
                ? 'Sign In to TaskMate'
                : authModalMode === 'signup'
                ? 'Create Account'
                : 'Send Reset Link'}
            </span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </form>

        {/* Demo User Fast Action */}
        <div className="pt-4 border-t border-stone-100">
          <button
            type="button"
            onClick={signInDemoUser}
            className="w-full py-2.5 px-4 rounded-xl bg-stone-100 hover:bg-stone-200/80 text-stone-800 text-xs font-semibold flex items-center justify-center gap-2 transition-colors cursor-pointer"
          >
            <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
            <span>Continue as Demo User (Alex Morgan)</span>
          </button>
        </div>

        {/* Mode Switcher */}
        <div className="text-center text-xs text-stone-500">
          {authModalMode === 'signin' ? (
            <p>
              Don&apos;t have an account yet?{' '}
              <button
                type="button"
                onClick={() => openAuthModal('signup')}
                className="font-bold text-indigo-600 hover:underline cursor-pointer"
              >
                Sign up free
              </button>
            </p>
          ) : (
            <p>
              Already have an account?{' '}
              <button
                type="button"
                onClick={() => openAuthModal('signin')}
                className="font-bold text-indigo-600 hover:underline cursor-pointer"
              >
                Sign in
              </button>
            </p>
          )}
        </div>
      </div>
    </div>
  );
};
