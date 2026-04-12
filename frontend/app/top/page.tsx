'use client'

import { useState, useEffect, useRef } from 'react'
import { useRouter } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import OutfitCard from '@/components/OutfitCard'
import BottomTabBar from '@/components/BottomTabBar'
import { fetchTopPick, postReaction, type TopPickItem } from '@/lib/api'

/* ── TPO 한글 이름 ──────────────────────────────────────── */

const TPO_LABEL: Record<string, string> = {
  commute:   '출근',
  date:      '데이트',
  interview: '면접',
  weekend:   '주말',
  campus:    '캠퍼스',
  travel:    '여행',
  event:     '행사',
  workout:   '운동',
}

/* ── 스켈레톤 ──────────────────────────────────────────── */

function Skeleton() {
  return (
    <div className="flex flex-col gap-4">
      <div
        className="animate-pulse"
        style={{
          width: '55%', height: 22,
          borderRadius: 'var(--radius-sm)',
          background: 'var(--border)',
        }}
      />
      <div
        className="animate-pulse"
        style={{
          width: '40%', height: 16,
          borderRadius: 'var(--radius-sm)',
          background: 'var(--border)',
        }}
      />
      <motion.div
        className="overflow-hidden"
        style={{
          borderRadius: 'var(--radius-md)',
          background: 'var(--surface)',
          border: '1px solid var(--border)',
        }}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
      >
        <div
          className="w-full animate-pulse"
          style={{ aspectRatio: '3/4', background: 'var(--border)' }}
        />
        <div className="flex flex-col gap-2 p-3">
          <div className="flex gap-1.5">
            <div className="animate-pulse" style={{ width: 48, height: 16, borderRadius: 'var(--radius-sm)', background: 'var(--border)' }} />
            <div className="animate-pulse" style={{ width: 40, height: 16, borderRadius: 'var(--radius-sm)', background: 'var(--border)' }} />
          </div>
          <div className="animate-pulse" style={{ width: '80%', height: 18, borderRadius: 'var(--radius-sm)', background: 'var(--border)' }} />
          <div className="animate-pulse" style={{ width: '40%', height: 16, borderRadius: 'var(--radius-sm)', background: 'var(--border)' }} />
        </div>
      </motion.div>
    </div>
  )
}

/* ── 메인 페이지 ─────────────────────────────────────────── */

