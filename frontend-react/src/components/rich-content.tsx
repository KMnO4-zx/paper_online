import { useEffect, useMemo, useRef } from 'react';

import { renderMarkdown, renderMath } from '@/lib/content';

interface RichContentProps {
  content: string;
  className?: string;
}

export function RichContent({ content, className }: RichContentProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const html = useMemo(() => renderMarkdown(content), [content]);

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
