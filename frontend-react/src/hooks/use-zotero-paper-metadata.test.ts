import { describe, expect, it } from 'vitest';

import type { Paper } from '@/types';

import { buildZoteroPaperMetadata } from './use-zotero-paper-metadata';

function metadataByName(paper: Paper, name: string): string[] {
  return buildZoteroPaperMetadata(paper, { origin: 'https://paper-insight.herobase.tech' })
    .filter((entry) => entry.name === name)
    .map((entry) => entry.content);
}

describe('buildZoteroPaperMetadata', () => {
  it('builds Zotero citation metadata from a conference paper', () => {
    const paper: Paper = {
      id: 'paper/id',
      title: '  Test   Paper  ',
      abstract: 'A paper about metadata.',
      authors: ['Alice Zhang', 'Bob Li', 'Alice Zhang', ' '],
      keywords: ['metadata', 'zotero', 'metadata'],
      venue: 'ICLR 2026 Poster',
      pdf: '/pdfs/test.pdf',
    };

    expect(metadataByName(paper, 'citation_title')).toEqual(['Test Paper']);
    expect(metadataByName(paper, 'citation_author')).toEqual(['Alice Zhang', 'Bob Li']);
    expect(metadataByName(paper, 'citation_conference_title')).toEqual(['ICLR 2026 Poster']);
    expect(metadataByName(paper, 'citation_publication_date')).toEqual(['2026']);
    expect(metadataByName(paper, 'citation_keywords')).toEqual(['metadata; zotero']);
    expect(metadataByName(paper, 'citation_public_url')).toEqual([
      'https://paper-insight.herobase.tech/papers/paper%2Fid',
    ]);
    expect(metadataByName(paper, 'citation_pdf_url')).toEqual([
      'https://paper-insight.herobase.tech/pdfs/test.pdf',
    ]);
  });

  it('prefers arXiv PDF metadata when available', () => {
    const paper: Paper = {
      id: 'arxiv:2401.00001',
      title: 'Arxiv Paper',
      abstract: 'An arXiv paper.',
      keywords: [],
      pdf: 'https://openreview.net/pdf?id=arxiv:2401.00001',
      arxiv: {
        arxiv_id: '2401.00001',
        pdf_url: 'https://arxiv.org/pdf/2401.00001',
        published_at: '2024-01-02T00:00:00Z',
      },
    };

    expect(metadataByName(paper, 'citation_pdf_url')).toEqual(['https://arxiv.org/pdf/2401.00001']);
    expect(metadataByName(paper, 'citation_arxiv_id')).toEqual(['2401.00001']);
    expect(metadataByName(paper, 'citation_publication_date')).toEqual(['2024-01-02']);
  });
});
