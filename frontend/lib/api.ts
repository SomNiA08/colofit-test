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
