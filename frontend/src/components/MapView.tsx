import {
  useState, useEffect, useCallback, useRef, type ReactNode,
} from 'react';
import {
  MapContainer, TileLayer, Marker, Popup, Circle,
  GeoJSON, Polyline, useMap, useMapEvents,
} from 'react-leaflet';
import L, { type PathOptions } from 'leaflet';
import type { GeoJsonObject } from 'geojson';

import { fetchNearby, fetchRestaurant, fetchCategories, fetchZones, checkZone , fetchRoute} from '../api';
import type {
  Restaurant, RestaurantDetail, Category, DeliveryZone,
  LatLng, GeoJSONFeature, MapClickHandlerProps, MapControllerProps,
} from '../types';
import RestaurantSidebar from './RestaurantSidebar';
import DetailPanel from './DetailPanel';

// Fix Leaflet default icon in Vite
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl:       'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl:     'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

// ── Icons ──────────────────────────────────────────────────

const userIcon = L.divIcon({
  html: `<div style="width:16px;height:16px;background:#2563EB;border:2.5px solid #fff;border-radius:50%;box-shadow:0 0 0 4px rgba(37,99,235,0.2)"></div>`,
  className: '', iconSize: [16, 16], iconAnchor: [8, 8],
});

function makeRestaurantIcon(selected: boolean, open: boolean): L.DivIcon {
  const bg = selected ? '#E8420A' : open ? '#16A34A' : '#9E9B94';
  const size = selected ? 32 : 26;
  const half = size / 2;
  return L.divIcon({
    html: `<div style="width:${size}px;height:${size}px;background:${bg};border:2px solid #fff;border-radius:50%;box-shadow:0 2px 8px rgba(0,0,0,0.22);display:flex;align-items:center;justify-content:center;font-size:${selected ? 15 : 12}px;transition:all .15s">🍽️</div>`,
    className: '', iconSize: [size, size], iconAnchor: [half, half],
  });
}

// ── Constants ──────────────────────────────────────────────

const DEFAULT_CENTER: LatLng = { lat: 36.27, lng: 50.00 };
const DEFAULT_RADIUS = 5;

// ── Inner map components ───────────────────────────────────

function MapClickHandler({ onMapClick }: MapClickHandlerProps): null {
  useMapEvents({ click: (e) => onMapClick({ lat: e.latlng.lat, lng: e.latlng.lng }) });
  return null;
}

function MapController({ userLocation }: MapControllerProps): null {
  const map = useMap();
  const prevLoc = useRef<LatLng | null>(null);

  useEffect(() => {
    if (
      userLocation &&
      (!prevLoc.current ||
        prevLoc.current.lat !== userLocation.lat ||
        prevLoc.current.lng !== userLocation.lng)
    ) {
      prevLoc.current = userLocation;
      map.flyTo([userLocation.lat, userLocation.lng], 13, { duration: 1 });
    }
  }, [userLocation, map]);
  return null;
}

const zoneStyle = (): PathOptions => ({ fillColor: '#E8420A', fillOpacity: 0.07, color: '#E8420A', weight: 1.5, dashArray: '5,4' });
const activeZoneStyle = (): PathOptions => ({ fillColor: '#2563EB', fillOpacity: 0.03, stroke: false});

// ── MapView ────────────────────────────────────────────────

