import { useEffect, useState } from 'react';

import type { SearchFilters } from '@/types';

export interface AppLocation {
  pathname: string;
  search: string;
}

function readLocation(): AppLocation {
  return {
    pathname: window.location.pathname,
    search: window.location.search,
  };
}

function notifyNavigation(): void {
  window.dispatchEvent(new Event('app:navigate'));
}

export function navigate(to: string, options?: { replace?: boolean }): void {
  if (options?.replace) {
    window.history.replaceState(null, '', to);
  } else {
    window.history.pushState(null, '', to);
  }
  notifyNavigation();
}

export function useAppLocation(): AppLocation {
  const [location, setLocation] = useState<AppLocation>(() => readLocation());

  useEffect(() => {
    const onChange = () => setLocation(readLocation());
    window.addEventListener('popstate', onChange);
    window.addEventListener('app:navigate', onChange);
    return () => {
      window.removeEventListener('popstate', onChange);
      window.removeEventListener('app:navigate', onChange);
    };
  }, []);

  return location;
}

export function parseFilters(params: URLSearchParams): SearchFilters {
  return {
    title: params.get('title') !== 'false',
    abstract: params.get('abstract') !== 'false',
    keywords: params.get('keywords') !== 'false',
  };
}

export function applyFilters(params: URLSearchParams, filters: SearchFilters): URLSearchParams {
  params.set('title', String(filters.title));
  params.set('abstract', String(filters.abstract));
  params.set('keywords', String(filters.keywords));
  return params;
}

export function parsePage(value: string | null): number {
  if (!value) {
    return 1;
  }

  const parsed = Number.parseInt(value, 10);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : 1;
}

export function buildQueryString(params: URLSearchParams): string {
  const query = params.toString();
  return query ? `?${query}` : '';
}

export function getLegacyRedirect(pathname: string, search: string): string | null {
  if (pathname !== '/') {
    return null;
  }

  const params = new URLSearchParams(search);
  const paperId = params.get('id');
  if (paperId) {
    return `/papers/${paperId}`;
  }

  const conference = params.get('conference');
  if (conference) {
    return `/conference/${conference}`;
  }

  const keyword = params.get('search');
  if (keyword) {
    const next = new URLSearchParams();
    next.set('q', keyword);
    next.set('title', params.get('title') ?? 'true');
    next.set('abstract', params.get('abstract') ?? 'true');
    next.set('keywords', params.get('keywords') ?? 'true');
    return `/search${buildQueryString(next)}`;
  }

  return null;
}
