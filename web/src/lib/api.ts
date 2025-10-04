import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000/api';

export interface EventSummary { id: string; title: string; year: number; lat: number; lon: number; category: string; }

export async function fetchEvents(params: {year?: number, category?: string} = {}): Promise<EventSummary[]> {
  const resp = await axios.get(`${API_BASE}/events`, { params });
  return resp.data;
}

export async function fetchEvent(id: string) {
  const resp = await axios.get(`${API_BASE}/events/${id}`);
  return resp.data;
}

export async function fetchSummary() {
  const resp = await axios.get(`${API_BASE}/stats/summary`);
  return resp.data;
}
