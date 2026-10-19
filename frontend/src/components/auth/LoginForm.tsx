import React, { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { LogIn, AlertCircle } from 'lucide-react';

interface LoginFormProps {
  onSwitchToRegister: () => void;
}

export const LoginForm: React.FC<LoginFormProps> = ({ onSwitchToRegister }) => {
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!email.trim() || !password) {
      setError('Please fill in both email and password.');
      return;
    }

    setIsSubmitting(true);
    try {
      await login(email, password);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Login failed. Please check credentials.';
      setError(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="w-full max-w-md p-6 sm:p-8 bg-white rounded-2xl shadow-xs border border-stone-200">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2.5 bg-orange-50 text-orange-600 rounded-xl">
          <LogIn className="w-6 h-6" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-stone-900 tracking-tight">Welcome back</h1>
          <p className="text-sm text-stone-500">Sign in to access your saved links</p>
        </div>
      </div>

      {error && (
        <div
          role="alert"
          className="flex items-center gap-2 p-3.5 mb-5 text-sm text-rose-700 bg-rose-50 border border-rose-200 rounded-xl"
        >
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} method="POST" className="space-y-4">
        <div>
          <label htmlFor="login-email" className="block text-sm font-medium text-stone-700 mb-1">
            Email address
          </label>
          <input
            id="login-email"
            name="email"
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
            className="w-full px-3.5 py-2.5 text-sm rounded-xl border border-stone-300 focus:outline-none focus:ring-2 focus:ring-orange-500/20 focus:border-orange-600 transition"
          />
        </div>

        <div>
          <div className="flex justify-between items-center mb-1">
            <label htmlFor="login-password" className="block text-sm font-medium text-stone-700">
              Password
            </label>
          </div>
          <input
            id="login-password"
            name="password"
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
            className="w-full px-3.5 py-2.5 text-sm rounded-xl border border-stone-300 focus:outline-none focus:ring-2 focus:ring-orange-500/20 focus:border-orange-600 transition"
          />
        </div>

        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full py-2.5 px-4 bg-orange-600 hover:bg-orange-700 text-white font-medium rounded-xl shadow-xs hover:shadow transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {isSubmitting ? (
            <span className="inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
          ) : (
            'Sign In'
          )}
        </button>
      </form>

      <div className="mt-6 pt-5 border-t border-stone-100 text-center">
        <p className="text-sm text-stone-600">
          Don't have an account?{' '}
          <button
            type="button"
            onClick={onSwitchToRegister}
            className="font-medium text-orange-600 hover:text-orange-800 transition"
          >
            Create account
          </button>
        </p>
      </div>
    </div>
  );
};
