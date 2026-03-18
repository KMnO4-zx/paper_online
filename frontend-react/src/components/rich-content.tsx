import type { Components } from 'react-markdown';
import { useMemo } from 'react';
import ReactMarkdown from 'react-markdown';
import rehypeKatex from 'rehype-katex';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';

import { normalizeMarkdownContent, splitStreamingMarkdown } from '@/lib/content';

interface RichContentProps {
  content: string;
  className?: string;
  inline?: boolean;
  analysisMode?: boolean;
  isStreaming?: boolean;
}

const blockComponents: Components = {
  a: ({ node: _node, href, children, ...props }) => {
    void _node;
    const isExternal = Boolean(href && !href.startsWith('#'));
    return (
      <a
        {...props}
        href={href}
        target={isExternal ? '_blank' : undefined}
        rel={isExternal ? 'noreferrer' : undefined}
      >
        {children}
      </a>
    );
  },
};

const inlineComponents: Components = {
  ...blockComponents,
  p: ({ node: _node, children }) => {
    void _node;
    return <>{children}</>;
  },
};

function MarkdownAst({
  content,
  components,
}: {
  content: string;
  components: Components;
}) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm, remarkMath]}
      rehypePlugins={[rehypeKatex]}
      skipHtml
      components={components}
    >
      {content}
    </ReactMarkdown>
  );
}

export function RichContent({
  content,
  className,
  inline = false,
  analysisMode = false,
  isStreaming = false,
}: RichContentProps) {
  const normalizedContent = useMemo(
    () => normalizeMarkdownContent(content, { analysisMode }),
    [analysisMode, content],
  );
  const splitContent = useMemo(
    () => (isStreaming ? splitStreamingMarkdown(content, { analysisMode }) : null),
    [analysisMode, content, isStreaming],
  );

  if (inline) {
    return (
      <span className={className}>
        <MarkdownAst content={normalizedContent} components={inlineComponents} />
      </span>
    );
  }

  const stableContent = splitContent?.stableContent ?? normalizedContent;
  const unstableContent = splitContent?.unstableContent ?? '';

  return (
    <div className={className}>
      {stableContent ? <MarkdownAst content={stableContent} components={blockComponents} /> : null}
      {unstableContent ? <pre className="rich-content-tail">{unstableContent}</pre> : null}
    </div>
  );
}
