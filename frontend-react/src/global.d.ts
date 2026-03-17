interface Window {
  marked?: {
    parse: (markdown: string) => string;
  };
  renderMathInElement?: (
    element: HTMLElement,
    options?: {
      delimiters?: Array<{ left: string; right: string; display: boolean }>;
      throwOnError?: boolean;
      strict?: boolean;
    },
  ) => void;
}

declare module 'katex/contrib/auto-render' {
  interface AutoRenderDelimiter {
    left: string;
    right: string;
    display: boolean;
  }

  interface AutoRenderOptions {
    delimiters?: AutoRenderDelimiter[];
    throwOnError?: boolean;
    strict?: boolean;
  }

  export default function renderMathInElement(
    element: HTMLElement,
    options?: AutoRenderOptions,
  ): void;
}
