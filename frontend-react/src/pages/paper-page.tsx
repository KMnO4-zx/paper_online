import { useCallback, useEffect, useRef, useState } from 'react';
import { ChevronLeft, Eye, ExternalLink, FileText, Heart, Loader2, Sparkles } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ChatPanel } from '@/components/chat-panel';
import { RichContent } from '@/components/rich-content';
import { fetchPaperInfo, streamSse } from '@/lib/api';
import { getVenueParts, normalizeKeywords } from '@/lib/content';
import { navigate } from '@/lib/router';
import { getPaperMarks, setPaperMark } from '@/lib/storage';
import type { Paper } from '@/types';

interface PaperPageProps {
  paperId: string;
}

export function PaperPage({ paperId }: PaperPageProps) {
  const [paper, setPaper] = useState<Paper | null>(null);
  const [paperError, setPaperError] = useState<string | null>(null);
  const [paperLoading, setPaperLoading] = useState(true);
  const [analysisText, setAnalysisText] = useState('');
  const [analysisStatus, setAnalysisStatus] = useState('正在获取论文信息...');
  const [analysisLoading, setAnalysisLoading] = useState(true);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [marks, setMarks] = useState(() => getPaperMarks(paperId));
  const [isLikeAnimating, setIsLikeAnimating] = useState(false);
  const analysisRequestIdRef = useRef(0);
  const analysisAbortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    setMarks(getPaperMarks(paperId));
  }, [paperId]);

  useEffect(() => {
    let active = true;
    setPaperLoading(true);
    setPaperError(null);

    void fetchPaperInfo(paperId)
      .then((payload) => {
        if (active) {
          setPaper(payload);
        }
      })
      .catch((error) => {
        if (active) {
          setPaperError(error instanceof Error ? error.message : '加载失败');
          setPaper(null);
        }
      })
      .finally(() => {
        if (active) {
          setPaperLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, [paperId]);

  const loadAnalysis = useCallback(async (reanalyze = false) => {
    analysisAbortRef.current?.abort();
    const controller = new AbortController();
    analysisAbortRef.current = controller;
    const requestId = analysisRequestIdRef.current + 1;
    analysisRequestIdRef.current = requestId;

    setAnalysisText('');
    setAnalysisError(null);
    setAnalysisLoading(true);
    setAnalysisStatus(reanalyze ? '正在重新分析论文...' : '正在获取论文信息...');

    try {
      await streamSse(
        `/paper/${paperId}${reanalyze ? '?reanalyze=true' : ''}`,
        { method: 'GET', signal: controller.signal },
        {
          onChunk: (chunk) => {
            if (analysisRequestIdRef.current !== requestId) {
              return;
            }
            setAnalysisLoading(false);
            setAnalysisText((current) => current + chunk);
          },
          onEvent: (event, data) => {
            if (analysisRequestIdRef.current !== requestId) {
              return;
            }
            if (event === 'status') {
              setAnalysisStatus(data);
            }
            if (event === 'error') {
              setAnalysisLoading(false);
              setAnalysisError(data || '分析失败');
            }
            if (event === 'done') {
              setAnalysisLoading(false);
              setAnalysisStatus('');
            }
          },
        },
      );
    } catch (error) {
      if (controller.signal.aborted) {
        return;
      }
      setAnalysisLoading(false);
      setAnalysisError(error instanceof Error ? error.message : '分析失败');
    } finally {
      if (analysisAbortRef.current === controller) {
        analysisAbortRef.current = null;
      }
    }
  }, [paperId]);

  useEffect(() => {
    void loadAnalysis(false);
    return () => {
      analysisAbortRef.current?.abort();
      analysisAbortRef.current = null;
    };
  }, [loadAnalysis]);

  const venue = getVenueParts(paper?.venue);
  const keywords = normalizeKeywords(paper?.keywords);
  const openReviewUrl = `https://openreview.net/forum?id=${paperId}`;
  const pdfUrl = paper?.pdf || `https://openreview.net/pdf?id=${paperId}`;

  return (
    <div className="mx-auto max-w-[96rem] animate-fade-in">
      <Button
        variant="ghost"
        className="mb-4 rounded-full px-0 text-[#728095]"
        onClick={() => {
          if (window.history.length > 1) {
            window.history.back();
            return;
          }
          navigate('/');
        }}
      >
        <ChevronLeft className="mr-1 h-4 w-4" />
        返回
      </Button>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.55fr)_minmax(24rem,0.95fr)] 2xl:grid-cols-[minmax(0,1.7fr)_minmax(26rem,1.02fr)]">
        <div className="space-y-6">
          <section className="rounded-[32px] bg-white p-6 shadow-sm ring-1 ring-black/5">
            {paperLoading ? (
              <div className="flex items-center gap-2 text-[#728095]">
                <Loader2 className="h-5 w-5 animate-spin" />
                加载论文信息...
              </div>
            ) : paperError ? (
              <div className="text-[#b91c1c]">{paperError}</div>
            ) : paper ? (
              <div className="space-y-6">
                <div>
                  <h1 className="text-3xl font-semibold leading-tight text-[#172033]">{paper.title}</h1>
                  <div className="mt-4 flex flex-wrap gap-2.5">
                    <Badge variant="outline" className="border-blue-200 bg-blue-50 px-3 py-1 text-sm text-blue-700">
                      {venue.label}
                    </Badge>
                    {paper.primary_area ? (
                      <Badge
                        variant="outline"
                        className="border-[#e6ebf2] bg-[#f8fafc] px-3 py-1 text-sm text-[#516072]"
                      >
                        {paper.primary_area}
                      </Badge>
                    ) : null}
                    {keywords.slice(0, 6).map((keyword, index) => (
                      <Badge
                        key={`${paper.id}-${keyword}`}
                        variant="outline"
                        className={
                          index % 2 === 0
                            ? 'border-orange-100 bg-orange-50 px-3 py-1 text-sm text-orange-700'
                            : 'border-violet-100 bg-violet-50 px-3 py-1 text-sm text-violet-700'
                        }
                      >
                        {keyword}
                      </Badge>
                    ))}
                  </div>
                </div>

                <div>
                  <h2 className="mb-3 text-sm font-semibold uppercase tracking-[0.2em] text-[#8a98ac]">Abstract</h2>
                  <RichContent content={paper.abstract || '暂无摘要'} className="markdown-body text-base leading-7 text-[#475569]" />
                </div>

                <div className="flex flex-wrap gap-2">
                  <a href={openReviewUrl} target="_blank" rel="noreferrer">
                    <Button variant="outline" className="rounded-full border-[#f3d597] bg-[#fff7df] text-[#c77b00]">
                      <ExternalLink className="mr-1.5 h-4 w-4" />
                      OpenReview
                    </Button>
                  </a>
                  <a href={pdfUrl} target="_blank" rel="noreferrer">
                    <Button variant="outline" className="rounded-full border-[#bfdbfe] bg-[#eff6ff] text-[#2563eb]">
                      <FileText className="mr-1.5 h-4 w-4" />
                      PDF
                    </Button>
                  </a>
                  <Button
                    variant="outline"
                    className={`rounded-full ${
                      marks.viewed
                        ? 'border-[#bfdbfe] bg-[#eff6ff] text-[#2563eb]'
                        : 'border-[#dbe2ea] text-[#66768b]'
                    }`}
                    onClick={() => setMarks(setPaperMark(paperId, 'viewed', !marks.viewed))}
                  >
                    <Eye className={`mr-1.5 h-4 w-4 ${marks.viewed ? 'fill-current' : ''}`} />
                    {marks.viewed ? '已看过' : '看过'}
                  </Button>
                  <Button
                    variant="outline"
                    className={`rounded-full ${
                      marks.liked
                        ? 'border-[#fecaca] bg-[#fff1f2] text-[#e11d48]'
                        : 'border-[#dbe2ea] text-[#66768b]'
                    }`}
                    onClick={() => {
                      setIsLikeAnimating(true);
                      setMarks(setPaperMark(paperId, 'liked', !marks.liked));
                      window.setTimeout(() => setIsLikeAnimating(false), 400);
                    }}
                  >
                    <Heart className={`mr-1.5 h-4 w-4 ${isLikeAnimating ? 'animate-heart-beat' : ''} ${marks.liked ? 'fill-current' : ''}`} />
                    {marks.liked ? '已点赞' : '点赞'}
                  </Button>
                </div>
              </div>
            ) : null}
          </section>

          <section className="rounded-[32px] bg-white p-6 shadow-sm ring-1 ring-black/5">
            <div className="flex flex-col gap-3 border-b border-[#eef2f7] pb-4 sm:flex-row sm:items-center sm:justify-between">
              <div className="flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-[#ff9900]" />
                <div>
                  <h2 className="text-xl font-semibold text-[#172033]">AI 分析</h2>
                  {analysisStatus ? <p className="text-sm text-[#728095]">{analysisStatus}</p> : null}
                </div>
              </div>
              <Button
                variant="outline"
                className="rounded-full"
                onClick={() => void loadAnalysis(true)}
              >
                重新分析
              </Button>
            </div>

            {analysisLoading ? (
              <div className="mt-6 flex items-center gap-2 text-[#728095]">
                <Loader2 className="h-5 w-5 animate-spin" />
                {analysisStatus || '正在分析论文...'}
              </div>
            ) : analysisError ? (
              <div className="mt-6 rounded-2xl bg-[#fff1f2] p-4 text-[#b91c1c]">{analysisError}</div>
            ) : (
              <RichContent content={analysisText} className="markdown-body mt-6 text-base leading-8 text-[#334155]" />
            )}
          </section>
        </div>

        <div className="xl:sticky xl:top-6 xl:h-[calc(100vh-3rem)]">
          <ChatPanel paperId={paperId} />
        </div>
      </div>
    </div>
  );
}