export default function TopPage() {
  const router = useRouter()

  const [pick, setPick] = useState<TopPickItem | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [saved, setSaved] = useState(false)

  // 토스트
  const [toast, setToast] = useState<string | null>(null)
  const toastTimer = useRef<ReturnType<typeof setTimeout>>(null)

  const showToast = (msg: string) => {
    setToast(msg)
    if (toastTimer.current) clearTimeout(toastTimer.current)
    toastTimer.current = setTimeout(() => setToast(null), 1800)
  }

  useEffect(() => {
    const toneId   = localStorage.getItem('onboarding_tone_id')   || 'summer_cool_soft'
    const gender   = localStorage.getItem('onboarding_gender')     || 'female'
    const budgetMin = Number(localStorage.getItem('onboarding_budget_min')  || '0')
    const budgetMax = Number(localStorage.getItem('onboarding_budget_max')  || '300000')
    const tpoRaw   = localStorage.getItem('onboarding_tpo')
    const tpo      = tpoRaw ? (JSON.parse(tpoRaw) as string[])[0] ?? '' : ''
    const userId   = localStorage.getItem('onboarding_user_id') ?? undefined

    setIsLoading(true)
    setError(null)

    fetchTopPick({ tone_id: toneId, gender, budget_min: budgetMin, budget_max: budgetMax, tpo, user_id: userId })
      .then((data) => {
        setPick(data)
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : 'Top Pick을 불러올 수 없습니다')
      })
      .finally(() => {
        setIsLoading(false)
      })
  }, [])

  const handleSaveToggle = (outfitId: string) => {
    setSaved((prev) => !prev)
    const userId = localStorage.getItem('onboarding_user_id') ?? undefined
    postReaction({ user_id: userId, outfit_id: outfitId, reaction_type: 'save' }).catch(() => {})
    showToast(saved ? '저장 취소' : '저장됨')
  }

  const handleCardClick = (outfitId: string) => {
    router.push(`/outfit/${outfitId}`)
  }

  const handleRetry = () => {
    const toneId    = localStorage.getItem('onboarding_tone_id')   || 'summer_cool_soft'
    const gender    = localStorage.getItem('onboarding_gender')     || 'female'
    const budgetMin = Number(localStorage.getItem('onboarding_budget_min')  || '0')
    const budgetMax = Number(localStorage.getItem('onboarding_budget_max')  || '300000')
    const tpoRaw    = localStorage.getItem('onboarding_tpo')
    const tpo       = tpoRaw ? (JSON.parse(tpoRaw) as string[])[0] ?? '' : ''
    const userId    = localStorage.getItem('onboarding_user_id') ?? undefined

    setIsLoading(true)
    setError(null)
    setPick(null)

    fetchTopPick({ tone_id: toneId, gender, budget_min: budgetMin, budget_max: budgetMax, tpo, user_id: userId })
      .then((data) => { setPick(data) })
      .catch((err) => { setError(err instanceof Error ? err.message : 'Top Pick을 불러올 수 없습니다') })
      .finally(() => { setIsLoading(false) })
  }

  return (
    <div
      className="min-h-screen flex flex-col"
      style={{ background: 'var(--bg)' }}
    >
      {/* ══ 헤더 ══ */}
      <header
        className="sticky top-0 z-30 flex items-center px-5 py-3"
        style={{
          background: 'var(--bg)',
          borderBottom: '1px solid var(--border)',
        }}
      >
        <h1
          style={{
            fontFamily: 'var(--font-display)',
            fontSize: '22px',
            fontWeight: 700,
            color: 'var(--text-primary)',
            margin: 0,
          }}
        >
          Top Pick
        </h1>
      </header>

      {/* ══ 콘텐츠 ══ */}
      <main className="flex-1 px-5 pt-5 pb-24">

        {/* 로딩 */}
        {isLoading && <Skeleton />}

        {/* 에러 */}
        {!isLoading && error && (
          <motion.div
            className="flex flex-col items-center justify-center gap-4 py-20"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
          >
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--error-text)" strokeWidth="1.5">
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
            <p
              style={{
                fontFamily: 'var(--font-body)',
                fontSize: '15px',
                color: 'var(--text-secondary)',
                textAlign: 'center',
              }}
            >
              {error}
            </p>
            <button
              type="button"
              onClick={handleRetry}
              style={{
                fontFamily: 'var(--font-body)',
                fontSize: '14px',
                fontWeight: 600,
                color: '#fff',
                background: 'var(--accent)',
                border: 'none',
                borderRadius: 'var(--radius-md)',
                padding: '10px 24px',
                cursor: 'pointer',
              }}
            >
              다시 시도
            </button>
          </motion.div>
        )}

        {/* 결과 */}
        {!isLoading && !error && pick && (
          <>
            <motion.p
              style={{
                fontFamily: 'var(--font-display)',
                fontSize: '18px',
                fontWeight: 700,
                color: 'var(--text-primary)',
                margin: '0 0 4px 0',
              }}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
            >
              지금 당신에게 딱 맞는 코디
            </motion.p>

            <motion.p
              style={{
                fontFamily: 'var(--font-body)',
                fontSize: '13px',
                color: 'var(--text-tertiary)',
                margin: '0 0 16px 0',
              }}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.1, duration: 0.3 }}
            >
              {pick.source === 'saved' ? '저장한 코디 기반' : '전체 코디 기반'}
              {pick.inferred_tpo ? ` · ${TPO_LABEL[pick.inferred_tpo] ?? pick.inferred_tpo}` : ''}
            </motion.p>

            <OutfitCard
              outfitId={pick.outfit_id}
              items={pick.items}
              totalPrice={pick.total_price}
              scores={pick.scores}
              reasons={pick.reasons}
              designedTpo={pick.designed_tpo}
              index={0}
              saved={saved}
              onSaveToggle={handleSaveToggle}
              onClick={handleCardClick}
            />
          </>
        )}
      </main>

      <BottomTabBar />

      {/* ══ 토스트 ══ */}
      <AnimatePresence>
        {toast && (
          <motion.div
            className="fixed bottom-20 left-1/2 z-50 pointer-events-none"
            style={{ transform: 'translateX(-50%)' }}
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 8 }}
            transition={{ duration: 0.25, ease: 'easeOut' }}
          >
            <div
              style={{
                fontFamily: 'var(--font-body)',
                fontSize: '14px',
                fontWeight: 500,
                color: '#fff',
                background: 'rgba(34,34,34,0.8)',
                borderRadius: 'var(--radius-full)',
                padding: '8px 20px',
                whiteSpace: 'nowrap',
              }}
            >
              {toast}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
