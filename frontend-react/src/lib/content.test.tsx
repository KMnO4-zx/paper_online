import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';

import { RichContent } from '@/components/rich-content';

import { normalizeMarkdownContent, splitStreamingMarkdown } from './content';

describe('normalizeMarkdownContent', () => {
  it('normalizes bracket math and markdown markers', () => {
    const normalized = normalizeMarkdownContent(String.raw`\#Heading
\(x_i\)
\[
\frac{1}{2}
\]
1)First item`);

    expect(normalized).toContain('# Heading');
    expect(normalized).toContain('$x_i$');
    expect(normalized).toContain('$$\n\\frac{1}{2}\n$$');
    expect(normalized).toContain('1) First item');
  });

  it('keeps math-like code fenced content untouched', () => {
    const normalized = normalizeMarkdownContent("```python\nvalue = '$x$'\n```");

    expect(normalized).toBe("```python\nvalue = '$x$'\n```");
  });

  it('splits inline heading fragments onto their own line', () => {
    const normalized = normalizeMarkdownContent(
      '开源代码仓库链接：https://github.com/lasr-spelling/sae-spelling # 问题1：论文要解决什么任务？',
    );

    expect(normalized).toContain('开源代码仓库链接：https://github.com/lasr-spelling/sae-spelling\n\n# 问题1：论文要解决什么任务？');
  });
});

describe('splitStreamingMarkdown', () => {
  it('holds an unclosed code fence in the unstable tail', () => {
    const split = splitStreamingMarkdown('Intro line\n```ts\nconst value = 1');

    expect(split.stableContent).toBe('Intro line\n');
    expect(split.unstableContent).toBe('```ts\nconst value = 1');
  });

  it('holds an unclosed inline formula in the unstable tail', () => {
    const split = splitStreamingMarkdown('The answer is $x');

    expect(split.stableContent).toBe('');
    expect(split.unstableContent).toBe('The answer is $x');
  });
});

describe('RichContent', () => {
  it('renders math through the markdown AST renderer', () => {
    const html = renderToStaticMarkup(
      <RichContent content={'The rate is $\\frac{1}{2}$.'} className="markdown-body" />,
    );

    expect(html).toContain('katex');
    expect(html).toContain('The rate is');
  });

  it('does not render code blocks as math', () => {
    const html = renderToStaticMarkup(
      <RichContent content={"```text\n$not-math$\n```"} className="markdown-body" />,
    );

    expect(html).not.toContain('katex');
    expect(html).toContain('$not-math$');
  });

  it('renders the unstable streaming tail as plain text', () => {
    const html = renderToStaticMarkup(
      <RichContent content={'Result:\n$$\na + b'} isStreaming className="markdown-body" />,
    );

    expect(html).toContain('rich-content-tail');
    expect(html).toContain('$$');
    expect(html).toContain('a + b');
  });
});
