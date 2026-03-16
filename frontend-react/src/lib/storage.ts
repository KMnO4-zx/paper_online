import type { PaperMark } from '@/types';

const USER_ID_KEY = 'paper_user_id';
const PAPER_MARKS_KEY = 'paperMarks';

export function getUserId(): string {
  const existing = window.localStorage.getItem(USER_ID_KEY);
  if (existing) {
    return existing;
  }

  const generated = window.crypto.randomUUID();
  window.localStorage.setItem(USER_ID_KEY, generated);
  return generated;
}

export function getPaperMarks(paperId: string): PaperMark {
  const raw = window.localStorage.getItem(PAPER_MARKS_KEY);
  if (!raw) {
    return { viewed: false, liked: false };
  }

  try {
    const parsed = JSON.parse(raw) as Record<string, PaperMark>;
    return parsed[paperId] ?? { viewed: false, liked: false };
  } catch {
    return { viewed: false, liked: false };
  }
}

export function setPaperMark(paperId: string, markType: keyof PaperMark, value: boolean): PaperMark {
  const raw = window.localStorage.getItem(PAPER_MARKS_KEY);
  const parsed = raw ? (JSON.parse(raw) as Record<string, PaperMark>) : {};
  const nextMark = {
    viewed: parsed[paperId]?.viewed ?? false,
    liked: parsed[paperId]?.liked ?? false,
    [markType]: value,
  } as PaperMark;

  if (markType === 'liked' && value) {
    nextMark.viewed = true;
  }

  parsed[paperId] = nextMark;
  window.localStorage.setItem(PAPER_MARKS_KEY, JSON.stringify(parsed));
  return nextMark;
}
