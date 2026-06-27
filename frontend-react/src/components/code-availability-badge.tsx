import { Code2, ExternalLink } from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import type { PaperCodeStatus } from '@/types';

interface CodeAvailabilityBadgeProps {
  status?: PaperCodeStatus | null;
  codeUrl?: string | null;
  className?: string;
}

function isCodeAvailable(status?: PaperCodeStatus | null): boolean {
  return status === 'open_source';
}

export function CodeAvailabilityBadge({
  status,
  codeUrl,
  className = '',
}: CodeAvailabilityBadgeProps) {
  const available = isCodeAvailable(status);
  const label = available ? 'Code available' : 'Code unavailable';
  const badgeClass = available
    ? 'border-emerald-200 bg-emerald-50 text-emerald-700'
    : 'border-[#e6ebf2] bg-[#f8fafc] text-[#64748b]';
  const content = (
    <>
      <Code2 className="mr-1 h-3 w-3" />
      {label}
      {available && codeUrl ? <ExternalLink className="ml-1 h-3 w-3" /> : null}
    </>
  );

  if (available && codeUrl) {
    return (
      <Badge asChild variant="outline" className={`${badgeClass} ${className}`}>
        <a href={codeUrl} target="_blank" rel="noreferrer" onClick={(event) => event.stopPropagation()}>
          {content}
        </a>
      </Badge>
    );
  }

  return (
    <Badge variant="outline" className={`${badgeClass} ${className}`}>
      {content}
    </Badge>
  );
}
