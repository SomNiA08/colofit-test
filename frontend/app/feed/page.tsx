'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import { useRouter } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import OutfitCard from '@/components/OutfitCard'
import BottomTabBar from '@/components/BottomTabBar'
import { fetchFeed, postReaction, type OutfitItem } from '@/lib/api'

/* ── TPO 데이터 ──────────────────────────────────────── */

interface TpoOption {
  id: string
  label: string
}

const TPO_OPTIONS: TpoOption[] = [
  { id: '',          label: '전체' },
  { id: 'commute',   label: '출근' },
  { id: 'date',      label: '데이트' },
  { id: 'interview', label: '면접' },
  { id: 'weekend',   label: '주말' },
  { id: 'campus',    label: '캠퍼스' },
  { id: 'travel',    label: '여행' },
  { id: 'event',     label: '행사' },
  { id: 'workout',   label: '운동' },
]

/* ── 톤 한글 이름 ────────────────────────────────────── */

const TONE_NAME: Record<string, string> = {
  spring_warm_light:  '봄웜라이트',
  spring_warm_bright: '봄웜브라이트',
  spring_warm_mute:   '봄웜뮤트',
  summer_cool_light:  '여름쿨라이트',
  summer_cool_soft:   '여름쿨소프트',
  summer_cool_mute:   '여름쿨뮤트',
  autumn_warm_bright: '가을웜브라이트',
  autumn_warm_mute:   '가을웜뮤트',
  autumn_warm_deep:   '가을웜딥',
  winter_cool_bright: '겨울쿨브라이트',
  winter_cool_deep:   '겨울쿨딥',
  winter_cool_light:  '겨울쿨라이트',
}

/* ── 가격 포맷 ────────────────────────────────────────── */

function formatWon(value: number): string {
  if (value === 0) return '0원'
  if (value >= 10000) {
    const man = Math.floor(value / 10000)
    return `${man}만원`
  }
  return `${value.toLocaleString()}원`
}

/* ── 스켈레톤 카드 ───────────────────────────────────── */

function SkeletonCard({ index }: { index: number }) {
  return (
    <motion.div
      className="overflow-hidden"
      style={{
        borderRadius: 'var(--radius-md)',
        background: 'var(--surface)',
        border: '1px solid var(--border)',
      }}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ delay: index * 0.05 }}
    >
      <div
        className="w-full animate-pulse"
        style={{ aspectRatio: '3/4', background: 'var(--border)' }}
      />
      <div className="flex flex-col gap-2 p-3">
        <div className="flex gap-1.5">
          <div
            className="animate-pulse"
            style={{
              width: 48, height: 16,
              borderRadius: 'var(--radius-sm)',
              background: 'var(--border)',
            }}
          />
          <div
            className="animate-pulse"
            style={{
              width: 40, height: 16,
              borderRadius: 'var(--radius-sm)',
              background: 'var(--border)',
            }}
          />
        </div>
        <div
          className="animate-pulse"
          style={{
            width: '80%', height: 18,
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
      </div>
    </motion.div>
  )
}

/* ── 메인 페이지 ─────────────────────────────────────── */

