import { useEffect, useMemo, useState } from 'react';
import { ChevronLeft, Loader2, Sparkles } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { PaginationBar } from '@/components/pagination-bar';
import { PaperCard } from '@/components/paper-card';
import { SearchControls } from '@/components/search-controls';
import { fetchHfDailyPapers } from '@/lib/api';
import { buildQueryString, navigate, parseFilters, parsePage, useAppLocation } from '@/lib/router';
import type { PaperListResponse, SearchFilters } from '@/types';

const EMPTY_RESULTS: PaperListResponse = {
  papers: [],
  total: 0,
  page: 1,
  pages: 1,
};

export function HfDailyPage() {
  const location = useAppLocation();
  const { query, page, filters } = useMemo(() => {
    const params = new URLSearchParams(location.search);
    return {
      query: params.get('q') ?? '',
      page: parsePage(params.get('page')),
      filters: parseFilters(params),
    };
  }, [location.search]);

  const [draftQuery, setDraftQuery] = useState(query);
  const [draftFilters, setDraftFilters] = useState<SearchFilters>(filters);
  const [results, setResults] = useState<PaperListResponse>(EMPTY_RESULTS);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setDraftQuery(query);
    setDraftFilters(filters);
  }, [query, filters]);

  useEffect(() => {
    let active = true;
    setIsLoading(true);
    setError(null);

    void fetchHfDailyPapers(page, query, filters)
      .then((payload) => {
        if (active) {
          setResults(payload);
        }
      })
      .catch((requestError) => {
        if (active) {
          setError(requestError instanceof Error ? requestError.message : '加载失败');
          setResults(EMPTY_RESULTS);
        }
      })
      .finally(() => {
        if (active) {
          setIsLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, [page, query, filters]);

  const submitSearch = () => {
    const next = new URLSearchParams();
    if (draftQuery.trim()) {
      next.set('q', draftQuery.trim());
      next.set('title', String(draftFilters.title));
      next.set('abstract', String(draftFilters.abstract));
      next.set('keywords', String(draftFilters.keywords));
    }
    navigate(`/hf-daily${buildQueryString(next)}`);
  };

  const onPageChange = (nextPage: number) => {
    const next = new URLSearchParams(location.search);
    next.set('page', String(nextPage));
    navigate(`/hf-daily${buildQueryString(next)}`);
  };

  return (
    <div className="mx-auto max-w-6xl animate-fade-in">
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="space-y-2">
          <Button variant="ghost" className="rounded-full px-0 text-[#728095]" onClick={() => navigate('/')}>
            <ChevronLeft className="mr-1 h-4 w-4" />
            返回首页
          </Button>
          <div>
            <div className="mb-2 inline-flex items-center gap-2 rounded-full bg-white/80 px-3 py-1 text-sm text-[#7a4b00] shadow-sm ring-1 ring-black/5">
              <Sparkles className="h-4 w-4 text-[#ff9900]" />
              Hugging Face Daily Papers
            </div>
            <h1 className="text-3xl font-semibold text-[#172033]">Hugging Face Daily Papers</h1>
            <p className="text-sm text-[#728095]">按入库时间倒序展示每日点赞最高论文</p>
          </div>
        </div>
      </div>

      <SearchControls
        query={draftQuery}
        filters={draftFilters}
        onQueryChange={setDraftQuery}
        onFiltersChange={setDraftFilters}
        onSubmit={submitSearch}
        placeholder="搜索 Hugging Face Daily Papers..."
        compact
      />

      <div className="mt-6 rounded-[28px] bg-white/70 p-4 text-sm text-[#596579] shadow-sm ring-1 ring-black/5">
        共 {results.total} 篇论文
      </div>

      {isLoading ? (
        <div className="mt-8 flex items-center justify-center gap-2 rounded-[28px] bg-white/90 p-8 text-[#728095] shadow-sm ring-1 ring-black/5">
          <Loader2 className="h-5 w-5 animate-spin" />
          加载论文中...
        </div>
      ) : error ? (
        <div className="mt-8 rounded-[28px] bg-white/90 p-8 text-center text-[#b91c1c] shadow-sm ring-1 ring-black/5">
          {error}
        </div>
      ) : results.papers.length === 0 ? (
        <div className="mt-8 rounded-[28px] bg-white/90 p-8 text-center text-[#728095] shadow-sm ring-1 ring-black/5">
          暂无 Hugging Face Daily Papers 数据
        </div>
      ) : (
        <div className="mt-8 space-y-4">
          {results.papers.map((paper, index) => (
            <PaperCard
              key={paper.id}
              paper={paper}
              index={index}
              onOpen={(nextPaper) => navigate(`/papers/${nextPaper.id}`)}
            />
          ))}
        </div>
      )}

      <PaginationBar page={results.page} pages={results.pages} onPageChange={onPageChange} />
    </div>
  );
}