export default function MapView(): ReactNode {
  const [userLocation, setUserLocation]       = useState<LatLng>(DEFAULT_CENTER);
  const [restaurants,  setRestaurants]         = useState<Restaurant[]>([]);
  const [selected,     setSelected]            = useState<Restaurant | null>(null);
  const [detail,       setDetail]              = useState<RestaurantDetail | null>(null);
  const [zones,        setZones]               = useState<DeliveryZone[]>([]);
  const [userZones,    setUserZones]           = useState<GeoJSONFeature[]>([]);
  const [categories,   setCategories]          = useState<Category[]>([]);
  const [activeCategory, setActiveCategory]    = useState<string | null>(null);
  const [radius,       setRadius]              = useState<number>(DEFAULT_RADIUS);
  const [searchTerm,   setSearchTerm]          = useState<string>('');
  const [loading,      setLoading]             = useState<boolean>(false);
  const [showZones,    setShowZones]           = useState<boolean>(false);
  const [showRadius,   setShowRadius]          = useState<boolean>(true);
  const searchTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [routeData, setRouteData] = useState<RouteResponse | null>(null);
  // Auto detect location safely on mount
  useEffect(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          const newLat = Number(pos.coords.latitude.toFixed(6));
          const newLng = Number(pos.coords.longitude.toFixed(6));
          setUserLocation({ lat: newLat, lng: newLng });
        },
        (error) => {
          console.warn('Geolocation failed or denied:', error);
        },
        { timeout: 10000, maximumAge: 60000 }
      );
    }
  }, []);

  useEffect(() => { fetchCategories().then(setCategories).catch(console.error); }, []);
  useEffect(() => { 
    if (showZones) {

    fetchZones().then(setZones).catch(console.error);
  } else {
    setZones([]);
  }
  }, [showZones]);
    
  useEffect(() => {
    let isMounted = true;
    setLoading(true);

    fetchNearby({ lat: userLocation.lat, lng: userLocation.lng, radius, category: activeCategory })
      .then((data) => {
        if (!isMounted) return;
        const filtered = searchTerm ? data.filter(r => r.name?.toLowerCase().includes(searchTerm.toLowerCase())) : data;
        setRestaurants(filtered);
      })
      .catch(console.error)
      .finally(() => { if (isMounted) setLoading(false); });

    checkZone({ lat: userLocation.lat, lng: userLocation.lng })
      .then(r => {
        if (!isMounted) return;
        setUserZones((r.rawZones?.features as GeoJSONFeature[] | undefined) ?? []);
      })
      .catch(console.error);

    return () => { isMounted = false; };
  }, [userLocation.lat, userLocation.lng, radius, activeCategory]); // دقت: مقادیر دکانستراکت شده برای جلوگیری از چرخه نهایی

  useEffect(() => {
    if (searchTimer.current) clearTimeout(searchTimer.current);
    searchTimer.current = setTimeout(() => {
      fetchNearby({ lat: userLocation.lat, lng: userLocation.lng, radius, category: activeCategory })
        .then(data => {
          const filtered = searchTerm ? data.filter(r => r.name?.toLowerCase().includes(searchTerm.toLowerCase())) : data;
          setRestaurants(filtered);
        });
    }, 300);
  }, [searchTerm]);

  useEffect(() => {
    if (!selected) { setDetail(null); return; }
    fetchRestaurant(selected.id).then(setDetail).catch(console.error);
  }, [selected]);

  useEffect(() => {
    if (!selected || !userLocation) {
      setRouteData(null);
      return;
    }
    fetchRoute(selected.id, userLocation.lat, userLocation.lng)
      .then(setRouteData)
      .catch(console.error);
  }, [selected, userLocation.lat, userLocation.lng]);

  const handleMapClick = useCallback((latlng: LatLng) => {
    setUserLocation({
      lat: Number(latlng.lat.toFixed(6)),
      lng: Number(latlng.lng.toFixed(6)),
    });
    setSelected(null);
    setDetail(null);
    setRouteData(null);
  }, []);

  const handleRestaurantClick = useCallback((r: Restaurant) => {
    setSelected(prev => prev?.id === r.id ? null : r);
  }, []);

  const handleLocateMe = useCallback(() => {
    if (!navigator.geolocation) {
      alert('Geolocation is not supported by your browser');
      return;
    }
    navigator.geolocation.getCurrentPosition(
      pos => {
        setUserLocation({
          lat: Number(pos.coords.latitude.toFixed(6)),
          lng: Number(pos.coords.longitude.toFixed(6)),
        });
      },
      (err) => alert(`Could not get location: ${err.message}`),
      { enableHighAccuracy: true, timeout: 5000 }
    );
  }, []);

  return (
    <div className="flex flex-1 overflow-hidden">
      <RestaurantSidebar
        restaurants={restaurants} loading={loading} categories={categories}
        activeCategory={activeCategory} onCategoryChange={setActiveCategory}
        radius={radius} onRadiusChange={setRadius}
        searchTerm={searchTerm} onSearchChange={setSearchTerm}
        selectedRestaurant={selected} onRestaurantClick={handleRestaurantClick}
        userLocation={userLocation}
      />

      {/* ── Map area ── */}
      <div className="relative flex-1 overflow-hidden">
        <MapContainer
          center={[DEFAULT_CENTER.lat, DEFAULT_CENTER.lng]} zoom={13}
          style={{ width: '100%', height: '100%' }}
          zoomControl={false}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          <MapClickHandler onMapClick={handleMapClick} />
          <MapController userLocation={userLocation} />

          {/* User pin */}
          <Marker position={[userLocation.lat, userLocation.lng]} icon={userIcon}>
            <Popup>
              <div className="p-3">
                <p className="font-semibold text-sm text-ink">📍 Your Location</p>
                <p className="text-xs text-ink-muted mt-1">{userLocation.lat.toFixed(4)}, {userLocation.lng.toFixed(4)}</p>
                <p className="text-[11px] text-ink-faint mt-1">Click anywhere to move</p>
              </div>
            </Popup>
          </Marker>

          {showRadius && (
            <Circle
              center={[userLocation.lat, userLocation.lng]}
              radius={radius * 1000}
              pathOptions={{ color: '#2563EB', fillColor: '#2563EB', fillOpacity: 0.04, weight: 1.5, dashArray: '6,4' }}
            />
          )}  


          {routeData?.route_geometry?.coordinates && (
            <Polyline
              positions={routeData.route_geometry.coordinates.map(
                (coord) => [coord[1], coord[0]] 
              )}
              pathOptions={{
                color: '#8B5CF6',   
                weight: 5,           
                opacity: 0.85,
                lineCap: 'round',
                lineJoin: 'round',
              }}
            />
          )}

          {/* Delivery zone polygons */}
          {showZones && zones.map(zone => (
            <GeoJSON
              key={`zone-${zone.id}`}
              data={{ type: 'Feature', geometry: zone.geometry, properties: zone } as unknown as GeoJsonObject}
              style={zoneStyle}
              onEachFeature={(feature, layer) => {
                const p = feature.properties as DeliveryZone;
                layer.bindTooltip(`<b>${p.name}</b><br/>${p.restaurant_name ?? ''}<br/>${p.delivery_fee} delivery`, { sticky: true });
              }}
            />
          ))}

          {/* User active zones */}
          {showZones && userZones.map((f, i) => (
            <GeoJSON key={`uz-${f.id ?? i}`} data={f as unknown as GeoJsonObject} style={activeZoneStyle} />
          ))}

          {/* Restaurant markers */}
          {restaurants.map(r => (
            <Marker
              key={r.id}
              position={[r.lat, r.lng]}
              icon={makeRestaurantIcon(selected?.id === r.id, r.is_open)}
              eventHandlers={{ click: () => handleRestaurantClick(r) }}
            >
              <Popup>
                <div className="p-3 min-w-[180px]">
                  <p className="font-bold text-sm text-ink mb-2 leading-snug">{r.name}</p>
                  {selected?.id === r.id && routeData && (
                    <div className="bg-purple-50 text-purple-700 p-2 rounded-lg text-xs mb-2 border border-purple-200">
                      <p className="font-semibold">🛣️ مسیریابی خیابانی:</p>
                      <p>مسافت: <strong>{routeData.distance_km} کیلومتر</strong></p>
                      <p>زمان تخمینی: <strong>{routeData.duration_minutes} دقیقه</strong></p>
                    </div>
                  )}
                  <div className="flex gap-1.5 flex-wrap mb-2">
                    <span className="text-[11px] bg-amber-50 text-amber-600 px-1.5 py-0.5 rounded">⭐ {r.rating}</span>
                    {r.distance_km != null && (
                      <span className="text-[11px] bg-blue-50 text-blue-600 px-1.5 py-0.5 rounded">📍 {r.distance_km} km</span>
                    )}
                  </div>
                  <p className="text-xs text-ink-muted mb-2.5">🕐 {r.delivery_time_min} min · {r.delivery_fee} delivery</p>
                  <button
                    onClick={() => handleRestaurantClick(r)}
                    className="w-full py-1.5 bg-brand text-white text-xs font-semibold rounded-lg cursor-pointer border-0 hover:opacity-90 transition-opacity"
                  >
                    View Menu
                  </button>
                </div>
              </Popup>
            </Marker>
          ))}
        </MapContainer>

        {/* ── Map overlay controls ── */}
        <div className="absolute top-4 right-4 z-[1000] flex flex-col gap-2">
          <MapButton onClick={handleLocateMe}>🎯 Locate Me</MapButton>
          <MapButton active={showRadius} onClick={() => setShowRadius(p => !p)}>⭕ Radius</MapButton>
          <MapButton active={showZones} onClick={() => setShowZones(p => !p)}>🗺️ Zones</MapButton>

          {/* Legend */}
          <div className="bg-white border border-edge rounded-xl px-3 py-2.5 shadow-card text-xs space-y-1.5 mt-1">
            {[
              { color: '#2563EB', label: 'Your location' },
              { color: '#16A34A', label: 'Open' },
              { color: '#9E9B94', label: 'Closed' },
            ].map(({ color, label }) => (
              <div key={label} className="flex items-center gap-2 text-ink-faint">
                <div className="w-2 h-2 rounded-full shrink-0" style={{ background: color }} />
                {label}
              </div>
            ))}
            <div className="flex items-center gap-2 text-ink-faint">
              <div className="w-3 h-0.5 shrink-0 rounded" style={{ background: '#E8420A' }} />
              Delivery zone
            </div>
          </div>
        </div>

        {/* Zone indicator badge */}
        {showZones && userZones.length > 0 && (
          <div className="absolute top-4 left-4 z-[1000] bg-white border border-edge rounded-xl px-3.5 py-3 shadow-card max-w-[220px]">
            <p className="text-[10px] font-semibold uppercase tracking-widest text-ink-faint mb-1.5">
              📦 In a delivery zone
            </p>
            {userZones.map((f, i) => (
              <p key={i} className="text-xs font-medium text-emerald-600">
                ✓ {(f.properties as { name?: string })?.name ?? `Zone ${i + 1}`}
              </p>
            ))}
          </div>
        )}

        {/* Detail panel */}
        {detail && (
          <DetailPanel
            restaurant={detail}
            onClose={() => { setSelected(null); setDetail(null); }}
          />
        )}
      </div>
    </div>
  );
}

function MapButton({ children, onClick, active = false }: {
  children: React.ReactNode;
  onClick: () => void;
  active?: boolean;
}) {
  return (
    <button
      onClick={onClick}
      className={[
        'flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-medium shadow-card border cursor-pointer transition-all duration-150',
        active
          ? 'bg-brand text-white border-brand'
          : 'bg-white text-ink border-edge hover:border-brand hover:text-brand',
      ].join(' ')}
    >
      {children}
    </button>
  );
}