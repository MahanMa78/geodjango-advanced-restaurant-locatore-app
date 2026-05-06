/**
 * types.ts — Shared TypeScript interfaces
 *
 * These types mirror the GeoJSON structures returned by the GeoDjango backend,
 * as well as the parsed flat objects used throughout the React components.
 */

// ─── GeoJSON primitives ──────────────────────────────────────────────────────

export type GeoJSONGeometryType =
  | 'Point'
  | 'LineString'
  | 'Polygon'
  | 'MultiPoint'
  | 'MultiLineString'
  | 'MultiPolygon'
  | 'GeometryCollection';

export interface GeoJSONGeometry {
  type: GeoJSONGeometryType;
  /** For Point: [longitude, latitude]. For Polygon: [[[lng, lat], ...]] */
  coordinates: number[] | number[][] | number[][][];
}

export interface GeoJSONFeature<P = Record<string, unknown>> {
  type: 'Feature';
  id?: number | string;
  geometry: GeoJSONGeometry;
  properties: P;
}

export interface GeoJSONFeatureCollection<P = Record<string, unknown>> {
  type: 'FeatureCollection';
  features: GeoJSONFeature<P>[];
}

// ─── Domain models (parsed from GeoJSON features) ────────────────────────────

export interface Category {
  id: number;
  name: string;
  icon: string;
}

/**
 * Restaurant as returned by the list/nearby endpoints.
 * Coordinates are extracted from the GeoJSON geometry and added as flat fields.
 */
export interface Restaurant {
  id: number;
  name: string;
  description?: string;
  address: string;
  phone?: string;
  rating: string | number;
  price_range: 1 | 2 | 3;
  delivery_time_min: number;
  delivery_fee: string | number;
  minimum_order: string | number;
  is_open: boolean;
  is_featured: boolean;
  image_url?: string;
  category_name?: string;
  category_icon?: string;
  distance_km?: number | null;
  /** Extracted from GeoJSON geometry.coordinates[1] */
  lat: number;
  /** Extracted from GeoJSON geometry.coordinates[0] */
  lng: number;
  geometry: GeoJSONGeometry;
}

export interface MenuItem {
  id: number;
  name: string;
  description?: string;
  price: string | number;
  category: string;
  is_available: boolean;
  image_url?: string;
}

/**
 * Full restaurant detail (from the /restaurants/:id/ endpoint).
 * Includes nested menu_items and category.
 */
export interface RestaurantDetail extends Restaurant {
  menu_items: MenuItem[];
  category: Category | null;
  created_at: string;
}

/** Delivery zone parsed from GeoJSON (PolygonField on the backend) */
export interface DeliveryZone {
  id: number;
  name: string;
  restaurant: number;
  restaurant_name?: string;
  delivery_fee: string | number;
  min_order: string | number;
  estimated_time: number;
  is_active: boolean;
  area_sq_km?: number | null;
  geometry: GeoJSONGeometry;
}

// ─── API param types ─────────────────────────────────────────────────────────

export interface NearbyParams {
  lat: number;
  lng: number;
  radius?: number;
  category?: string | null;
}

export interface BboxParams {
  minLat: number;
  maxLat: number;
  minLng: number;
  maxLng: number;
}

export interface LatLng {
  lat: number;
  lng: number;
}

// ─── Component prop types ────────────────────────────────────────────────────

export interface RestaurantSidebarProps {
  restaurants: Restaurant[];
  loading: boolean;
  categories: Category[];
  activeCategory: string | null;
  onCategoryChange: (cat: string | null) => void;
  radius: number;
  onRadiusChange: (r: number) => void;
  searchTerm: string;
  onSearchChange: (s: string) => void;
  selectedRestaurant: Restaurant | null;
  onRestaurantClick: (r: Restaurant) => void;
  userLocation: LatLng | null;
}

export interface RestaurantCardProps {
  restaurant: Restaurant;
  isSelected: boolean;
  onClick: () => void;
}

export interface DetailPanelProps {
  restaurant: RestaurantDetail;
  onClose: () => void;
}

export interface MapClickHandlerProps {
  onMapClick: (latlng: LatLng) => void;
}

export interface MapControllerProps {
  userLocation: LatLng | null;
}

// ─── Concepts panel ──────────────────────────────────────────────────────────

export interface Concept {
  icon: string;
  color: string;
  title: string;
  subtitle: string;
  body: string;
  code: string;
  api: string | null;
}