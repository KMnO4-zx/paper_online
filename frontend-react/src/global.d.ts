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
