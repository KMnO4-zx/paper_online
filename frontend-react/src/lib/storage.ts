import type { PaperMark } from '@/types';

const USER_ID_KEY = 'paper_user_id';
const PAPER_MARKS_KEY = 'paperMarks';
const EMPTY_MARK: PaperMark = { viewed: false, liked: false, favorited: false };

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
    return { ...EMPTY_MARK };
  }

  try {
    const parsed = JSON.parse(raw) as Record<string, PaperMark>;
    return { ...EMPTY_MARK, ...parsed[paperId] };
  } catch {
    return { ...EMPTY_MARK };
  }
}

export function getAllPaperMarks(): Record<string, PaperMark> {
  const raw = window.localStorage.getItem(PAPER_MARKS_KEY);
  if (!raw) {
    return {};
  }

  try {
    return JSON.parse(raw) as Record<string, PaperMark>;
  } catch {
    return {};
  }
}

export function clearPaperMarks(): void {
  window.localStorage.removeItem(PAPER_MARKS_KEY);
}

export function setPaperMark(paperId: string, markType: keyof PaperMark, value: boolean): PaperMark {
  const raw = window.localStorage.getItem(PAPER_MARKS_KEY);
  const parsed = raw ? (JSON.parse(raw) as Record<string, PaperMark>) : {};
  const nextMark = {
    viewed: parsed[paperId]?.viewed ?? false,
    liked: parsed[paperId]?.liked ?? false,
    favorited: parsed[paperId]?.favorited ?? false,
    [markType]: value,
  } as PaperMark;

  if ((markType === 'liked' || markType === 'favorited') && value) {
    nextMark.viewed = true;
  }
  if (markType === 'viewed' && !value) {
    nextMark.liked = false;
    nextMark.favorited = false;
  }

  parsed[paperId] = nextMark;
  window.localStorage.setItem(PAPER_MARKS_KEY, JSON.stringify(parsed));
  return nextMark;
}
