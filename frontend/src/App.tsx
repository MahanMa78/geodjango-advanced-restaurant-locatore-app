import { useState, useEffect } from 'react';
import MapView from './components/MapView';
import ConceptsView from './components/ConceptsView';
import { AuthModal } from './components/AuthModal';
import { fetchUserProfile } from './api';
import type { User } from './types';
import './index.css';

type Tab = 'map' | 'concepts';

export default function App() {
  const [activeTab, setActiveTab] = useState<Tab>('map');
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [currentUser, setCurrentUser] = useState<User | null>(null);

  // بررسی وضعیت لاگین کاربر هنگام لود اولیه برنامه
  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token) {
      fetchUserProfile()
        .then((user) => setCurrentUser(user))
        .catch(() => {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          setCurrentUser(null);
        });
    }
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    setCurrentUser(null);
  };

  return (
    <div className="flex flex-col h-screen overflow-hidden bg-surface">
      {/* Header */}
      <header className="flex items-center justify-between px-6 h-14 bg-white border-b border-edge shrink-0 z-50">
        <a href="#" className="flex items-center gap-2 no-underline">
          <span className="w-2.5 h-2.5 rounded-full bg-brand mt-px" />
          <span className="text-ink font-bold text-lg tracking-tight" style={{ fontFamily: 'Syne, sans-serif' }}>
            NearMe
          </span>
        </a>

        <nav className="flex items-center gap-1 bg-surface rounded-lg p-1 border border-edge">
          {([
            { id: 'map' as Tab, label: '🗺️ Live Map' },
            { id: 'concepts' as Tab, label: '📚 Concepts' },
          ]).map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={[
                'px-4 py-1.5 rounded-md text-sm font-medium transition-all duration-150 cursor-pointer border-0 outline-none',
                activeTab === tab.id
                  ? 'bg-white text-ink shadow-card'
                  : 'bg-transparent text-ink-muted hover:text-ink',
              ].join(' ')}
            >
              {tab.label}
            </button>
          ))}
        </nav>

        {/* Auth Section */}
        <div className="flex items-center gap-3">
          {currentUser ? (
            <div className="flex items-center gap-2">
              <span className="text-xs font-medium text-ink bg-surface px-3 py-1.5 rounded-md border border-edge">
                👤 {currentUser.phone_number}
              </span>
              <button
                onClick={handleLogout}
                className="text-xs font-semibold text-red-600 hover:text-red-700 bg-red-50 hover:bg-red-100 px-2.5 py-1.5 rounded-md transition-colors border-0 cursor-pointer"
              >
                خروج
              </button>
            </div>
          ) : (
            <button
              onClick={() => setIsAuthModalOpen(true)}
              className="text-xs font-semibold text-white bg-brand hover:opacity-90 px-3 py-1.5 rounded-md transition-all border-0 cursor-pointer shadow-sm"
            >
              ورود / ثبت‌نام
            </button>
          )}

          <span className="text-xs font-semibold text-brand bg-brand-soft px-3 py-1 rounded-full">
            GeoDjango Demo
          </span>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {activeTab === 'map' && <MapView />}
        {activeTab === 'concepts' && <ConceptsView />}
      </div>

      {/* Auth Modal */}
      <AuthModal
        isOpen={isAuthModalOpen}
        onClose={() => setIsAuthModalOpen(false)}
        onSuccess={(user) => setCurrentUser(user)}
      />
    </div>
  );
}