export default function FeedPage() {
  const router = useRouter()

  // 온보딩 데이터 (localStorage)
  const [gender, setGender] = useState('')
  const [toneId, setToneId] = useState('')
  const [budgetMin, setBudgetMin] = useState(0)
  const [budgetMax, setBudgetMax] = useState(300000)
  const [userTpo, setUserTpo] = useState<string[]>([])

  // 피드 상태
  const [outfits, setOutfits] = useState<OutfitItem[]>([])
  const [page, setPage] = useState(1)
  const [hasNext, setHasNext] = useState(false)
  const [totalCount, setTotalCount] = useState(0)
  const [isLoading, setIsLoading] = useState(true)
  const [isLoadingMore, setIsLoadingMore] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // 필터 상태
  const [activeTpo, setActiveTpo] = useState('')
  const [budgetOpen, setBudgetOpen] = useState(false)
  const [localBudgetMin, setLocalBudgetMin] = useState(0)
  const [localBudgetMax, setLocalBudgetMax] = useState(300000)

  // 저장 상태
  const [savedIds, setSavedIds] = useState<Set<string>>(new Set())

  // 토스트
  const [toast, setToast] = useState<string | null>(null)
  const toastTimer = useRef<ReturnType<typeof setTimeout>>(null)

  // 무한 스크롤 옵저버
  const sentinelRef = useRef<HTMLDivElement>(null)
  const isLoadingRef = useRef(false)

  // ── localStorage에서 온보딩 데이터 로드 ──
  useEffect(() => {
    const g = localStorage.getItem('onboarding_gender') || 'female'
    const t = localStorage.getItem('onboarding_tone_id') || 'summer_cool_soft'
    const bMin = Number(localStorage.getItem('onboarding_budget_min') || '0')
    const bMax = Number(localStorage.getItem('onboarding_budget_max') || '300000')
    const tpoRaw = localStorage.getItem('onboarding_tpo')
    const tpo: string[] = tpoRaw ? JSON.parse(tpoRaw) : []

    setGender(g)
    setToneId(t)
    setBudgetMin(bMin)
    setBudgetMax(bMax)
    setLocalBudgetMin(bMin)
    setLocalBudgetMax(bMax)
    setUserTpo(tpo)
  }, [])

  // ── 피드 로드 ──
  const loadFeed = useCallback(
    async (pageNum: number, replace: boolean) => {
      if (!toneId || !gender) return

      if (replace) {
        setIsLoading(true)
      } else {
        setIsLoadingMore(true)
      }
      setError(null)

      try {
        const data = await fetchFeed({
          tone_id: toneId,
          gender,
          budget_min: budgetMin,
          budget_max: budgetMax,
          tpo: activeTpo,
          page: pageNum,
        })

        if (replace) {
          setOutfits(data.outfits)
        } else {
          setOutfits((prev) => [...prev, ...data.outfits])
        }
        setTotalCount(data.total_count)
        setHasNext(data.has_next)
        setPage(pageNum)
      } catch (err) {
        setError(err instanceof Error ? err.message : '피드를 불러올 수 없습니다')
      } finally {
        setIsLoading(false)
        setIsLoadingMore(false)
        isLoadingRef.current = false
      }
    },
    [toneId, gender, budgetMin, budgetMax, activeTpo],
  )

  // 초기 로드 + 필터 변경 시 리로드
  useEffect(() => {
    if (toneId && gender) {
      loadFeed(1, true)
    }
  }, [toneId, gender, budgetMin, budgetMax, activeTpo, loadFeed])

  // ── 무한 스크롤 ──
  useEffect(() => {
    const sentinel = sentinelRef.current
    if (!sentinel) return

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasNext && !isLoadingRef.current) {
          isLoadingRef.current = true
          loadFeed(page + 1, false)
        }
      },
      { rootMargin: '200px' },
    )

    observer.observe(sentinel)
    return () => observer.disconnect()
  }, [hasNext, page, loadFeed])

  // ── TPO 필터 변경 ──
  const handleTpoChange = (tpoId: string) => {
    setActiveTpo(tpoId)
  }

  // ── 예산 필터 적용 ──
  const applyBudget = () => {
    setBudgetMin(localBudgetMin)
    setBudgetMax(localBudgetMax)
    setBudgetOpen(false)
  }

  // ── 토스트 표시 ──
  const showToast = (msg: string) => {
    setToast(msg)
    if (toastTimer.current) clearTimeout(toastTimer.current)
    toastTimer.current = setTimeout(() => setToast(null), 1800)
  }

  // ── 저장 토글 (API 연동) ──
  const handleSaveToggle = (outfitId: string) => {
    const wasSaved = savedIds.has(outfitId)
    setSavedIds((prev) => {
      const next = new Set(prev)
      if (wasSaved) {
        next.delete(outfitId)
      } else {
        next.add(outfitId)
      }
      return next
    })
    const userId = localStorage.getItem('onboarding_user_id') || undefined
    postReaction({ user_id: userId, outfit_id: outfitId, reaction_type: 'save' }).catch(() => {})
  }

  // ── Dislike (스와이프 → 카드 제거 + 토스트 + API) ──
  const handleDislike = (outfitId: string) => {
    setOutfits((prev) => prev.filter((o) => o.outfit_id !== outfitId))
    setTotalCount((prev) => Math.max(0, prev - 1))
    showToast('관심없음')
    const userId = localStorage.getItem('onboarding_user_id') || undefined
    postReaction({ user_id: userId, outfit_id: outfitId, reaction_type: 'dislike' }).catch(() => {})
  }

  // ── 카드 클릭 → 상세 ──
  const handleCardClick = (outfitId: string) => {
    router.push(`/outfit/${outfitId}`)
  }

  // 오늘의 컬러핏 (피드 1번째)
  const todayPick = outfits[0] ?? null
  const feedItems = outfits.slice(1)

  return (
    <div
      className="min-h-screen flex flex-col"
      style={{ background: 'var(--bg)' }}
    >
      {/* ══════════════ 헤더 ══════════════ */}
      <header
        className="sticky top-0 z-30 flex items-center justify-between px-5 py-3"
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
          ColorFit
        </h1>

        <button
          type="button"
          aria-label="프로필"
          style={{
            width: 32, height: 32,
            borderRadius: 'var(--radius-full)',
            background: 'var(--surface)',
            border: '1px solid var(--border)',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--text-secondary)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
            <circle cx="12" cy="7" r="4" />
          </svg>
        </button>
      </header>

      {/* ══════════════ TPO 탭 필터 ══════════════ */}
      <div
        className="sticky top-[53px] z-20 overflow-x-auto"
        style={{
          background: 'var(--bg)',
          scrollbarWidth: 'none',
          WebkitOverflowScrolling: 'touch',
        }}
      >
        <div className="flex gap-2 px-5 py-3" style={{ minWidth: 'max-content' }}>
          {TPO_OPTIONS.map((opt) => {
            const isActive = activeTpo === opt.id
            return (
              <button
                key={opt.id}
                type="button"
                onClick={() => handleTpoChange(opt.id)}
                style={{
                  fontFamily: 'var(--font-body)',
                  fontSize: '13px',
                  fontWeight: isActive ? 600 : 400,
                  color: isActive ? '#fff' : 'var(--text-secondary)',
                  background: isActive ? 'var(--accent)' : 'var(--surface)',
                  border: `1px solid ${isActive ? 'var(--accent)' : 'var(--border)'}`,
                  borderRadius: 'var(--radius-full)',
                  padding: '6px 16px',
                  cursor: 'pointer',
                  whiteSpace: 'nowrap',
                  transition: 'background 0.2s, color 0.2s, border-color 0.2s',
                  WebkitTapHighlightColor: 'transparent',
                }}
              >
                {opt.label}
              </button>
            )
          })}

          {/* 예산 필터 버튼 */}
          <button
            type="button"
            onClick={() => setBudgetOpen((v) => !v)}
            style={{
              fontFamily: 'var(--font-body)',
              fontSize: '13px',
              fontWeight: budgetOpen ? 600 : 400,
              color: budgetOpen ? '#fff' : 'var(--text-secondary)',
              background: budgetOpen ? 'var(--accent)' : 'var(--surface)',
              border: `1px solid ${budgetOpen ? 'var(--accent)' : 'var(--border)'}`,
              borderRadius: 'var(--radius-full)',
              padding: '6px 16px',
              cursor: 'pointer',
              whiteSpace: 'nowrap',
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              transition: 'background 0.2s, color 0.2s, border-color 0.2s',
              WebkitTapHighlightColor: 'transparent',
            }}
          >
            {formatWon(budgetMin)}~{formatWon(budgetMax)}
            <svg
              width="12" height="12" viewBox="0 0 12 12" fill="none"
              style={{
                transform: budgetOpen ? 'rotate(180deg)' : 'rotate(0deg)',
                transition: 'transform 0.2s',
              }}
            >
              <path d="M3 4.5L6 7.5L9 4.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </button>
        </div>
      </div>

      {/* ══════════════ 예산 슬라이더 (펼침) ══════════════ */}
      <AnimatePresence>
        {budgetOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25, ease: 'easeOut' }}
            className="overflow-hidden"
            style={{
              background: 'var(--surface)',
              borderBottom: '1px solid var(--border)',
            }}
          >
            <div className="px-5 py-4 flex flex-col gap-3">
              <div className="flex justify-between">
                <span
                  style={{
                    fontFamily: 'var(--font-body)',
                    fontSize: '13px',
                    color: 'var(--text-secondary)',
                  }}
                >
                  예산 범위
                </span>
                <span
                  style={{
                    fontFamily: 'var(--font-body)',
                    fontSize: '13px',
                    fontWeight: 600,
                    color: 'var(--text-primary)',
                  }}
                >
                  {formatWon(localBudgetMin)} ~ {formatWon(localBudgetMax)}
                </span>
              </div>

              {/* 최솟값 슬라이더 */}
              <div className="flex items-center gap-3">
                <span style={{ fontFamily: 'var(--font-body)', fontSize: '11px', color: 'var(--text-tertiary)', width: 28 }}>
                  MIN
                </span>
                <input
                  type="range"
                  min={0}
                  max={300000}
                  step={5000}
                  value={localBudgetMin}
                  onChange={(e) => {
                    const v = Number(e.target.value)
                    setLocalBudgetMin(Math.min(v, localBudgetMax - 5000))
                  }}
                  className="flex-1"
                  style={{ accentColor: 'var(--accent)' }}
                />
              </div>

              {/* 최댓값 슬라이더 */}
              <div className="flex items-center gap-3">
                <span style={{ fontFamily: 'var(--font-body)', fontSize: '11px', color: 'var(--text-tertiary)', width: 28 }}>
                  MAX
                </span>
                <input
                  type="range"
                  min={0}
                  max={300000}
                  step={5000}
                  value={localBudgetMax}
                  onChange={(e) => {
                    const v = Number(e.target.value)
                    setLocalBudgetMax(Math.max(v, localBudgetMin + 5000))
                  }}
                  className="flex-1"
                  style={{ accentColor: 'var(--accent)' }}
                />
              </div>

              <button
                type="button"
                onClick={applyBudget}
                style={{
                  fontFamily: 'var(--font-body)',
                  fontSize: '14px',
                  fontWeight: 600,
                  color: '#fff',
                  background: 'var(--accent)',
                  border: 'none',
                  borderRadius: 'var(--radius-md)',
                  padding: '10px 0',
                  cursor: 'pointer',
                  WebkitTapHighlightColor: 'transparent',
                }}
              >
                적용
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ══════════════ 피드 콘텐츠 ══════════════ */}
      <main className="flex-1 px-5 pt-4 pb-24">

        {/* ── 로딩 (스켈레톤) ── */}
        {isLoading && (
          <div className="flex flex-col gap-4">
            {/* 오늘의 컬러핏 스켈레톤 */}
            <div
              className="animate-pulse"
              style={{
                width: '50%', height: 20,
                borderRadius: 'var(--radius-sm)',
                background: 'var(--border)',
                marginBottom: 4,
              }}
            />
            <SkeletonCard index={0} />
            <div
              className="animate-pulse"
              style={{
                width: '30%', height: 16,
                borderRadius: 'var(--radius-sm)',
                background: 'var(--border)',
                marginTop: 16,
              }}
            />
            <div className="grid grid-cols-2 gap-3">
              {[1, 2, 3, 4].map((i) => (
                <SkeletonCard key={i} index={i} />
              ))}
            </div>
          </div>
        )}

        {/* ── 에러 ── */}
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
              onClick={() => loadFeed(1, true)}
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

        {/* ── 빈 상태 ── */}
        {!isLoading && !error && outfits.length === 0 && (
          <motion.div
            className="flex flex-col items-center justify-center gap-4 py-20"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
          >
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--text-tertiary)" strokeWidth="1.5">
              <rect x="2" y="7" width="20" height="14" rx="2" ry="2" />
              <path d="M16 7V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2" />
            </svg>
            <p
              style={{
                fontFamily: 'var(--font-body)',
                fontSize: '15px',
                color: 'var(--text-secondary)',
                textAlign: 'center',
              }}
            >
              조건에 맞는 코디가 없어요
            </p>
            <button
              type="button"
              onClick={() => {
                setActiveTpo('')
                setBudgetMin(0)
                setBudgetMax(300000)
                setLocalBudgetMin(0)
                setLocalBudgetMax(300000)
              }}
              style={{
                fontFamily: 'var(--font-body)',
                fontSize: '14px',
                fontWeight: 600,
                color: 'var(--accent)',
                background: 'none',
                border: `1px solid var(--accent)`,
                borderRadius: 'var(--radius-md)',
                padding: '10px 24px',
                cursor: 'pointer',
              }}
            >
              필터 초기화
            </button>
          </motion.div>
        )}

        {/* ── 피드 본문 ── */}
        {!isLoading && !error && outfits.length > 0 && (
          <>
            {/* ─── 오늘의 컬러핏 ─── */}
            {todayPick && (
              <section className="mb-5">
                <motion.p
                  style={{
                    fontFamily: 'var(--font-display)',
                    fontSize: '18px',
                    fontWeight: 700,
                    color: 'var(--text-primary)',
                    margin: '0 0 8px 0',
                  }}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3 }}
                >
                  오늘의 컬러핏
                </motion.p>

                <motion.p
                  style={{
                    fontFamily: 'var(--font-body)',
                    fontSize: '13px',
                    color: 'var(--text-tertiary)',
                    margin: '0 0 12px 0',
                  }}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.1, duration: 0.3 }}
                >
                  {TONE_NAME[toneId] ?? toneId}에 딱 맞는 추천
                </motion.p>

                <OutfitCard
                  outfitId={todayPick.outfit_id}
                  items={todayPick.items}
                  totalPrice={todayPick.total_price}
                  scores={todayPick.scores}
                  reasons={todayPick.reasons}
                  index={0}
                  saved={savedIds.has(todayPick.outfit_id)}
                  onSaveToggle={handleSaveToggle}
                  onDislike={handleDislike}
                  onClick={handleCardClick}
                />
              </section>
            )}

            {/* ─── 코디 리스트 (2열 그리드) ─── */}
            {feedItems.length > 0 && (
              <section>
                <motion.p
                  style={{
                    fontFamily: 'var(--font-body)',
                    fontSize: '13px',
                    fontWeight: 500,
                    color: 'var(--text-tertiary)',
                    margin: '0 0 12px 0',
                  }}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: 0.2 }}
                >
                  {totalCount}개의 코디
                </motion.p>

                <div className="grid grid-cols-2 gap-3">
                  {feedItems.map((outfit, i) => (
                    <OutfitCard
                      key={outfit.outfit_id}
                      outfitId={outfit.outfit_id}
                      items={outfit.items}
                      totalPrice={outfit.total_price}
                      scores={outfit.scores}
                      reasons={outfit.reasons}
                      index={i + 1}
                      saved={savedIds.has(outfit.outfit_id)}
                      onSaveToggle={handleSaveToggle}
                      onDislike={handleDislike}
                      onClick={handleCardClick}
                    />
                  ))}
                </div>
              </section>
            )}

            {/* ─── 무한 스크롤 센티넬 ─── */}
            <div ref={sentinelRef} className="h-1" />

            {/* ─── 추가 로딩 ─── */}
            {isLoadingMore && (
              <div className="grid grid-cols-2 gap-3 mt-3">
                {[0, 1].map((i) => (
                  <SkeletonCard key={`more-${i}`} index={i} />
                ))}
              </div>
            )}

            {/* ─── 더 이상 없음 ─── */}
            {!hasNext && outfits.length > 0 && (
              <p
                className="text-center py-8"
                style={{
                  fontFamily: 'var(--font-body)',
                  fontSize: '13px',
                  color: 'var(--text-tertiary)',
                }}
              >
                모든 코디를 확인했어요
              </p>
            )}
          </>
        )}
      </main>

      {/* ══════════════ 하단 탭바 ══════════════ */}
      <BottomTabBar />

      {/* ══════════════ 토스트 ══════════════ */}
      <AnimatePresence>
        {toast && (
          <motion.div
            className="fixed bottom-20 left-1/2 z-50 pointer-events-none"
            style={{
              transform: 'translateX(-50%)',
            }}
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
