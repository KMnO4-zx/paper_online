import { useLayoutEffect, useMemo, useRef } from 'react';

import { renderInlineContent, renderMarkdown, renderMath } from '@/lib/content';

interface RichContentProps {
  content: string;
  className?: string;
  inline?: boolean;
  analysisMode?: boolean;
}

export function RichContent({ content, className, inline = false, analysisMode = false }: RichContentProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const html = useMemo(
    () => (inline ? renderInlineContent(content) : renderMarkdown(content, { analysisMode })),
    [analysisMode, content, inline],
  );

  useLayoutEffect(() => {
    renderMath(containerRef.current);
  });

  return (
    <div
      ref={containerRef}
      className={className}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}
