import { useEffect, useMemo, useRef } from 'react';

import { renderInlineContent, renderMarkdown, renderMath } from '@/lib/content';

interface RichContentProps {
  content: string;
  className?: string;
  inline?: boolean;
}

export function RichContent({ content, className, inline = false }: RichContentProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const html = useMemo(
    () => (inline ? renderInlineContent(content) : renderMarkdown(content)),
    [content, inline],
  );

  useEffect(() => {
    renderMath(containerRef.current);
  }, [html]);

  return (
    <div
      ref={containerRef}
      className={className}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}
