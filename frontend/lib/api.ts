/**
 * ColorFit API 클라이언트.
 * NEXT_PUBLIC_API_URL 환경변수로 백엔드 베이스 URL을 지정한다.
 */

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

// ── 온보딩 ───────────────────────────────────────────────────────────────────

export interface OnboardingPayload {
  user_id?: string
  gender: 'female' | 'male'
  tone_id: string
  tpo: string[]
  moods: string[]
  budget_min: number
  budget_max: number
  visual_seeds: string[]
}

export interface OnboardingResult {
  user_id: string
}

export async function submitOnboarding(
  payload: OnboardingPayload,
): Promise<OnboardingResult> {
  const res = await fetch(`${BASE_URL}/api/onboarding`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })

  if (!res.ok) {
    const text = await res.text()
    throw new Error(`온보딩 저장 실패 (${res.status}): ${text}`)
  }

  return res.json() as Promise<OnboardingResult>
}

// ── 피드 ────────────────────────────────────────────────────────────────────

export interface ProductItem {
  product_id: string
  name?: string | null
  brand?: string | null
  category?: string | null
  color_hex?: string | null
  tone_id?: string | null
  price?: number | null
  gender?: string | null
  image_url?: string | null
  mall_url?: string | null
}

export interface OutfitScores {
  pcf: number
  of: number
  ch: number
  pe: number
  sf: number
  total: number
  total_reranked?: number | null
}

export interface OutfitItem {
  outfit_id: string
  items: ProductItem[]
  total_price?: number | null
  lowest_total_price?: number | null
  scores: OutfitScores
  reasons: string[]
  is_complete_outfit?: boolean | null
  designed_tpo?: string | null
}

export interface FeedResponse {
  outfits: OutfitItem[]
  total_count: number
  has_next: boolean
}

export interface FeedParams {
  tone_id: string
  gender: string
  budget_min?: number
  budget_max?: number
  tpo?: string
  page?: number
}

export async function fetchFeed(params: FeedParams): Promise<FeedResponse> {
  const q = new URLSearchParams({
    tone_id: params.tone_id,
    gender: params.gender,
    budget_min: String(params.budget_min ?? 0),
    budget_max: String(params.budget_max ?? 300000),
    tpo: params.tpo ?? '',
    page: String(params.page ?? 1),
  })

  const res = await fetch(`${BASE_URL}/api/feed?${q}`)

  if (!res.ok) {
    const text = await res.text()
    throw new Error(`피드 로드 실패 (${res.status}): ${text}`)
  }

  return res.json() as Promise<FeedResponse>
}

// ── 코디 상세 ───────────────────────────────────────────────────────────────

export interface OutfitDetailParams {
  outfit_id: string
  tone_id: string
  gender?: string
  budget_min?: number
  budget_max?: number
  tpo?: string
}

export async function fetchOutfit(params: OutfitDetailParams): Promise<OutfitItem> {
  const q = new URLSearchParams({
    tone_id: params.tone_id,
    gender: params.gender ?? 'female',
    budget_min: String(params.budget_min ?? 0),
    budget_max: String(params.budget_max ?? 300000),
    tpo: params.tpo ?? '',
  })

  const res = await fetch(`${BASE_URL}/api/outfit/${params.outfit_id}?${q}`)

  if (!res.ok) {
    const text = await res.text()
    throw new Error(`코디 상세 로드 실패 (${res.status}): ${text}`)
  }

  return res.json() as Promise<OutfitItem>
}

// ── 리액션 ──────────────────────────────────────────────────────────────────

export interface ReactionPayload {
  user_id?: string | null
  outfit_id: string
  reaction_type: 'save' | 'dislike'
}

export interface ReactionResult {
  id: number
  reaction_type: string
  outfit_id: string
}

export async function postReaction(
  payload: ReactionPayload,
): Promise<ReactionResult> {
  const res = await fetch(`${BASE_URL}/api/reaction`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })

  if (!res.ok) {
    const text = await res.text()
    throw new Error(`리액션 저장 실패 (${res.status}): ${text}`)
  }

  return res.json() as Promise<ReactionResult>
}
