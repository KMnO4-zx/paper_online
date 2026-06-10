import { ArrowRight, CalendarDays, FileText, Loader2, Sparkles } from 'lucide-react';
import { useState } from 'react';

import { Button } from '@/components/ui/button';
import { SearchControls } from '@/components/search-controls';
import { CONFERENCES } from '@/lib/constants';
import { createArxivPaper } from '@/lib/api';
import { extractArxivId } from '@/lib/arxiv';
import { applyFilters, buildQueryString, navigate } from '@/lib/router';
import type { SearchFilters } from '@/types';

export function HomePage() {
  const [query, setQuery] = useState('');
  const [filters, setFilters] = useState<SearchFilters>({
    title: true,
    abstract: true,
    keywords: true,
  });
  const [isAddingArxiv, setIsAddingArxiv] = useState(false);
  const [arxivSubmitError, setArxivSubmitError] = useState<string | null>(null);
  const detectedArxivId = extractArxivId(query);

  const submitSearch = async () => {
    const trimmedQuery = query.trim();
    if (!trimmedQuery || isAddingArxiv) {
      return;
    }

    const arxivId = extractArxivId(trimmedQuery);
    if (arxivId) {
      setIsAddingArxiv(true);
      setArxivSubmitError(null);
      try {
        const paper = await createArxivPaper(trimmedQuery);
        navigate(`/papers/${encodeURIComponent(paper.id)}`);
      } catch (error) {
        setArxivSubmitError(error instanceof Error ? error.message : 'arXiv 论文加载失败');
      } finally {
        setIsAddingArxiv(false);
      }
      return;
    }

    setArxivSubmitError(null);
    const params = applyFilters(new URLSearchParams(), filters);
    params.set('q', trimmedQuery);
    navigate(`/search${buildQueryString(params)}`);
  };

  return (
    <div className="mx-auto max-w-7xl animate-fade-in">
      <section className="grid items-start gap-10 py-10 lg:grid-cols-[1.05fr_0.95fr] lg:gap-14">
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

        <div className="relative lg:pt-16 xl:pt-20">
          <div className="absolute -inset-10 rounded-[48px] bg-gradient-to-br from-[#ffe7b5] via-[#fff7df] to-[#d9efff] opacity-80 blur-3xl" />
          <div className="relative ml-auto max-w-[48rem] rounded-[40px] bg-gradient-to-br from-white/75 via-[#fffaf0]/70 to-[#edfaff]/75 p-4 shadow-[0_24px_72px_rgba(148,163,184,0.24)] ring-1 ring-white/70 backdrop-blur-sm sm:p-5 lg:p-6">
            <div className="w-full">
              <SearchControls
                query={query}
                filters={filters}
                onQueryChange={setQuery}
                onFiltersChange={setFilters}
                onSubmit={submitSearch}
                placeholder="搜索会议论文，或粘贴 arXiv 链接 / ID..."
                submitLabel={detectedArxivId ? (isAddingArxiv ? '准备分析' : '分析 arXiv') : '搜索'}
                hero
              />
              {arxivSubmitError ? (
                <div className="mt-3 rounded-2xl bg-[#fff1f2] px-4 py-3 text-sm text-[#b91c1c]">
                  {arxivSubmitError}
                </div>
              ) : null}
              {isAddingArxiv ? (
                <div className="mt-3 flex items-center gap-2 px-2 text-sm text-[#728095]">
                  <Loader2 className="h-4 w-4 animate-spin text-[#ff9900]" />
                  正在准备 arXiv:{detectedArxivId} 的 AI 分析
                </div>
              ) : null}
            </div>
          </div>
        </div>
      </section>

      <section className="mt-10">
        <button
          type="button"
          onClick={() => navigate('/hf-daily')}
          className="group relative w-full overflow-hidden rounded-[32px] bg-white p-6 text-left shadow-sm ring-1 ring-black/5 transition hover:-translate-y-1 hover:shadow-xl"
        >
          <div className="absolute inset-x-0 top-0 h-1.5 bg-gradient-to-r from-[#ff9900] via-[#ffd166] to-[#ff7a00]" />
          <div className="flex flex-col gap-5 md:flex-row md:items-center md:justify-between">
            <div>
              <div className="mb-3 inline-flex items-center gap-2 rounded-full bg-[#fff7ed] px-3 py-1 text-sm text-[#c2410c]">
                <Sparkles className="h-4 w-4 text-[#ff9900]" />
                每日热门论文
              </div>
              <h2 className="text-2xl font-semibold text-[#172033]">Hugging Face Daily Papers</h2>
              <p className="mt-2 max-w-3xl text-sm leading-6 text-[#6b7280]">
                每天晚上自动抓取 Hugging Face Daily Papers 点赞最多的 5 篇论文，按日期倒序展示，并自动进行 AI 分析。
              </p>
            </div>
            <Button variant="ghost" className="px-0 text-[#ff7a00] hover:bg-transparent hover:text-[#ff7a00]">
              查看 Daily Papers
              <ArrowRight className="ml-2 h-4 w-4 transition group-hover:translate-x-1" />
            </Button>
          </div>
        </button>
      </section>

      <section className="mt-10">
        <button
          type="button"
          onClick={() => navigate('/arxiv')}
          className="group relative w-full overflow-hidden rounded-[32px] bg-white p-6 text-left shadow-sm ring-1 ring-black/5 transition hover:-translate-y-1 hover:shadow-xl"
        >
          <div className="absolute inset-x-0 top-0 h-1.5 bg-gradient-to-r from-[#0891b2] via-[#38bdf8] to-[#0f766e]" />
          <div className="flex flex-col gap-5 md:flex-row md:items-center md:justify-between">
            <div>
              <div className="mb-3 inline-flex items-center gap-2 rounded-full bg-[#ecfeff] px-3 py-1 text-sm text-[#075985]">
                <FileText className="h-4 w-4 text-[#0891b2]" />
                arXiv 论文
              </div>
              <h2 className="text-2xl font-semibold text-[#172033]">最近分析的 arXiv 论文</h2>
              <p className="mt-2 max-w-3xl text-sm leading-6 text-[#6b7280]">
                展示用户主动添加并完成 AI 分析的 arXiv 论文，按添加时间倒序排列，同时保留 arXiv 原始发布时间。
              </p>
            </div>
            <Button variant="ghost" className="px-0 text-[#0891b2] hover:bg-transparent hover:text-[#0e7490]">
              查看 arXiv Papers
              <ArrowRight className="ml-2 h-4 w-4 transition group-hover:translate-x-1" />
            </Button>
          </div>
        </button>
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
