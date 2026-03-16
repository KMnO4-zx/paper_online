import { Search } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Input } from '@/components/ui/input';
import type { SearchFilters } from '@/types';

interface SearchControlsProps {
  query: string;
  filters: SearchFilters;
  onQueryChange: (value: string) => void;
  onFiltersChange: (value: SearchFilters) => void;
  onSubmit: () => void;
  placeholder: string;
  submitLabel?: string;
  compact?: boolean;
}

export function SearchControls({
  query,
  filters,
  onQueryChange,
  onFiltersChange,
  onSubmit,
  placeholder,
  submitLabel = '搜索',
  compact = false,
}: SearchControlsProps) {
  const toggleFilter = (key: keyof SearchFilters) => {
    const next = { ...filters, [key]: !filters[key] };
    if (!next.title && !next.abstract && !next.keywords) {
      return;
    }
    onFiltersChange(next);
  };

  return (
    <div className={`rounded-2xl bg-white/90 shadow-sm ring-1 ring-black/5 ${compact ? 'p-4' : 'p-8'}`}>
      <div className={`mb-4 flex flex-wrap items-center gap-5 ${compact ? 'justify-start' : 'justify-center'}`}>
        {(['title', 'abstract', 'keywords'] as Array<keyof SearchFilters>).map((field) => (
          <label key={field} className="flex cursor-pointer items-center gap-2 text-sm text-[#3f4a5a]">
            <Checkbox
              checked={filters[field]}
              onCheckedChange={() => toggleFilter(field)}
              className="border-[#c6d0dc] data-[state=checked]:border-[#ff9900] data-[state=checked]:bg-[#ff9900]"
            />
            <span className={filters[field] ? 'font-semibold text-[#172033]' : ''}>
              {field === 'title' ? 'Title' : field === 'abstract' ? 'Abstract' : 'Keywords'}
            </span>
          </label>
        ))}
      </div>

      <div className={`flex ${compact ? 'flex-col gap-3 sm:flex-row' : 'gap-3'} items-stretch`}>
        <div className="relative flex-1">
          <Input
            value={query}
            onChange={(event) => onQueryChange(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === 'Enter' && event.shiftKey) {
                event.preventDefault();
                onSubmit();
              } else if (event.key === 'Enter') {
                event.preventDefault();
              }
            }}
            className="h-12 rounded-xl border-2 border-transparent bg-[#f6f8fb] pl-11 text-base shadow-none transition hover:border-[#d7dfe8] focus-visible:border-[#ff9900] focus-visible:ring-0"
            placeholder={placeholder}
          />
          <Search className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-[#7a8799]" />
        </div>
        <Button
          onClick={onSubmit}
          className="h-12 rounded-xl bg-gradient-to-r from-[#ff9900] to-[#ff7a00] px-6 font-semibold text-white hover:from-[#ff7a00] hover:to-[#ff9900]"
        >
          <Search className="mr-2 h-4 w-4" />
          {submitLabel}
        </Button>
      </div>
    </div>
  );
}
