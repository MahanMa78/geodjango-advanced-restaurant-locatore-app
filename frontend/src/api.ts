/**
 * api.ts — Typed API service layer
 *
 * All calls go to the GeoDjango backend.
 * The backend returns GeoJSON (FeatureCollection or Feature objects).
 *
 * GeoJSON structure reminder:
 *   FeatureCollection → { type, features: [Feature, ...] }
 *   Feature           → { type, id, geometry, properties }
 *   geometry          → { type: "Point", coordinates: [lng, lat] }
 *
 * NOTE: GeoJSON coordinates are [longitude, latitude] (x, y).
 * Leaflet uses [latitude, longitude]. Remember to swap when passing to Leaflet!
 */

import axios from 'axios';
import type {
  Restaurant,
  RestaurantDetail,
  Category,
  DeliveryZone,
  GeoJSONFeatureCollection,
  GeoJSONFeature,
  NearbyParams,
  BboxParams,
  RouteResponse,
  ReverseGeocodeResponse,
  AuthTokens,
  User,
  UserAddress,
  OrderCreatePayload,
  OrderResponse,
} from './types';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api',
  headers: { 'Content-Type': 'application/json' },
});

// ─── JWT Interceptor ─────────────────────────────────────────────────────────

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ─── GeoJSON parsers ──────────────────────────────────────────────────────────

/**
 * Parse a GeoJSON FeatureCollection of restaurants into flat Restaurant objects.
 * Extracts coordinates from geometry so components don't need to touch GeoJSON directly.
 */
function parseRestaurantCollection(
  geojson: GeoJSONFeatureCollection
): Restaurant[] {
  if (!geojson?.features) return [];

  return geojson.features.map((feature: GeoJSONFeature) => {
    const coords = feature.geometry?.coordinates as number[] | undefined;
    return {
      id: feature.id as number,
      ...(feature.properties as Omit<Restaurant, 'id' | 'lat' | 'lng' | 'geometry'>),
      // GeoJSON Point: coordinates = [longitude, latitude]
      lng: coords?.[0] ?? 0,
      lat: coords?.[1] ?? 0,
      geometry: feature.geometry,
    } as Restaurant;
  });
}

/**
 * Parse a GeoJSON FeatureCollection of zones into flat DeliveryZone objects.
 */
function parseZoneCollection(geojson: GeoJSONFeatureCollection): DeliveryZone[] {
  if (!geojson?.features) return [];

  return geojson.features.map((feature: GeoJSONFeature) => ({
    id: feature.id as number,
    ...(feature.properties as Omit<DeliveryZone, 'id' | 'geometry'>),
    geometry: feature.geometry,
  })) as DeliveryZone[];
}

// ─── Authentication endpoints ────────────────────────────────────────────────

export async function sendOtpApi(phoneNumber: string): Promise<{ message: string; dev_code?: string }> {
  const res = await api.post('/accounts/send-otp/', { phone_number: phoneNumber });
  return res.data;
}

export async function verifyOtpApi(
  phoneNumber: string,
  code: string
): Promise<{ message: string; is_new_user: boolean; tokens: AuthTokens; user: User }> {
  const res = await api.post('/accounts/verify-otp/', { phone_number: phoneNumber, code });
  return res.data;
}

export async function fetchUserProfile(): Promise<User> {
  const res = await api.get<User>('/accounts/profile/');
  return res.data;
}

// ─── User Address endpoints ──────────────────────────────────────────────────

export async function fetchUserAddresses(): Promise<UserAddress[]> {
  const res = await api.get<UserAddress[] | { results: UserAddress[] }>('/accounts/addresses/');
  const data = res.data;
  return Array.isArray(data) ? data : (data as { results: UserAddress[] }).results ?? [];
}

export async function saveUserAddress(payload: {
  title: string;
  address_text: string;
  lat: number;
  lng: number;
}): Promise<UserAddress> {
  const res = await api.post<UserAddress>('/accounts/addresses/', payload);
  return res.data;
}

// ─── Restaurant endpoints ─────────────────────────────────────────────────────

/**
 * GET /api/restaurants/
 * Returns all restaurants as a GeoJSON FeatureCollection.
 */
export async function fetchRestaurants(
  params: Record<string, string | number | boolean> = {}
): Promise<Restaurant[]> {
  const res = await api.get<GeoJSONFeatureCollection>('/restaurants/', { params });
  return parseRestaurantCollection(res.data);
}

/**
 * GET /api/restaurants/nearby/?lat=&lng=&radius=
 *
 * GeoDjango spatial query: location__distance_lte=(point, D(km=radius))
 * Returns restaurants sorted by distance, with distance_km in properties.
 */
