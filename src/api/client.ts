import { AnalysisParams, AnalysisResponse, HazardEvent, RegionPreset } from '../types';

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || '/api/v1').replace(/\/$/, '');

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number = 500) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

export async function fetchHealth(): Promise<{ status: string; database_connected: boolean; version: string; supported_hazards: string[] }> {
  const res = await fetch(`${API_BASE_URL}/health`);
  if (!res.ok) {
    throw new ApiError(`Health check failed (${res.status})`, res.status);
  }
  return res.json();
}

export async function fetchRegions(): Promise<RegionPreset[]> {
  const res = await fetch(`${API_BASE_URL}/regions`);
  if (!res.ok) {
    throw new ApiError(`Failed to fetch region presets (${res.status})`, res.status);
  }
  return res.json();
}

export async function searchRegions(query: string): Promise<RegionPreset[]> {
  if (!query || query.trim().length < 2) return [];
  const res = await fetch(`${API_BASE_URL}/regions/search?q=${encodeURIComponent(query.trim())}`);
  if (!res.ok) {
    throw new ApiError(`Region search failed (${res.status})`, res.status);
  }
  return res.json();
}

export async function fetchAnalysis(params: AnalysisParams): Promise<AnalysisResponse> {
  const search = new URLSearchParams({
    latitude: params.latitude.toString(),
    longitude: params.longitude.toString(),
    start_year: params.start_year.toString(),
    end_year: params.end_year.toString(),
    hazard: params.hazard,
    baseline_start: params.baseline_start.toString(),
    baseline_end: params.baseline_end.toString(),
    ...(params.force_refresh ? { force_refresh: 'true' } : {}),
  });

  const res = await fetch(`${API_BASE_URL}/analysis?${search.toString()}`);
  if (!res.ok) {
    let errorDetail = `Analysis request failed (${res.status})`;
    try {
      const errorJson = await res.json();
      if (errorJson.detail) {
        errorDetail = errorJson.detail;
      }
    } catch {
      // fallback
    }
    throw new ApiError(errorDetail, res.status);
  }
  return res.json();
}

export async function fetchEvents(params: AnalysisParams & { min_duration?: number }): Promise<HazardEvent[]> {
  const search = new URLSearchParams({
    latitude: params.latitude.toString(),
    longitude: params.longitude.toString(),
    start_year: params.start_year.toString(),
    end_year: params.end_year.toString(),
    hazard: params.hazard,
    baseline_start: params.baseline_start.toString(),
    baseline_end: params.baseline_end.toString(),
    ...(params.min_duration ? { min_duration: params.min_duration.toString() } : {}),
  });

  const res = await fetch(`${API_BASE_URL}/events?${search.toString()}`);
  if (!res.ok) {
    throw new ApiError(`Failed to fetch events (${res.status})`, res.status);
  }
  return res.json();
}

export async function refreshCache(params: AnalysisParams): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/cache/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      latitude: params.latitude,
      longitude: params.longitude,
      start_year: params.start_year,
      end_year: params.end_year,
      baseline_start: params.baseline_start,
      baseline_end: params.baseline_end,
      hazard: params.hazard,
    }),
  });

  if (!res.ok) {
    let detail = `Cache refresh failed (${res.status})`;
    try {
      const json = await res.json();
      if (json.detail) detail = json.detail;
    } catch {}
    throw new ApiError(detail, res.status);
  }
}
