'use client'

import { useState, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import Image from 'next/image'
import { submitOnboarding } from '@/lib/api'

// ── 타입 ─────────────────────────────────────────────────────────────────────

interface StyleImage {
  id: string
  /** /public/onboarding/ 아래 실제 이미지로 교체 필요 */
  src: string
  style: string
  alt: string
}

interface Round {
  images: StyleImage[]
}

// ── 라운드 데이터 ─────────────────────────────────────────────────────────────
// src는 실제 패션 사진으로 교체 예정. 현재는 picsum 플레이스홀더 사용.

const ROUNDS: Round[] = [
  {
    images: [
      { id: 'r1_minimal',   src: 'https://picsum.photos/seed/cf_min1/400/533',   style: 'minimal',   alt: '미니멀 코디' },
      { id: 'r1_casual',    src: 'https://picsum.photos/seed/cf_cas1/400/533',   style: 'casual',    alt: '캐주얼 코디' },
      { id: 'r1_classic',   src: 'https://picsum.photos/seed/cf_cls1/400/533',   style: 'classic',   alt: '클래식 코디' },
      { id: 'r1_street',    src: 'https://picsum.photos/seed/cf_str1/400/533',   style: 'street',    alt: '스트릿 코디' },
    ],
  },
  {
    images: [
      { id: 'r2_editorial', src: 'https://picsum.photos/seed/cf_edi2/400/533',   style: 'editorial', alt: '에디토리얼 코디' },
      { id: 'r2_lovely',    src: 'https://picsum.photos/seed/cf_lov2/400/533',   style: 'lovely',    alt: '러블리 코디' },
      { id: 'r2_dandy',     src: 'https://picsum.photos/seed/cf_dan2/400/533',   style: 'dandy',     alt: '댄디 코디' },
      { id: 'r2_amekaji',   src: 'https://picsum.photos/seed/cf_ame2/400/533',   style: 'amekaji',   alt: '아메카지 코디' },
    ],
  },
  {
    images: [
      { id: 'r3_minimal',   src: 'https://picsum.photos/seed/cf_min3/400/533',   style: 'minimal',   alt: '미니멀 무드' },
      { id: 'r3_street',    src: 'https://picsum.photos/seed/cf_str3/400/533',   style: 'street',    alt: '스트릿 무드' },
      { id: 'r3_classic',   src: 'https://picsum.photos/seed/cf_cls3/400/533',   style: 'classic',   alt: '클래식 무드' },
      { id: 'r3_casual',    src: 'https://picsum.photos/seed/cf_cas3/400/533',   style: 'casual',    alt: '캐주얼 무드' },
    ],
  },
  {
    images: [
      { id: 'r4_editorial', src: 'https://picsum.photos/seed/cf_edi4/400/533',   style: 'editorial', alt: '에디토리얼 무드' },
      { id: 'r4_lovely',    src: 'https://picsum.photos/seed/cf_lov4/400/533',   style: 'lovely',    alt: '러블리 무드' },
      { id: 'r4_minimal',   src: 'https://picsum.photos/seed/cf_min4/400/533',   style: 'minimal',   alt: '미니멀 포인트' },
      { id: 'r4_classic',   src: 'https://picsum.photos/seed/cf_cls4/400/533',   style: 'classic',   alt: '클래식 포인트' },
    ],
  },
]

const TOTAL_ROUNDS = ROUNDS.length

// ── 메인 페이지 ───────────────────────────────────────────────────────────────

export default function Step5Page() {
  const router = useRouter()

  const [roundIndex, setRoundIndex]     = useState(0)
  const [selectedId, setSelectedId]     = useState<string | null>(null)
  const [visualSeeds, setVisualSeeds]   = useState<string[]>([])
  const [isTransitioning, setIsTransitioning] = useState(false)
  const [isDone, setIsDone]             = useState(false)
  const [apiError, setApiError]         = useState<string | null>(null)

  const currentRound = ROUNDS[roundIndex]

  // localStorage에서 5 Step 데이터를 모아 API 호출
  const _callOnboardingApi = useCallback(async (seeds: string[]) => {
    try {
      const gender     = (localStorage.getItem('onboarding_gender') ?? 'female') as 'female' | 'male'
      const toneId     = localStorage.getItem('onboarding_tone_id') ?? ''
      const tpo        = JSON.parse(localStorage.getItem('onboarding_tpo') ?? '[]') as string[]
      const moods      = JSON.parse(localStorage.getItem('onboarding_mood') ?? '[]') as string[]
      const budgetMin  = Number(localStorage.getItem('onboarding_budget_min') ?? 0)
      const budgetMax  = Number(localStorage.getItem('onboarding_budget_max') ?? 300000)
      const existingId = localStorage.getItem('onboarding_user_id') ?? undefined

      const result = await submitOnboarding({
        user_id: existingId,
        gender,
        tone_id: toneId,
        tpo,
        moods,
        budget_min: budgetMin,
        budget_max: budgetMax,
        visual_seeds: seeds,
      })

      localStorage.setItem('onboarding_user_id', result.user_id)
    } catch (err) {
      // API 실패해도 UX는 계속 진행. 에러 메시지만 표시.
      setApiError('프로필 저장에 실패했어요. 나중에 다시 시도할게요.')
      console.error('[onboarding] API error:', err)
    } finally {
      setIsDone(true)
    }
  }, [])

  // 라운드 진행
  const advance = useCallback((chosenStyle: string | null) => {
    setIsTransitioning(true)

    const newSeeds = chosenStyle ? [...visualSeeds, chosenStyle] : visualSeeds
    setVisualSeeds(newSeeds)

    const nextIndex = roundIndex + 1

    if (nextIndex >= TOTAL_ROUNDS) {
      // 완료 — API 전송
      localStorage.setItem('onboarding_visual_seeds', JSON.stringify(newSeeds))
      _callOnboardingApi(newSeeds)
      return
    }

    // 0.5s 후 다음 라운드 crossfade
    setTimeout(() => {
      setRoundIndex(nextIndex)
      setSelectedId(null)
      setIsTransitioning(false)
    }, 500)
  }, [roundIndex, visualSeeds])

  // 이미지 탭 → 선택 후 advance
  const handleSelect = (img: StyleImage) => {
    if (isTransitioning || selectedId) return
    setSelectedId(img.id)
    setTimeout(() => advance(img.style), 500)
  }

  // 패스
  const handlePass = () => {
    if (isTransitioning || selectedId) return
    advance(null)
  }

  // 완료 후 피드 이동
  useEffect(() => {
    if (isDone) {
      router.push('/feed')
    }
  }, [isDone, router])

  // 완료 화면 (짧게 보여주고 이동)
  if (isDone) {
    return (
      <div className="flex flex-col flex-1 items-center justify-center px-5">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.4, ease: 'easeOut' }}
          className="text-center"
        >
          <p
            style={{
              fontFamily: 'var(--font-display)',
              fontSize: '22px',
              fontWeight: 700,
              color: 'var(--text-primary)',
              marginBottom: '8px',
            }}
          >
            취향을 파악했어요
          </p>
          <p
            style={{
              fontFamily: 'var(--font-body)',
              fontSize: '15px',
              color: 'var(--text-secondary)',
            }}
          >
            나만의 코디를 찾는 중…
          </p>
          {apiError && (
            <p
              style={{
                fontFamily: 'var(--font-body)',
                fontSize: '13px',
                color: '#964F4C',
                marginTop: '12px',
              }}
            >
              {apiError}
            </p>
          )}
        </motion.div>
      </div>
    )
  }

  return (
    <div className="flex flex-col flex-1 px-5 pt-2 pb-8">

      {/* ── 헤드라인 ──────────────────────────────────── */}
      <motion.div
        className="mb-4"
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35, ease: 'easeOut' }}
      >
        <h1
          style={{
            fontFamily: 'var(--font-display)',
            fontSize: '22px',
            fontWeight: 700,
            color: 'var(--text-primary)',
            lineHeight: 1.3,
          }}
        >
          더 끌리는 스타일은?
        </h1>
        <p
          style={{
            fontFamily: 'var(--font-body)',
            fontSize: '14px',
            color: 'var(--text-secondary)',
            marginTop: '4px',
          }}
        >
          직감대로 골라보세요
        </p>
      </motion.div>

      {/* ── 라운드 인디케이터 ─────────────────────────── */}
      <div className="flex items-center gap-2 mb-4">
        {Array.from({ length: TOTAL_ROUNDS }).map((_, i) => (
          <div
            key={i}
            style={{
              width: i === roundIndex ? 20 : 6,
              height: 6,
              borderRadius: 9999,
              background: i < roundIndex
                ? 'var(--accent)'
                : i === roundIndex
                  ? 'var(--accent)'
                  : 'var(--border)',
              opacity: i > roundIndex ? 0.4 : 1,
              transition: 'width 0.3s ease, background 0.3s ease',
            }}
          />
        ))}
        <span
          style={{
            fontFamily: 'var(--font-body)',
            fontSize: '12px',
            color: 'var(--text-tertiary)',
            marginLeft: 4,
          }}
        >
          {roundIndex + 1} / {TOTAL_ROUNDS}
        </span>
      </div>

      {/* ── 2×2 이미지 그리드 ─────────────────────────── */}
      <div className="flex-1 min-h-0">
        <AnimatePresence mode="wait">
          <motion.div
            key={roundIndex}
            className="grid grid-cols-2 gap-2 h-full"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.35, ease: 'easeInOut' }}
            style={{ maxHeight: 'calc(100vh - 280px)' }}
          >
            {currentRound.images.map((img, i) => {
              const isSelected = selectedId === img.id
              const isDimmed   = selectedId !== null && !isSelected

              return (
                <motion.button
                  key={img.id}
                  type="button"
                  onClick={() => handleSelect(img)}
                  initial={{ opacity: 0, y: 16 }}
                  animate={{
                    opacity: isDimmed ? 0.35 : 1,
                    y: 0,
                    scale: isSelected ? 0.97 : 1,
                  }}
                  transition={{
                    opacity: { duration: 0.25 },
                    y: { duration: 0.3, ease: 'easeOut', delay: i * 0.04 },
                    scale: { duration: 0.2 },
                  }}
                  className="relative overflow-hidden"
                  style={{
                    borderRadius: 'var(--radius-lg)',
                    border: isSelected
                      ? '2.5px solid var(--accent)'
                      : '1.5px solid var(--border)',
                    cursor: 'pointer',
                    background: 'var(--surface)',
                    WebkitTapHighlightColor: 'transparent',
                    aspectRatio: '3 / 4',
                    padding: 0,
                  }}
                  aria-pressed={isSelected}
                  aria-label={img.alt}
                >
                  {/* 이미지 */}
                  <Image
                    src={img.src}
                    alt={img.alt}
                    fill
                    sizes="(max-width: 480px) 45vw, 200px"
                    style={{ objectFit: 'cover' }}
                    loading={i < 2 ? 'eager' : 'lazy'}
                  />

                  {/* 선택됨 오버레이 */}
                  <AnimatePresence>
                    {isSelected && (
                      <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        transition={{ duration: 0.2 }}
                        className="absolute inset-0 flex items-center justify-center"
                        style={{ background: 'rgba(150,79,76,0.18)' }}
                      >
                        <motion.div
                          initial={{ scale: 0 }}
                          animate={{ scale: 1 }}
                          transition={{ type: 'spring', stiffness: 400, damping: 20 }}
                          style={{
                            width: 40,
                            height: 40,
                            borderRadius: '50%',
                            background: 'var(--accent)',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                          }}
                        >
                          <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
                            <path
                              d="M4.5 10.5L8.5 14.5L15.5 6.5"
                              stroke="#FFFFFF"
                              strokeWidth="2"
                              strokeLinecap="round"
                              strokeLinejoin="round"
                            />
                          </svg>
                        </motion.div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </motion.button>
              )
            })}
          </motion.div>
        </AnimatePresence>
      </div>

      {/* ── 패스 링크 ────────────────────────────────── */}
      <div className="pt-5 flex justify-center">
        <button
          type="button"
          onClick={handlePass}
          disabled={isTransitioning || !!selectedId}
          style={{
            background: 'none',
            border: 'none',
            fontFamily: 'var(--font-body)',
            fontSize: '14px',
            color: 'var(--text-tertiary)',
            cursor: isTransitioning || selectedId ? 'default' : 'pointer',
            opacity: isTransitioning || selectedId ? 0.4 : 1,
            textDecoration: 'underline',
            textDecorationColor: 'var(--border)',
            textUnderlineOffset: '3px',
            transition: 'opacity 0.2s',
            padding: '8px 16px',
            WebkitTapHighlightColor: 'transparent',
          }}
        >
          잘 모르겠어요 (패스)
        </button>
      </div>

    </div>
  )
}
