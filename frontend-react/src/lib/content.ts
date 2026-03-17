import { marked } from 'marked';
import renderMathInElement from 'katex/contrib/auto-render';

function escapeHtml(content: string): string {
  return content
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}

const CODE_SEGMENT_PATTERN = /```[\s\S]*?```|`[^`\n]+`/g;

function maskCodeSegments(content: string): { masked: string; segments: string[] } {
  const segments: string[] = [];
  const masked = content.replace(CODE_SEGMENT_PATTERN, (segment) => {
    const token = `__CODE_SEGMENT_${segments.length}__`;
    segments.push(segment);
    return token;
  });

  return { masked, segments };
}

function unmaskCodeSegments(content: string, segments: string[]): string {
  return content.replace(/__CODE_SEGMENT_(\d+)__/g, (_, index) => segments[Number(index)] ?? '');
}

function looksLikeInlineMath(expression: string): boolean {
  const value = expression.trim();
  if (!value) {
    return false;
  }

  if (/\\[A-Za-z]+|[_^{}]/.test(value)) {
    return true;
  }

  if (/\s/.test(value)) {
    return false;
  }

  if (!/[A-Za-z]/.test(value) && !/[=<>+\-*/]/.test(value)) {
    return false;
  }

  return /^[A-Za-z0-9()[\].,:;+\-*/=<>|]+$/.test(value);
}

function normalizeEscapedInlineMath(content: string): string {
  return content
    .replace(/\\\$([^\n]*?)(\\\$|\$)/g, (match, expression) =>
      looksLikeInlineMath(expression) ? `$${expression}$` : match,
    )
    .replace(/\$([^\n]*?)\\\$/g, (match, expression) =>
      looksLikeInlineMath(expression) ? `$${expression}$` : match,
    );
}

export function normalizeMathContent(content: string): string {
  if (!content) {
    return '';
  }

  const { masked, segments } = maskCodeSegments(content);
  const normalized = normalizeEscapedInlineMath(
    masked
      .replace(/\\\$\$([\s\S]+?)\\\$\$/g, (_, expression) => `$$${expression}$$`)
      .replace(/\\\$\$([\s\S]+?)\$\$/g, (_, expression) => `$$${expression}$$`)
      .replace(/\$\$([\s\S]+?)\\\$\$/g, (_, expression) => `$$${expression}$$`),
  );

  return unmaskCodeSegments(normalized, segments);
}

interface MarkdownRenderOptions {
  analysisMode?: boolean;
}

function normalizeMarkdownSyntax(content: string, options: MarkdownRenderOptions = {}): string {
  if (!content) {
    return '';
  }

  const { masked, segments } = maskCodeSegments(content);
  let normalized = masked
    .replace(/^([ \t]{0,3})\\(#{1,6})(?=\s|\S)/gm, '$1$2')
    .replace(/^(#{1,6})(\S)/gm, '$1 $2');

  if (options.analysisMode) {
    const lines = normalized.split('\n');
    normalized = lines
      .map((line, index) => {
        const trimmed = line.trim();
        if (!trimmed) {
          return line;
        }

        const leadingWhitespace = line.match(/^\s*/)?.[0] ?? '';
        const previousLine = index > 0 ? lines[index - 1].trim() : '';

        if (!previousLine) {
          const numberedSectionMatch = trimmed.match(/^(\d+[.、:：)]\s*.+)$/);
          if (numberedSectionMatch && trimmed.length <= 80) {
            return `${leadingWhitespace}## ${numberedSectionMatch[1]}`;
          }
        }

        const looseHashHeadingMatch = trimmed.match(/^#+\s*.+$/);
        if (looseHashHeadingMatch) {
          const [, hashes = '', title = ''] = trimmed.match(/^(#{1,6})\s*(.+)$/) ?? [];
          if (hashes && title) {
            return `${leadingWhitespace}${hashes} ${title}`;
          }
        }

        return line;
      })
      .join('\n');
  }

  return unmaskCodeSegments(normalized, segments);
}

export function renderInlineContent(content: string): string {
  if (!content) {
    return '';
  }

  return escapeHtml(normalizeMathContent(content)).replaceAll('\n', '<br />');
}

export function renderMarkdown(content: string, options: MarkdownRenderOptions = {}): string {
  if (!content) {
    return '';
  }

  const normalizedContent = normalizeMarkdownSyntax(normalizeMathContent(content), options);
  return marked.parse(normalizedContent, { async: false }) as string;
}

export function renderMath(element: HTMLElement | null): void {
  if (!element) {
    return;
  }

  renderMathInElement(element, {
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
