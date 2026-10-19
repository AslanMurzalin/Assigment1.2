import React, { useState } from 'react';
import { LoginForm } from '../components/auth/LoginForm';
import { RegisterForm } from '../components/auth/RegisterForm';
import { Bookmark } from 'lucide-react';

export const AuthPage: React.FC = () => {
  const [isRegister, setIsRegister] = useState(false);

  return (
    <div className="min-h-screen bg-stone-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center mb-6">
        <div className="w-12 h-12 mx-auto rounded-2xl bg-gradient-to-tr from-orange-600 to-amber-500 flex items-center justify-center text-white shadow-md shadow-orange-200 mb-3">
          <Bookmark className="w-6 h-6 fill-current" />
        </div>
        <h2 className="text-3xl font-extrabold text-stone-900 tracking-tight">
          Link Saver
        </h2>
        <p className="text-sm text-stone-500 mt-1">
          Save, organize, and stream videos directly to your device
        </p>
      </div>

      <div className="sm:mx-auto sm:w-full sm:max-w-md px-4">
        {isRegister ? (
          <RegisterForm onSwitchToLogin={() => setIsRegister(false)} />
        ) : (
          <LoginForm onSwitchToRegister={() => setIsRegister(true)} />
        )}
      </div>

      <div className="mt-8 text-center text-xs text-stone-400">
        Demo mode active • Powered by MockService
      </div>
    </div>
  );
};
