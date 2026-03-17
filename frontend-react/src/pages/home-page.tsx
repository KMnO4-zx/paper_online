import { ArrowRight, CalendarDays, Sparkles } from 'lucide-react';
import { useState } from 'react';

import { Button } from '@/components/ui/button';
import { SearchControls } from '@/components/search-controls';
import { CONFERENCES } from '@/lib/constants';
import { applyFilters, buildQueryString, navigate } from '@/lib/router';
import type { SearchFilters } from '@/types';

export function HomePage() {
  const [query, setQuery] = useState('');
  const [filters, setFilters] = useState<SearchFilters>({
    title: true,
    abstract: true,
    keywords: true,
  });

  const submitSearch = () => {
    if (!query.trim()) {
      return;
    }

    const params = applyFilters(new URLSearchParams(), filters);
    params.set('q', query.trim());
    navigate(`/search${buildQueryString(params)}`);
  };

  return (
    <div className="mx-auto max-w-7xl animate-fade-in">
      <section className="grid items-center gap-8 py-10 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="space-y-6">
          <div className="flex items-center gap-4">
            <img
              src="/images/logo.svg"
              alt="Paper Insight logo"
              className="h-16 w-16 rounded-[1.5rem] object-contain shadow-sm"
            />
            <div>
              <div className="text-2xl font-semibold tracking-tight text-[#172033]">Paper Insight</div>
              <div className="text-sm text-[#728095]">AI-driven paper analysis</div>
            </div>
          </div>

          <div className="inline-flex items-center gap-2 rounded-full bg-white/80 px-4 py-2 text-sm font-medium text-[#7a4b00] shadow-sm ring-1 ring-black/5">
            <Sparkles className="h-4 w-4 text-[#ff9900]" />
            AI 论文智能分析与检索
          </div>

          <div className="space-y-4">
            <h1 className="max-w-3xl text-4xl font-semibold leading-[1.18] tracking-tight text-[#172033] sm:text-5xl">
              用 AI 批量浏览 AI 会议论文，再决定哪些值得精读
            </h1>
            <p className="max-w-2xl text-lg leading-8 text-[#64748b]">
              辅助快速浏览 AI 会议论文，通过自动生成 AI 分析，帮你快速判断哪些论文值得收藏到 Zotero 继续精读，作为 AI 论文阅读流程中的第一道筛选关卡。
            </p>
          </div>
        </div>

        <div className="relative">
          <div className="absolute inset-0 rounded-[32px] bg-gradient-to-br from-[#ffe7b5] via-[#fff4d6] to-[#d9efff] blur-3xl" />
          <div className="relative rounded-[32px] border border-white/70 bg-white/60 p-4 backdrop-blur-sm">
            <SearchControls
              query={query}
              filters={filters}
              onQueryChange={setQuery}
              onFiltersChange={setFilters}
              onSubmit={submitSearch}
              placeholder="输入关键词搜索所有会议论文..."
            />
          </div>
        </div>
      </section>

      <section className="mt-10">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-semibold text-[#172033]">浏览会议论文</h2>
            <p className="mt-1 text-sm text-[#728095]">与当前后端支持的会议范围保持一致</p>
          </div>
        </div>

        <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
          {CONFERENCES.map((conference, index) => (
            <button
              key={conference.id}
              type="button"
              onClick={() => navigate(`/conference/${conference.id}`)}
              className="group relative overflow-hidden rounded-[28px] bg-white p-6 text-left shadow-sm ring-1 ring-black/5 transition hover:-translate-y-1 hover:shadow-xl"
              style={{ animationDelay: `${index * 0.1}s` }}
            >
              <div className={`absolute inset-x-0 top-0 h-1.5 bg-gradient-to-r ${conference.accentClass}`} />
              <div className="mb-8 flex items-center justify-between">
                <div className="inline-flex items-center gap-2 rounded-full bg-[#f8fafc] px-3 py-1 text-sm text-[#6b7280]">
                  <CalendarDays className="h-4 w-4 text-[#ff9900]" />
                  {conference.year}
                </div>
                <ArrowRight className="h-5 w-5 text-[#ff9900] transition group-hover:translate-x-1" />
              </div>

              <div className="space-y-3">
                <h3 className="text-2xl font-semibold text-[#1f2937]">{conference.name}</h3>
                <p className="min-h-[3rem] text-sm leading-6 text-[#6b7280]">{conference.fullName}</p>
              </div>

              <div className="mt-6">
                <Button variant="ghost" className="px-0 text-[#ff7a00] hover:bg-transparent hover:text-[#ff7a00]">
                  进入会议
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </div>
            </button>
          ))}
        </div>
      </section>
    </div>
  );
}
