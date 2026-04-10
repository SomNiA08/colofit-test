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

// ── 아이템 상세 ─────────────────────────────────────────────────────────────

export interface PriceEntry {
  product_id: string
  mall_name?: string | null
  mall_url?: string | null
  price?: number | null
  match_type: 'base' | 'exact'
}

export interface ItemDetail {
  product_id: string
  name?: string | null
  brand?: string | null
  category?: string | null
  color_hex?: string | null
  tone_id?: string | null
  price?: number | null
  mall_name?: string | null
  mall_url?: string | null
  image_url?: string | null
  gender?: string | null
  price_comparison: PriceEntry[]
}

export async function fetchItem(productId: string): Promise<ItemDetail> {
  const res = await fetch(`${BASE_URL}/api/item/${productId}`)

  if (!res.ok) {
    const text = await res.text()
    throw new Error(`아이템 로드 실패 (${res.status}): ${text}`)
  }

  return res.json() as Promise<ItemDetail>
}

// ── 유사 상품 ────────────────────────────────────────────────────────────────

export interface SimilarProduct {
  product_id: string
  name?: string | null
  brand?: string | null
  category?: string | null
  color_hex?: string | null
  price?: number | null
  image_url?: string | null
  mall_url?: string | null
  mall_name?: string | null
  similarity: number
  similarity_pct: number
  match_type: 'exact' | 'similar'
}

export interface SimilarResponse {
  base_product_id: string
  items: SimilarProduct[]
}

export async function fetchSimilarItems(
  productId: string,
  topN = 5,
): Promise<SimilarResponse> {
  const res = await fetch(
    `${BASE_URL}/api/item/${productId}/similar?top_n=${topN}`,
  )

  if (!res.ok) {
    const text = await res.text()
    throw new Error(`유사 상품 로드 실패 (${res.status}): ${text}`)
  }

  return res.json() as Promise<SimilarResponse>
}

// ── 톤 상세 ─────────────────────────────────────────────────────────────────

export interface ToneSwatch {
  hex: string
  name: string
}

export interface ToneSampleOutfit {
  outfit_id: string
  image_url?: string | null
  total_price?: number | null
  designed_tpo?: string | null
}

export interface ToneDetail {
  tone_id: string
  name: string
  gradient: string
  description: string
  good_colors: ToneSwatch[]
  avoid_colors: ToneSwatch[]
  sample_outfits: ToneSampleOutfit[]
}

export async function fetchTone(toneId: string): Promise<ToneDetail> {
  const res = await fetch(`${BASE_URL}/api/tone/${toneId}`)

  if (!res.ok) {
    const text = await res.text()
    throw new Error(`톤 정보 로드 실패 (${res.status}): ${text}`)
  }

  return res.json() as Promise<ToneDetail>
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

export async function fetchReactionCount(userId: string): Promise<number> {
  if (!userId) return 0
  const res = await fetch(
    `${BASE_URL}/api/reaction/count?user_id=${encodeURIComponent(userId)}`,
  )
  if (!res.ok) return 0
  const data = await res.json() as { count: number }
  return data.count
}

export async function deleteReactions(userId: string): Promise<number> {
  if (!userId) return 0
  const res = await fetch(
    `${BASE_URL}/api/reaction?user_id=${encodeURIComponent(userId)}`,
    { method: 'DELETE' },
  )
  if (!res.ok) return 0
  const data = await res.json() as { deleted: number }
  return data.deleted
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

// ── 저장 목록 ────────────────────────────────────────────────────────────────

export interface SavedParams {
  user_id: string
  tone_id: string
  gender: string
  budget_min?: number
  budget_max?: number
  tpo?: string
  sort?: 'recent' | 'score' | 'price'
}

export interface SavedResponse {
  outfits: OutfitItem[]
  total_count: number
}

// ── Top Pick ─────────────────────────────────────────────────────────────────

export interface TopPickItem extends OutfitItem {
  source: 'saved' | 'global'
  inferred_tpo: string
}

export interface TopPickParams {
  tone_id: string
  gender: string
  budget_min?: number
  budget_max?: number
  tpo?: string
  user_id?: string
}

export async function fetchTopPick(params: TopPickParams): Promise<TopPickItem> {
  const q = new URLSearchParams({
    tone_id: params.tone_id,
    gender: params.gender,
    budget_min: String(params.budget_min ?? 0),
    budget_max: String(params.budget_max ?? 300000),
    tpo: params.tpo ?? '',
  })
  if (params.user_id) q.set('user_id', params.user_id)
  const res = await fetch(`${BASE_URL}/api/top-pick?${q}`)
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`Top Pick 로드 실패 (${res.status}): ${text}`)
  }
  return res.json() as Promise<TopPickItem>
}

// ── A vs B 비교 ──────────────────────────────────────────────────────────────

export interface CompareResult {
  outfit_a: OutfitItem
  outfit_b: OutfitItem
  winner: 'a' | 'b' | 'tie'
  decisive_axis: 'pcf' | 'of' | 'ch' | 'pe' | 'sf' | null
  score_a: number
  score_b: number
  axis_diffs: Record<string, number>  // 양수 = A가 높음
  conclusion: string
}

export interface CompareParams {
  ids: string          // 콤마 구분 ID 2개
  tone_id: string
  gender: string
  budget_min?: number
  budget_max?: number
  tpo?: string
}

export async function fetchCompare(params: CompareParams): Promise<CompareResult> {
  const q = new URLSearchParams({
    ids: params.ids,
    tone_id: params.tone_id,
    gender: params.gender,
    budget_min: String(params.budget_min ?? 0),
    budget_max: String(params.budget_max ?? 300000),
    tpo: params.tpo ?? '',
  })
  const res = await fetch(`${BASE_URL}/api/compare?${q}`)
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`비교 로드 실패 (${res.status}): ${text}`)
  }
  return res.json() as Promise<CompareResult>
}

export async function fetchSaved(params: SavedParams): Promise<SavedResponse> {
  const q = new URLSearchParams({
    user_id: params.user_id,
    tone_id: params.tone_id,
    gender: params.gender,
    budget_min: String(params.budget_min ?? 0),
    budget_max: String(params.budget_max ?? 300000),
    tpo: params.tpo ?? '',
    sort: params.sort ?? 'recent',
  })
  const res = await fetch(`${BASE_URL}/api/saved?${q}`)
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`저장 목록 로드 실패 (${res.status}): ${text}`)
  }
  return res.json() as Promise<SavedResponse>
}

// ── 피드백 개인화 ─────────────────────────────────────────────────────────────

export interface FeedbackPayload {
  outfit_id: string
  event_type: 'save' | 'like' | 'click' | 'dislike'
}

export interface FeedbackResult {
  ok: boolean
  feedback_count: number
  has_overrides: boolean
}

export async function postFeedback(
  payload: FeedbackPayload,
  authToken: string,
): Promise<FeedbackResult> {
  const res = await fetch(`${BASE_URL}/api/feedback`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${authToken}`,
    },
    body: JSON.stringify(payload),
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`피드백 전송 실패 (${res.status}): ${text}`)
  }
  return res.json() as Promise<FeedbackResult>
}
