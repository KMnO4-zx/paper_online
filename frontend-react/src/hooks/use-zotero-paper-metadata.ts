import { useEffect } from 'react';

import type { Paper } from '@/types';

const ZOTERO_META_ATTRIBUTE = 'data-paper-insight-zotero';
const ZOTERO_META_SELECTOR = `meta[${ZOTERO_META_ATTRIBUTE}="true"]`;

export interface ZoteroMetadataEntry {
  name: string;
  content: string;
}

interface BuildZoteroMetadataOptions {
  origin?: string;
}

function normalizeMetadataText(value: string | null | undefined): string | null {
  const normalized = value?.replace(/\s+/g, ' ').trim();
  return normalized || null;
}

function uniqueMetadataValues(values: Array<string | null | undefined>): string[] {
  const seen = new Set<string>();
  const uniqueValues: string[] = [];

  for (const value of values) {
    const normalized = normalizeMetadataText(value);
    if (!normalized || seen.has(normalized)) {
      continue;
    }
    seen.add(normalized);
    uniqueValues.push(normalized);
  }

  return uniqueValues;
}

function toAbsoluteUrl(value: string | null | undefined, origin: string | undefined): string | null {
  const normalized = normalizeMetadataText(value);
  if (!normalized) {
    return null;
  }

  try {
    return new URL(normalized, origin).href;
  } catch {
    return normalized.startsWith('http://') || normalized.startsWith('https://') ? normalized : null;
  }
}

function buildPaperUrl(paperId: string, origin: string | undefined): string | null {
  if (!origin) {
    return null;
  }

  return toAbsoluteUrl(`/papers/${encodeURIComponent(paperId)}`, origin);
}

function buildPaperPdfUrl(paper: Paper, origin: string | undefined): string | null {
  const explicitPdfUrl = paper.arxiv?.pdf_url ?? paper.pdf ?? paper.pdfUrl;
  if (explicitPdfUrl) {
    return toAbsoluteUrl(explicitPdfUrl, origin);
  }

  if (paper.id.startsWith('arxiv:')) {
    return null;
  }

  return toAbsoluteUrl(`https://openreview.net/pdf?id=${paper.id}`, origin);
}

function paperPublicationDate(paper: Paper): string | null {
  const arxivDate = paper.arxiv?.published_at ?? paper.arxiv?.updated_at;
  if (arxivDate) {
    return arxivDate.slice(0, 10);
  }

  const venueYear = paper.venue?.match(/\b(20\d{2})\b/)?.[1] ?? paper.conference?.match(/\b(20\d{2})\b/)?.[1];
  if (venueYear) {
    return venueYear;
  }

  return paper.created_at?.slice(0, 10) ?? null;
}

export function buildZoteroPaperMetadata(
  paper: Paper,
  options: BuildZoteroMetadataOptions = {},
): ZoteroMetadataEntry[] {
  const entries: ZoteroMetadataEntry[] = [];
  const origin = options.origin ?? (typeof window !== 'undefined' ? window.location.origin : undefined);
  const title = normalizeMetadataText(paper.title);
  const abstract = normalizeMetadataText(paper.abstract);
  const keywords = uniqueMetadataValues(paper.keywords ?? []);
  const venue = normalizeMetadataText(paper.venue ?? paper.conference ?? null);
  const publicationDate = paperPublicationDate(paper);
  const publicUrl = buildPaperUrl(paper.id, origin);
  const pdfUrl = buildPaperPdfUrl(paper, origin);

  const addEntry = (name: string, content: string | null) => {
    if (content) {
      entries.push({ name, content });
    }
  };

  addEntry('citation_title', title);
  for (const author of uniqueMetadataValues(paper.authors ?? [])) {
    addEntry('citation_author', author);
  }
  addEntry('citation_abstract', abstract);
  addEntry('citation_conference_title', venue);
  addEntry('citation_publication_date', publicationDate);
  addEntry('citation_keywords', keywords.length > 0 ? keywords.join('; ') : null);
  addEntry('citation_public_url', publicUrl);
  addEntry('citation_pdf_url', pdfUrl);
  addEntry('citation_arxiv_id', normalizeMetadataText(paper.arxiv?.arxiv_id));

  return entries;
}

function clearZoteroPaperMetadata() {
  document.querySelectorAll(ZOTERO_META_SELECTOR).forEach((element) => element.remove());
}

function dispatchZoteroItemUpdated() {
  document.dispatchEvent(new Event('ZoteroItemUpdated', { bubbles: true, cancelable: true }));
}

function writeZoteroPaperMetadata(entries: ZoteroMetadataEntry[]) {
  for (const entry of entries) {
    const element = document.createElement('meta');
    element.setAttribute('name', entry.name);
    element.setAttribute('content', entry.content);
    element.setAttribute(ZOTERO_META_ATTRIBUTE, 'true');
    document.head.appendChild(element);
  }
}

export function useZoteroPaperMetadata(paper: Paper | null) {
  useEffect(() => {
    if (typeof document === 'undefined') {
      return undefined;
    }

    clearZoteroPaperMetadata();

    if (!paper) {
      dispatchZoteroItemUpdated();
      return () => {
        clearZoteroPaperMetadata();
        dispatchZoteroItemUpdated();
      };
    }

    writeZoteroPaperMetadata(buildZoteroPaperMetadata(paper));
    dispatchZoteroItemUpdated();

    return () => {
      clearZoteroPaperMetadata();
      dispatchZoteroItemUpdated();
    };
  }, [paper]);
}
