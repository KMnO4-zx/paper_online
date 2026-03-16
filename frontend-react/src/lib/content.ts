function escapeHtml(content: string): string {
  return content
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}

export function renderMarkdown(content: string): string {
  if (!content) {
    return '';
  }

  if (window.marked?.parse) {
    return window.marked.parse(content);
  }

  const paragraphs = escapeHtml(content)
    .split(/\n{2,}/)
    .map((paragraph) => `<p>${paragraph.replaceAll('\n', '<br />')}</p>`);
  return paragraphs.join('');
}

export function renderMath(element: HTMLElement | null): void {
  if (!element || !window.renderMathInElement) {
    return;
  }

  window.renderMathInElement(element, {
    delimiters: [
      { left: '$$', right: '$$', display: true },
      { left: '$', right: '$', display: false },
    ],
    throwOnError: false,
    strict: false,
  });
}

export function normalizeKeywords(keywords: string[] | undefined | null): string[] {
  if (!keywords?.length) {
    return [];
  }

  const flattened = keywords.flatMap((keyword) =>
    keyword
      .split(';')
      .map((item) => item.trim())
      .filter(Boolean),
  );

  return [...new Set(flattened)];
}

export function getVenueParts(venue?: string | null): { label: string; conference: string; type: string } {
  if (!venue) {
    return { label: 'Unknown venue', conference: 'Unknown', type: '' };
  }

  const lower = venue.toLowerCase();
  const conference = lower.includes('neurips')
    ? 'NeurIPS'
    : lower.includes('iclr')
      ? 'ICLR'
      : lower.includes('icml')
        ? 'ICML'
        : venue.split(' ')[0];

  const type = lower.includes('oral')
    ? 'Oral'
    : lower.includes('spotlight')
      ? 'Spotlight'
      : lower.includes('poster')
        ? 'Poster'
        : '';

  return {
    label: venue,
    conference,
    type,
  };
}