export async function fetchNearby({
  lat,
  lng,
  radius = 5,
  category,
}: NearbyParams): Promise<Restaurant[]> {
  const params: Record<string, string | number> = { lat, lng, radius };
  if (category) params.category = category;

  const res = await api.get<GeoJSONFeatureCollection>('/restaurants/nearby/', { params });
  return parseRestaurantCollection(res.data);
}

/**
 * GET /api/restaurants/:id/
 * Returns a single restaurant as a GeoJSON Feature (with menu_items in properties).
 */
export async function fetchRestaurant(id: number): Promise<RestaurantDetail> {
  const res = await api.get<GeoJSONFeature>(`/restaurants/${id}/`);
  const feature = res.data;
  const coords = feature.geometry?.coordinates as number[] | undefined;

  return {
    id: feature.id as number,
    ...(feature.properties as Omit<RestaurantDetail, 'id' | 'lat' | 'lng' | 'geometry'>),
    lng: coords?.[0] ?? 0,
    lat: coords?.[1] ?? 0,
    geometry: feature.geometry,
  } as RestaurantDetail;
}

/**
 * GET /api/restaurants/bbox/?min_lat=&max_lat=&min_lng=&max_lng=
 * GeoDjango: location__within=bbox polygon
 */
export async function fetchInBbox({
  minLat,
  maxLat,
  minLng,
  maxLng,
}: BboxParams): Promise<Restaurant[]> {
  const res = await api.get<GeoJSONFeatureCollection>('/restaurants/bbox/', {
    params: { min_lat: minLat, max_lat: maxLat, min_lng: minLng, max_lng: maxLng },
  });
  return parseRestaurantCollection(res.data);
}

// ─── Routing & Geocoding endpoints ───────────────────────────────────────────

/**
 * GET /api/restaurants/:id/route/?user_lat=&user_lng=
 * Fetches real OSRM road route geometry between user and restaurant.
 */
export async function fetchRoute(
  restaurantId: number,
  userLat: number,
  userLng: number
): Promise<RouteResponse> {
  const res = await api.get<RouteResponse>(`/restaurants/${restaurantId}/route/`, {
    params: { user_lat: userLat, user_lng: userLng },
  });
  return res.data;
}

export async function fetchReverseGeocode(lat: number, lng: number): Promise<ReverseGeocodeResponse> {
  const res = await api.get<ReverseGeocodeResponse>('/geocoding/reverse/', {
    params: { lat, lng },
  });
  return res.data;
}

// ─── Category endpoints ───────────────────────────────────────────────────────

export async function fetchCategories(): Promise<Category[]> {
  const res = await api.get<{ results?: Category[] } | Category[]>('/categories/');
  const data = res.data;
  return Array.isArray(data) ? data : (data as { results?: Category[] }).results ?? [];
}

// ─── Delivery zone endpoints ──────────────────────────────────────────────────

/**
 * GET /api/zones/
 * Returns all delivery zones as GeoJSON FeatureCollection (polygons).
 */
export async function fetchZones(restaurantId?: number): Promise<DeliveryZone[]> {
  const params = restaurantId ? { restaurant: restaurantId } : {};
  const res = await api.get<GeoJSONFeatureCollection>('/zones/', { params });
  return parseZoneCollection(res.data);
}

export interface CheckZoneResult {
  zonesFound: number;
  zones: DeliveryZone[];
  rawZones: GeoJSONFeatureCollection | null;
}

/**
 * GET /api/zones/check/?lat=&lng=
 * GeoDjango: area__contains=user_point
 * Checks which delivery zones contain the user's location.
 */
export async function checkZone({
  lat,
  lng,
}: {
  lat: number;
  lng: number;
}): Promise<CheckZoneResult> {
  const res = await api.get<{
    zones_found: number;
    zones: GeoJSONFeatureCollection;
  }>('/zones/check/', { params: { lat, lng } });

  return {
    zonesFound: res.data.zones_found,
    zones: parseZoneCollection(res.data.zones ?? { type: 'FeatureCollection', features: [] }),
    rawZones: res.data.zones ?? null,
  };
}

// ─── Order & Dispatch endpoints ──────────────────────────────────────────────

export async function createOrder(payload: OrderCreatePayload): Promise<OrderResponse> {
  const res = await api.post<OrderResponse>('/orders/create/', payload);
  return res.data;
}

export async function fetchMyOrders(): Promise<OrderResponse[]> {
  const res = await api.get<OrderResponse[]>('/orders/my-orders/');
  return res.data;
}

export default api;