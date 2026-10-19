import React from 'react';
import { useAuth } from '../../context/AuthContext';
import { Bookmark, LogOut, User as UserIcon } from 'lucide-react';

export const Navbar: React.FC = () => {
  const { user, logout } = useAuth();

  return (
    <header className="sticky top-0 z-30 bg-white/90 backdrop-blur-md border-b border-stone-200">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-orange-600 to-amber-500 flex items-center justify-center text-white shadow-xs shadow-orange-200">
            <Bookmark className="w-5 h-5 fill-current" />
          </div>
          <div>
            <span className="text-lg font-bold text-stone-900 tracking-tight">
              Link Saver
            </span>
            <span className="hidden sm:inline-block ml-2 px-2 py-0.5 text-[10px] font-semibold text-orange-700 bg-orange-50 border border-orange-200 rounded-full">
              v1
            </span>
          </div>
        </div>

        {/* User Info & Actions */}
        {user && (
          <div className="flex items-center gap-2 sm:gap-4">
            <div className="hidden xs:flex items-center gap-2 px-3 py-1.5 rounded-full bg-stone-100 text-xs font-medium text-stone-700 border border-stone-200">
              <UserIcon className="w-3.5 h-3.5 text-stone-400" />
              <span className="truncate max-w-[140px] sm:max-w-[200px]">{user.email}</span>
            </div>

            <button
              onClick={() => logout()}
              type="button"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs sm:text-sm font-medium text-stone-600 hover:text-stone-900 bg-white hover:bg-stone-100 border border-stone-200 rounded-xl transition"
              title="Sign out of account"
            >
              <LogOut className="w-4 h-4 text-stone-400" />
              <span className="hidden sm:inline">Logout</span>
            </button>
          </div>
        )}
      </div>
    </header>
  );
};
