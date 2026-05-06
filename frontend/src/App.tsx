import { useState } from 'react';
import MapView from './components/MapView';
import ConceptsView from './components/ConceptsView';
import './index.css';

type Tab = 'map' | 'concepts';

export default function App() {
  const [activeTab, setActiveTab] = useState<Tab>('map');

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

        <span className="text-xs font-semibold text-brand bg-brand-soft px-3 py-1 rounded-full">
          GeoDjango Demo
        </span>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {activeTab === 'map' && <MapView />}
        {activeTab === 'concepts' && <ConceptsView />}
      </div>
    </div>
  );
}