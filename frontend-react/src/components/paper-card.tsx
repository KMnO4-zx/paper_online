import { Eye, ExternalLink, FileText, Heart } from 'lucide-react';
import { useState } from 'react';

import { RichContent } from '@/components/rich-content';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { getVenueParts, normalizeKeywords } from '@/lib/content';
import { getPaperMarks, setPaperMark } from '@/lib/storage';
import type { Paper } from '@/types';

interface PaperCardProps {
  paper: Paper;
  index: number;
  onOpen: (paper: Paper) => void;
}

function getConferenceColor(conference: string) {
  switch (conference) {
    case 'ICLR':
      return 'bg-blue-50 text-blue-700 border-blue-200';
    case 'NeurIPS':
      return 'bg-violet-50 text-violet-700 border-violet-200';
    case 'ICML':
      return 'bg-emerald-50 text-emerald-700 border-emerald-200';
    default:
      return 'bg-slate-100 text-slate-700 border-slate-200';
  }
}

function getKeywordColor(index: number) {
  const colors = [
    'bg-orange-50 text-orange-700 border-orange-100',
    'bg-sky-50 text-sky-700 border-sky-100',
    'bg-emerald-50 text-emerald-700 border-emerald-100',
    'bg-violet-50 text-violet-700 border-violet-100',
    'bg-rose-50 text-rose-700 border-rose-100',
  ];
  return colors[index % colors.length];
}

export function PaperCard({ paper, index, onOpen }: PaperCardProps) {
  const [marks, setMarks] = useState(() => getPaperMarks(paper.id));
  const [isLikeAnimating, setIsLikeAnimating] = useState(false);
  const keywords = normalizeKeywords(paper.keywords).slice(0, 6);
  const venue = getVenueParts(paper.venue);
  const openReviewUrl = `https://openreview.net/forum?id=${paper.id}`;
  const pdfUrl = paper.pdf || `https://openreview.net/pdf?id=${paper.id}`;

  return (
    <article
      onClick={() => onOpen(paper)}
      className="group cursor-pointer rounded-3xl bg-white/95 p-5 shadow-sm ring-1 ring-black/5 transition duration-300 hover:-translate-y-1 hover:shadow-xl"
      style={{ animationDelay: `${index * 0.04}s` }}
    >
      <div className="mb-4 flex flex-wrap items-start gap-2">
        <Badge variant="outline" className={getConferenceColor(venue.conference)}>
          {venue.label}
        </Badge>
        {paper.primary_area ? (
          <Badge variant="outline" className="border-[#e6ebf2] bg-[#f8fafc] text-[#516072]">
            {paper.primary_area}
          </Badge>
        ) : null}
      </div>

      <h3 className="mb-3 text-xl font-semibold leading-snug text-[#1f2937] transition-colors group-hover:text-[#ff7a00]">
        <RichContent content={paper.title} inline className="paper-title-math" />
      </h3>

      {keywords.length ? (
        <div className="mb-4 flex flex-wrap gap-2">
          {keywords.map((keyword, keywordIndex) => (
            <span
              key={`${paper.id}-${keyword}`}
              className={`rounded-full border px-2.5 py-1 text-xs ${getKeywordColor(keywordIndex)}`}
            >
              {keyword}
            </span>
          ))}
        </div>
      ) : null}

      <p className="mb-5 line-clamp-3 text-sm leading-6 text-[#67758a]">
        {paper.abstract || '暂无摘要'}
      </p>

      <div className="flex flex-wrap items-center gap-2">
        <a
          href={openReviewUrl}
          target="_blank"
          rel="noreferrer"
          onClick={(event) => event.stopPropagation()}
        >
          <Button variant="outline" size="sm" className="rounded-full border-[#f3d597] bg-[#fff7df] text-[#c77b00]">
            <ExternalLink className="mr-1.5 h-3.5 w-3.5" />
            OpenReview
          </Button>
        </a>

        <a
          href={pdfUrl}
          target="_blank"
          rel="noreferrer"
          onClick={(event) => event.stopPropagation()}
        >
          <Button variant="outline" size="sm" className="rounded-full border-[#bfdbfe] bg-[#eff6ff] text-[#2563eb]">
            <FileText className="mr-1.5 h-3.5 w-3.5" />
            PDF
          </Button>
        </a>

        <div className="ml-auto flex flex-wrap gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={(event) => {
              event.stopPropagation();
              setMarks(setPaperMark(paper.id, 'viewed', !marks.viewed));
            }}
            className={`rounded-full ${
              marks.viewed
                ? 'border-[#bfdbfe] bg-[#eff6ff] text-[#2563eb]'
                : 'border-[#dbe2ea] text-[#66768b]'
            }`}
          >
            <Eye className={`mr-1.5 h-3.5 w-3.5 ${marks.viewed ? 'fill-current' : ''}`} />
            {marks.viewed ? '已看过' : '看过'}
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={(event) => {
              event.stopPropagation();
              setIsLikeAnimating(true);
              setMarks(setPaperMark(paper.id, 'liked', !marks.liked));
              window.setTimeout(() => setIsLikeAnimating(false), 400);
            }}
            className={`rounded-full ${
              marks.liked
                ? 'border-[#fecaca] bg-[#fff1f2] text-[#e11d48]'
                : 'border-[#dbe2ea] text-[#66768b]'
            }`}
          >
            <Heart className={`mr-1.5 h-3.5 w-3.5 ${isLikeAnimating ? 'animate-heart-beat' : ''} ${marks.liked ? 'fill-current' : ''}`} />
            {marks.liked ? '已点赞' : '点赞'}
          </Button>
        </div>
      </div>
    </article>
  );
}
