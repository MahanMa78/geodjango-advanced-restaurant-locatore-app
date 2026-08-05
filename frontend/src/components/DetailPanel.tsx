import type { DetailPanelProps, MenuItem } from '../types';
import { useState } from 'react';
import { createOrder } from '../api';

const PRICE: Record<number, string> = { 1: 'تومان', 2: 'تومان', 3: 'تومان' };
const FALLBACK = 'https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=300';

interface ExtendedDetailPanelProps extends DetailPanelProps {
  userLocation?: { lat: number; lng: number } | null;
  userAddress?: string;
  onOrderCreated?: (orderId: number) => void;
}

export default function DetailPanel({ 
  restaurant,
  onClose,
  routeData,
  userLocation, 
  userAddress, 
  onOrderCreated 
}: ExtendedDetailPanelProps) {
  const [loading, setLoading] = useState(false);

  const handleOrder = async () => {
    if (!userLocation?.lat || !userLocation?.lng) {
      alert('لطفاً موقعیت خود را روی نقشه انتخاب کنید.');
      return;
    }

    setLoading(true);
    try {
      const response = await createOrder({
        restaurant_id: restaurant.id,
        lat: userLocation.lat,
        lng: userLocation.lng,
        address: userAddress || '',
        total_amount: 100000,
        delivery_fee: routeData?.pricing?.final_fee || Number(restaurant.delivery_fee) || 15000,
      });

      if (response.success && onOrderCreated) {
        onOrderCreated(response.order_id);
        onClose(); // 🚀 بسته شدن پنل جهت جلوگیری از کرش UI و تداخل State
      }
    } catch (err) {
      console.error('Failed to create order:', err);
      alert('خطا در ثبت سفارش. لطفاً دوباره تلاش کنید.');
    } finally {
      setLoading(false);
    }
  };  

  const price = PRICE[restaurant.price_range] ?? 'تومان';

  const deliveryFee = routeData?.pricing?.final_fee
    ? `${routeData.pricing.final_fee.toLocaleString()} تومان`
    : `${Number(restaurant.delivery_fee).toLocaleString()} تومان`;

  const deliveryTime = routeData?.duration_minutes
    ? `${routeData.duration_minutes} min`
    : `${restaurant.delivery_time_min} min`;

  const menuByCategory = (restaurant.menu_items ?? []).reduce<Record<string, MenuItem[]>>(
    (acc, item) => {
      const cat = item.category ?? 'Other';
      acc[cat] = acc[cat] ? [...acc[cat], item] : [item];
      return acc;
    },
    {}
  );

  return (
    <div className="absolute inset-0 z-[1000] flex flex-col justify-end pointer-events-none">
      <div
        className="bg-white rounded-t-2xl shadow-lift pointer-events-auto max-h-[62vh] flex flex-col animate-slide-up"
        style={{ borderTop: '1px solid #ECEAE4' }}
      >
        <div className="flex justify-center pt-3 pb-1 cursor-pointer shrink-0" onClick={onClose}>
          <div className="w-10 h-1 rounded-full bg-edge-dark" />
        </div>

        <div className="overflow-y-auto scrollbar-thin px-5 pb-6">
          <div className="flex gap-4 items-start mb-4">
            <img
              src={restaurant.image_url || FALLBACK}
              alt={restaurant.name}
              onError={(e) => { 
                const target = e.currentTarget as HTMLImageElement;
                if (target.src !== FALLBACK) {
                  target.src = FALLBACK;
                }
              }}
              className="w-20 h-20 rounded-xl object-cover shrink-0 bg-edge"
            />
            <div className="flex-1 min-w-0 pt-0.5">
              <h2
                className="text-xl font-bold text-ink leading-tight mb-1"
                style={{ fontFamily: 'Syne, sans-serif' }}
              >
                {restaurant.name}
              </h2>
              <p className="text-xs text-ink-muted mb-2 leading-snug">📍 {restaurant.address}</p>
              <div className="flex items-center gap-1.5 flex-wrap">
                <StatusBadge open={restaurant.is_open} />
                <span className="text-xs bg-amber-50 text-amber-600 px-2 py-0.5 rounded font-medium">
                  ⭐ {restaurant.rating}
                </span>
                <span className="text-xs bg-surface text-ink-muted border border-edge px-2 py-0.5 rounded font-medium">
                  {price}
                </span>
              </div>
            </div>
            <button
              onClick={onClose}
              className="w-7 h-7 rounded-full bg-surface border border-edge flex items-center justify-center text-ink-muted text-base hover:bg-edge transition-colors cursor-pointer shrink-0 mt-0.5"
            >
              ×
            </button>
          </div>

          <div className="grid grid-cols-3 gap-2 mb-4">
            {[
              { label: 'Delivery time', value: deliveryTime, accent: true },
              { label: 'Delivery fee', value: deliveryFee, accent: true },
              { label: 'Min. order', value: `${Number(restaurant.minimum_order).toLocaleString()} تومان`, accent: false },
            ].map((s) => (
              <div key={s.label} className="bg-surface rounded-xl p-3 text-center border border-edge">
                <p className="text-[10px] text-ink-faint uppercase tracking-wide mb-1">{s.label}</p>
                <p className={`font-bold text-base leading-none ${s.accent ? 'text-brand' : 'text-ink'}`} style={{ fontFamily: 'Syne, sans-serif' }}>
                  {s.value}
                </p>
              </div>
            ))}
          </div>

          <div className="rounded-xl px-4 py-3 mb-5 border" style={{ background: '#F8F7FF', borderColor: '#E0DEFF' }}>
            <p className="text-[11px] font-semibold mb-1.5" style={{ color: '#5B4FBE' }}>
              🌍 GeoDjango PointField
            </p>
            <code className="text-[11px] leading-relaxed block" style={{ fontFamily: 'JetBrains Mono, monospace', color: '#7B6FD8' }}>
              Point(<strong>{restaurant.lng?.toFixed(4)}</strong>,{' '}
              <strong>{restaurant.lat?.toFixed(4)}</strong>, srid=4326)
              <br />
              <span style={{ color: '#A09BC4' }}>// [longitude, latitude] — WGS84</span>
            </code>
          </div>

          {Object.keys(menuByCategory).length > 0 ? (
            <>
              <h3 className="font-bold text-sm text-ink mb-3" style={{ fontFamily: 'Syne, sans-serif' }}>
                Menu
              </h3>
              <div className="flex flex-col gap-4">
                {Object.entries(menuByCategory).map(([cat, items]) => (
                  <div key={cat}>
                    <p className="text-[10px] font-semibold uppercase tracking-widest text-ink-faint mb-2">
                      {cat}
                    </p>
                    <div className="flex flex-col gap-1.5">
                      {items.map((item) => (
                        <div
                          key={item.id}
                          className="flex justify-between items-start gap-3 bg-surface rounded-xl px-3 py-2.5 border border-edge"
                        >
                          <div className="min-w-0">
                            <p className="text-sm font-medium text-ink leading-snug">{item.name}</p>
                            {item.description && (
                              <p className="text-xs text-ink-faint mt-0.5 leading-snug line-clamp-2">
                                {item.description}
                              </p>
                            )}
                          </div>
                          <p className="text-sm font-bold text-brand shrink-0" style={{ fontFamily: 'Syne, sans-serif' }}>
                            {Number(item.price).toLocaleString()} تومان
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <p className="text-xs text-ink-faint text-center py-4">No menu items available</p>
          )}

          <button
            onClick={handleOrder}
            disabled={loading}
            className="w-full mt-5 h-11 rounded-xl bg-brand text-white font-semibold text-sm hover:opacity-90 active:scale-[0.98] transition-all cursor-pointer border-0 disabled:opacity-50"
          >
            {loading ? 'در حال ثبت سفارش...' : 'Order Now 🛵'}
          </button>
        </div>
      </div>
    </div>
  );
}

function StatusBadge({ open }: { open: boolean }) {
  return (
    <span className={`text-xs px-2 py-0.5 rounded font-medium flex items-center gap-1 ${open ? 'bg-emerald-50 text-emerald-600' : 'bg-surface text-ink-muted border border-edge'}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${open ? 'bg-emerald-500' : 'bg-ink-faint'}`} />
      {open ? 'Open Now' : 'Closed'}
    </span>
  );
}