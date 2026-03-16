export interface Paper {
  id: string;
  title: string;
  conference?: string;
  conferenceType?: 'Oral' | 'Poster' | 'Spotlight' | '';
  keywords: string[];
  abstract: string;
  venue?: string | null;
  primary_area?: string | null;
  authors?: string[];
  pdf?: string | null;
  llm_response?: string | null;
  openReviewUrl?: string;
  pdfUrl?: string;
  hasSeen?: boolean;
  isLiked?: boolean;
}

export interface Conference {
  id: string;
  name: string;
  fullName: string;
  year: number;
  paperCount?: number;
}

export interface ConferenceDefinition extends Conference {
  accentClass: string;
}

export type ConferenceSlug = 'iclr_2026' | 'neurips_2025' | 'icml_2025';

export interface ChatMessage {
  id?: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp?: Date;
  created_at?: string;
}

export interface SearchFilters {
  title: boolean;
  abstract: boolean;
  keywords: boolean;
}

export interface PaperListResponse {
  papers: Paper[];
  total: number;
  page: number;
  pages: number;
}

export interface ChatSessionSummary {
  id: string;
  user_id?: string;
  paper_id?: string;
  title: string | null;
  created_at: string;
}

export interface OnlineCount {
  count: number;
}

export interface PaperMark {
  viewed: boolean;
  liked: boolean;
}
