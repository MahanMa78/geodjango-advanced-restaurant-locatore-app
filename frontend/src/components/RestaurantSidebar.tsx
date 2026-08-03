import type { RestaurantSidebarProps, RestaurantCardProps } from '../types';

export default function RestaurantSidebar({
  restaurants,
  loading,
  categories,
  activeCategory,
  onCategoryChange,
  radius,
  onRadiusChange,
  searchTerm,
  onSearchChange,
  selectedRestaurant,
  onRestaurantClick,
  userLocation,
}: RestaurantSidebarProps) {
  return (
    <aside className="w-[360px] shrink-0 flex flex-col bg-white border-r border-edge overflow-hidden">

      {/* ── Panel header ── */}
      <div className="px-5 pt-5 pb-4 border-b border-edge shrink-0">
        <h1 className="text-xl font-bold text-ink tracking-tight leading-none mb-1" style={{ fontFamily: 'Syne, sans-serif' }}>
          Food Near You
        </h1>
        <p className="text-xs text-ink-faint leading-snug">
          {userLocation
            ? `Within ${radius} km · ${userLocation.lat.toFixed(3)}, ${userLocation.lng.toFixed(3)}`
            : 'Click the map to set your location'}
        </p>
      </div>

      {/* ── Search + radius ── */}
      <div className="px-4 py-3 border-b border-edge shrink-0">
        <div className="flex gap-2">
          <div className="relative flex-1">
            <svg
              className="absolute left-3 top-1/2 -translate-y-1/2 text-ink-faint pointer-events-none"
              width="13" height="13" viewBox="0 0 24 24" fill="none"
              stroke="currentColor" strokeWidth="2.5"
            >
              <circle cx="11" cy="11" r="8" /><path d="m21 21-4.35-4.35" />
            </svg>
            <input
              type="text"
              placeholder="Search restaurants…"
              value={searchTerm}
              onChange={(e) => onSearchChange(e.target.value)}
              className="w-full h-9 pl-8 pr-3 text-sm bg-surface border border-edge rounded-lg text-ink placeholder-ink-faint focus:outline-none focus:border-brand transition-colors"
            />
          </div>
          <select
            value={radius}
            onChange={(e) => onRadiusChange(Number(e.target.value))}
            className="h-9 px-2.5 text-sm bg-surface border border-edge rounded-lg text-ink-muted focus:outline-none cursor-pointer"
          >
            {[1, 2, 5, 10, 20].map((r) => (
              <option key={r} value={r}>{r} km</option>
            ))}
          </select>
        </div>
      </div>

      {/* ── Category chips ── */}
      <div className="flex gap-2 px-4 py-2.5 border-b border-edge overflow-x-auto scrollbar-thin shrink-0">
        <CategoryChip
          label="All"
          active={!activeCategory}
          onClick={() => onCategoryChange(null)}
        />
        {categories.map((cat) => (
          <CategoryChip
            key={cat.id}
            label={`${cat.icon} ${cat.name}`}
            active={activeCategory === cat.name}
            onClick={() => onCategoryChange(activeCategory === cat.name ? null : cat.name)}
          />
        ))}
      </div>

      {/* ── Result count bar ── */}
      <div className="flex items-center justify-between px-4 py-2 bg-surface border-b border-edge shrink-0">
        <span className="text-xs text-ink-faint">
          {loading ? (
            'Searching…'
          ) : (
            <><strong className="text-ink-muted">{restaurants.length}</strong> result{restaurants.length !== 1 ? 's' : ''}</>
          )}
        </span>
        <span className="text-[10px] font-mono text-ink-faint bg-white border border-edge px-2 py-0.5 rounded">
          distance_lte
        </span>
      </div>

      {/* ── Restaurant list ── */}
      <div className="flex-1 overflow-y-auto scrollbar-thin">
        {loading ? (
          <LoadingDots />
        ) : restaurants.length === 0 ? (
          <EmptyState />
        ) : (
          <ul className="divide-y divide-edge">
            {restaurants.map((r) => (
              <RestaurantCard
                key={r.id}
                restaurant={r}
                isSelected={selectedRestaurant?.id === r.id}
                onClick={() => onRestaurantClick(r)}
              />
            ))}
          </ul>
        )}
      </div>
    </aside>
  );
}

