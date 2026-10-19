import React, { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { UserPlus, AlertCircle } from 'lucide-react';

interface RegisterFormProps {
  onSwitchToLogin: () => void;
}

export const RegisterForm: React.FC<RegisterFormProps> = ({ onSwitchToLogin }) => {
  const { signup } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const trimmedEmail = email.trim();
    if (!trimmedEmail || !password) {
      setError('Please fill in all required fields.');
      return;
    }

    if (password.length < 6) {
      setError('Password must be at least 6 characters.');
      return;
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    setIsSubmitting(true);
    try {
      await signup(trimmedEmail, password);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Registration failed.';
      setError(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="w-full max-w-md p-6 sm:p-8 bg-white rounded-2xl shadow-xs border border-stone-200">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2.5 bg-orange-50 text-orange-600 rounded-xl">
          <UserPlus className="w-6 h-6" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-stone-900 tracking-tight">Create an account</h1>
          <p className="text-sm text-stone-500">Start organizing and streaming your links</p>
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
          <label htmlFor="reg-email" className="block text-sm font-medium text-stone-700 mb-1">
            Email address
          </label>
          <input
            id="reg-email"
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
          <label htmlFor="reg-password" className="block text-sm font-medium text-stone-700 mb-1">
            Password (min 6 characters)
          </label>
          <input
            id="reg-password"
            name="password"
            type="password"
            autoComplete="new-password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
            className="w-full px-3.5 py-2.5 text-sm rounded-xl border border-stone-300 focus:outline-none focus:ring-2 focus:ring-orange-500/20 focus:border-orange-600 transition"
          />
        </div>

        <div>
          <label htmlFor="reg-confirm-password" className="block text-sm font-medium text-stone-700 mb-1">
            Confirm password
          </label>
          <input
            id="reg-confirm-password"
            name="confirmPassword"
            type="password"
            autoComplete="new-password"
            required
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
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
            'Sign Up'
          )}
        </button>
      </form>

      <div className="mt-6 pt-5 border-t border-stone-100 text-center">
        <p className="text-sm text-stone-600">
          Already have an account?{' '}
          <button
            type="button"
            onClick={onSwitchToLogin}
            className="font-medium text-orange-600 hover:text-orange-800 transition"
          >
            Sign in
          </button>
        </p>
      </div>
    </div>
  );
};