/* ── Category chip ── */
function CategoryChip({ label, active, onClick }: { label: string; active: boolean; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className={[
        'px-3 py-1 rounded-full text-xs font-medium whitespace-nowrap shrink-0 border transition-all duration-150 cursor-pointer outline-none',
        active
          ? 'bg-brand text-white border-brand'
          : 'bg-white text-ink-muted border-edge hover:border-brand hover:text-brand',
      ].join(' ')}
    >
      {label}
    </button>
  );
}

/* ── Restaurant card ── */
const PRICE: Record<number, string> = { 1: 'تومان', 2: 'تومان', 3: 'تومان' };
const FALLBACK = 'https://images.unsplash.com/photo-1567364816519-cbc9c4ffe5fb?w=120';

function RestaurantCard({ restaurant, isSelected, onClick }: RestaurantCardProps) {
  const price = PRICE[restaurant.price_range] ?? 'تومان';

  return (
    <li
      onClick={onClick}
      className={[
        'flex gap-3 px-4 py-3.5 cursor-pointer transition-colors duration-100',
        isSelected ? 'bg-brand-soft' : 'hover:bg-surface',
      ].join(' ')}
    >
      {/* Thumbnail */}
      <img 
        src={restaurant.image_url || 'https://via.placeholder.com/150'} 
        alt={restaurant.name}
        className="w-14 h-14 rounded-lg object-cover bg-surface shrink-0 border border-edge"
        onError={(e) => {
          (e.target as HTMLImageElement).onerror = null; 
          (e.target as HTMLImageElement).src = 'https://via.placeholder.com/150';
        }} 
      />

      {/* Info */}
      <div className="flex-1 min-w-0">
        <p className="font-semibold text-sm text-ink truncate leading-snug mb-1" style={{ fontFamily: 'Syne, sans-serif' }}>
          {restaurant.name}
        </p>

        {/* Badges */}
        <div className="flex items-center flex-wrap gap-1 mb-1.5">
          <Badge color="amber">⭐ {restaurant.rating}</Badge>
          <Badge color={restaurant.is_open ? 'green' : 'gray'}>
            {restaurant.is_open ? 'Open' : 'Closed'}
          </Badge>
          {restaurant.distance_km != null && (
            <Badge color="blue">📍 {restaurant.distance_km} km</Badge>
          )}
          <Badge color="gray">{price}</Badge>
        </div>

        {/* Footer */}
        <p className="text-xs text-ink-faint">
          🕐 {restaurant.delivery_time_min} min &nbsp;·&nbsp; ₦{restaurant.delivery_fee} delivery
          {restaurant.category_icon && (
            <> &nbsp;·&nbsp; {restaurant.category_icon} {restaurant.category_name}</>
          )}
        </p>
      </div>
    </li>
  );
}

/* ── Badge ── */
type BadgeColor = 'amber' | 'green' | 'gray' | 'blue';

const BADGE_CLASSES: Record<BadgeColor, string> = {
  amber: 'bg-amber-50 text-amber-600',
  green: 'bg-emerald-50 text-emerald-600',
  gray:  'bg-surface text-ink-muted border border-edge',
  blue:  'bg-blue-50 text-blue-600',
};

function Badge({ color, children }: { color: BadgeColor; children: React.ReactNode }) {
  return (
    <span className={`inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded text-[11px] font-medium ${BADGE_CLASSES[color]}`}>
      {children}
    </span>
  );
}

/* ── Loading dots ── */
function LoadingDots() {
  return (
    <div className="flex items-center justify-center gap-1.5 py-12">
      {[0, 1, 2].map((i) => (
        <div
          key={i}
          className="w-2 h-2 rounded-full bg-brand animate-pulse-dot"
          style={{ animationDelay: `${i * 0.18}s` }}
        />
      ))}
    </div>
  );
}

/* ── Empty state ── */
function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-6 text-center gap-3">
      <div className="text-4xl">🔍</div>
      <p className="font-semibold text-sm text-ink-muted">No restaurants found</p>
      <p className="text-xs text-ink-faint leading-relaxed max-w-[200px]">
        Try increasing the radius or clicking a different spot on the map
      </p>
    </div>
  );
}