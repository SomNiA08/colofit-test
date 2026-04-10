'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import Image from 'next/image'
import { motion, AnimatePresence } from 'framer-motion'
import BottomTabBar from '@/components/BottomTabBar'
import { fetchSaved, fetchTopPick, postReaction, type OutfitItem, type TopPickItem } from '@/lib/api'
import { useBodyScrollLock } from '@/hooks/useBodyScrollLock'

/* ── 정렬 옵션 ────────────────────────────────────────── */

type SortKey = 'recent' | 'score' | 'price'

const SORT_OPTIONS: { key: SortKey; label: string }[] = [
  { key: 'recent', label: '최근' },
  { key: 'score',  label: '점수' },
  { key: 'price',  label: '가격' },
]

/* ── 가격 포맷 ────────────────────────────────────────── */

function formatPrice(price: number): string {
  if (price >= 10000) return `${Math.floor(price / 10000)}만원`
  return `${price.toLocaleString()}원`
}

/* ── 스켈레톤 카드 ───────────────────────────────────── */

function SkeletonCard() {
  return (
    <div
      style={{
        borderRadius: 'var(--radius-md)',
        background: 'var(--surface)',
        border: '1px solid var(--border)',
        overflow: 'hidden',
      }}
    >
      <motion.div
        style={{ width: '100%', aspectRatio: '3/4', background: 'var(--border)' }}
        animate={{ opacity: [0.5, 1, 0.5] }}
        transition={{ repeat: Infinity, duration: 1.4, ease: 'easeInOut' }}
      />
      <div className="flex flex-col gap-2 p-3">
        <motion.div
          style={{ height: 14, borderRadius: 4, background: 'var(--border)', width: '70%' }}
          animate={{ opacity: [0.5, 1, 0.5] }}
          transition={{ repeat: Infinity, duration: 1.4, ease: 'easeInOut', delay: 0.1 }}
        />
        <motion.div
          style={{ height: 14, borderRadius: 4, background: 'var(--border)', width: '40%' }}
          animate={{ opacity: [0.5, 1, 0.5] }}
          transition={{ repeat: Infinity, duration: 1.4, ease: 'easeInOut', delay: 0.2 }}
        />
      </div>
    </div>
  )
}

/* ── 빈 상태 ─────────────────────────────────────────── */

function EmptyState({ onGoFeed }: { onGoFeed: () => void }) {
  return (
    <motion.div
      className="flex flex-col items-center justify-center gap-6 px-8"
      style={{ paddingTop: '80px' }}
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
    >
      {/* 일러스트 */}
      <svg width="96" height="96" viewBox="0 0 96 96" fill="none">
        <circle cx="48" cy="48" r="44" fill="var(--surface)" stroke="var(--border)" strokeWidth="1.5" />
        <path
          d="M48 62 C34 53 26 43 26 35 C26 28 31.5 23 38 23 C42 23 45.5 25 48 28 C50.5 25 54 23 58 23 C64.5 23 70 28 70 35 C70 43 62 53 48 62Z"
          fill="none"
          stroke="var(--border)"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>

      <div className="flex flex-col items-center gap-2 text-center">
        <p
          style={{
            fontFamily: 'var(--font-display)',
            fontSize: '20px',
            fontWeight: 700,
            color: 'var(--text-primary)',
            margin: 0,
          }}
        >
          아직 저장한 코디가 없어요
        </p>
        <p
          style={{
            fontFamily: 'var(--font-body)',
            fontSize: '14px',
            color: 'var(--text-secondary)',
            lineHeight: 1.6,
            margin: 0,
          }}
        >
          마음에 드는 코디 이미지를 탭해서
          <br />저장해보세요
        </p>
      </div>

      <button
        type="button"
        onClick={onGoFeed}
        style={{
          padding: '13px 32px',
          borderRadius: 'var(--radius-md)',
          background: 'var(--accent)',
          border: 'none',
          fontFamily: 'var(--font-body)',
          fontSize: '15px',
          fontWeight: 600,
          color: '#fff',
          cursor: 'pointer',
          WebkitTapHighlightColor: 'transparent',
        }}
      >
        코디 둘러보기
      </button>
    </motion.div>
  )
}

/* ── 삭제 확인 바텀시트 ──────────────────────────────── */

interface DeleteSheetProps {
  onConfirm: () => void
  onCancel: () => void
}

function DeleteSheet({ onConfirm, onCancel }: DeleteSheetProps) {
  return (
    <>
      <motion.div
        className="fixed inset-0 z-40"
        style={{ background: 'rgba(0,0,0,0.4)' }}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={onCancel}
      />
      <motion.div
        className="fixed bottom-0 z-50 flex flex-col gap-4 px-5 pt-6 pb-8"
        style={{
          left: 'var(--app-offset)',
          right: 'var(--app-offset)',
          background: 'var(--bg)',
          borderRadius: 'var(--radius-xl) var(--radius-xl) 0 0',
          borderTop: '1px solid var(--border)',
        }}
        initial={{ y: '100%' }}
        animate={{ y: 0 }}
        exit={{ y: '100%' }}
        transition={{ type: 'spring', stiffness: 300, damping: 30 }}
      >
        <div
          className="mx-auto"
          style={{
            width: 36,
            height: 4,
            borderRadius: 2,
            background: 'var(--border)',
            marginBottom: 4,
          }}
        />
        <p
          style={{
            fontFamily: 'var(--font-display)',
            fontSize: '18px',
            fontWeight: 700,
            color: 'var(--text-primary)',
            margin: 0,
          }}
        >
          저장 취소
        </p>
        <p
          style={{
            fontFamily: 'var(--font-body)',
            fontSize: '14px',
            color: 'var(--text-secondary)',
            lineHeight: 1.6,
            margin: 0,
          }}
        >
          이 코디를 저장 목록에서 삭제할까요?
        </p>
        <div className="flex gap-3">
          <button
            type="button"
            onClick={onCancel}
            style={{
              flex: 1,
              padding: '13px',
              borderRadius: 'var(--radius-md)',
              background: 'transparent',
              border: '1px solid var(--border)',
              fontFamily: 'var(--font-body)',
              fontSize: '15px',
              fontWeight: 500,
              color: 'var(--text-secondary)',
              cursor: 'pointer',
            }}
          >
            취소
          </button>
          <button
            type="button"
            onClick={onConfirm}
            style={{
              flex: 1,
              padding: '13px',
              borderRadius: 'var(--radius-md)',
              background: 'var(--error-bg)',
              border: '1px solid var(--error-border)',
              fontFamily: 'var(--font-body)',
              fontSize: '15px',
              fontWeight: 600,
              color: 'var(--error-text)',
              cursor: 'pointer',
            }}
          >
            삭제
          </button>
        </div>
      </motion.div>
    </>
  )
}

/* ── 5축 바 차트 ─────────────────────────────────────── */

const SCORE_AXES = [
  { key: 'pcf', label: '퍼스널컬러', color: '#964F4C' },
  { key: 'of',  label: 'TPO 적합도', color: '#4F97A3' },
  { key: 'ch',  label: '색상 조화',  color: '#DDB67D' },
  { key: 'pe',  label: '가격 효율',  color: '#D1933F' },
  { key: 'sf',  label: '스타일',     color: '#6B5876' },
] as const

type ScoreKey = typeof SCORE_AXES[number]['key']

interface ScoreBarProps {
  label: string
  color: string
  value: number
  delay: number
}

function ScoreBar({ label, color, value, delay }: ScoreBarProps) {
  return (
    <div className="flex items-center gap-3">
      <span
        style={{
          fontFamily: 'var(--font-body)',
          fontSize: '12px',
          color: 'var(--text-secondary)',
          width: 60,
          flexShrink: 0,
        }}
      >
        {label}
      </span>
      <div
        style={{
          flex: 1,
          height: 6,
          borderRadius: 'var(--radius-full)',
          background: 'var(--border)',
          overflow: 'hidden',
        }}
      >
        <motion.div
          style={{
            height: '100%',
            borderRadius: 'var(--radius-full)',
            background: color,
          }}
          initial={{ width: '0%' }}
          animate={{ width: `${value}%` }}
          transition={{ duration: 0.8, ease: 'easeOut', delay }}
        />
      </div>
      <span
        style={{
          fontFamily: 'var(--font-body)',
          fontSize: '12px',
          fontWeight: 600,
          color: 'var(--text-primary)',
          width: 28,
          textAlign: 'right',
          flexShrink: 0,
        }}
      >
        {Math.round(value)}
      </span>
    </div>
  )
}

/* ── Top Pick 모달 ───────────────────────────────────── */

interface TopPickModalProps {
  item: TopPickItem
  onClose: () => void
  onDetail: (outfitId: string) => void
}

function TopPickModal({ item, onClose, onDetail }: TopPickModalProps) {
  const heroImage = item.items[0]?.image_url ?? ''
  const sourceLabel = item.source === 'saved' ? '저장 코디 중 1위' : '전체 코디 중 1위'
  const reasons = item.reasons.slice(0, 3)

  return (
    <motion.div
      className="fixed inset-0 z-50 flex flex-col"
      style={{ background: 'var(--bg)' }}
      initial={{ opacity: 0, y: 40 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 40 }}
      transition={{ type: 'spring', stiffness: 300, damping: 30 }}
    >
      {/* 헤더 */}
      <div
        className="flex items-center justify-between px-5 py-4 shrink-0"
        style={{ borderBottom: '1px solid var(--border)' }}
      >
        <div className="flex flex-col gap-0.5">
          <h2
            style={{
              fontFamily: 'var(--font-display)',
              fontSize: '20px',
              fontWeight: 700,
              color: 'var(--text-primary)',
              margin: 0,
            }}
          >
            Top Pick
          </h2>
          <span
            style={{
              fontFamily: 'var(--font-body)',
              fontSize: '12px',
              color: 'var(--accent)',
              fontWeight: 600,
            }}
          >
            {sourceLabel}
          </span>
        </div>
        <button
          type="button"
          aria-label="닫기"
          onClick={onClose}
          style={{
            width: 36, height: 36,
            borderRadius: 'var(--radius-full)',
            background: 'var(--surface)',
            border: '1px solid var(--border)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            cursor: 'pointer',
          }}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--text-primary)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>
      </div>

      {/* 스크롤 영역 */}
      <div className="flex-1 overflow-y-auto pb-8">

        {/* 코디 이미지 */}
        <div className="relative w-full" style={{ aspectRatio: '3/4', maxHeight: '55vh' }}>
          {heroImage ? (
            <Image
              src={heroImage}
              alt="Top Pick 코디"
              fill
              sizes="100vw"
              className="object-cover"
              unoptimized
              priority
            />
          ) : (
            <div
              className="w-full h-full flex items-center justify-center"
              style={{ background: 'var(--border)' }}
            >
              <span style={{ fontFamily: 'var(--font-body)', fontSize: '13px', color: 'var(--text-tertiary)' }}>
                이미지 없음
              </span>
            </div>
          )}

          {/* 가격 오버레이 */}
          {item.total_price != null && (
            <div
              className="absolute bottom-3 right-3"
              style={{
                background: 'rgba(34,34,34,0.75)',
                color: '#fff',
                fontFamily: 'var(--font-body)',
                fontSize: '14px',
                fontWeight: 700,
                borderRadius: 'var(--radius-sm)',
                padding: '4px 10px',
              }}
            >
              {item.total_price >= 10000
                ? `${Math.floor(item.total_price / 10000)}만원`
                : `${item.total_price.toLocaleString()}원`}
            </div>
          )}
        </div>

        <div className="flex flex-col gap-5 px-5 pt-5">

          {/* 추천 이유 */}
          {reasons.length > 0 && (
            <motion.div
              className="flex flex-col gap-2"
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.15, duration: 0.3 }}
            >
              <p
                style={{
                  fontFamily: 'var(--font-body)',
                  fontSize: '12px',
                  fontWeight: 600,
                  color: 'var(--text-secondary)',
                  margin: 0,
                  textTransform: 'uppercase',
                  letterSpacing: '0.05em',
                }}
              >
                추천 이유
              </p>
              {reasons.map((reason, i) => (
                <div key={i} className="flex items-start gap-2">
                  <span
                    style={{
                      width: 20,
                      height: 20,
                      borderRadius: 'var(--radius-full)',
                      background: 'var(--accent)',
                      color: '#fff',
                      fontFamily: 'var(--font-body)',
                      fontSize: '11px',
                      fontWeight: 700,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      flexShrink: 0,
                      marginTop: 1,
                    }}
                  >
                    {i + 1}
                  </span>
                  <p
                    style={{
                      fontFamily: 'var(--font-body)',
                      fontSize: '14px',
                      color: 'var(--text-primary)',
                      lineHeight: 1.6,
                      margin: 0,
                    }}
                  >
                    {reason}
                  </p>
                </div>
              ))}
            </motion.div>
          )}

          {/* 5축 바 차트 */}
          <motion.div
            className="flex flex-col gap-3"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.25, duration: 0.3 }}
          >
            <p
              style={{
                fontFamily: 'var(--font-body)',
                fontSize: '12px',
                fontWeight: 600,
                color: 'var(--text-secondary)',
                margin: 0,
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
              }}
            >
              점수 분석
            </p>
            {SCORE_AXES.map((axis, i) => (
              <ScoreBar
                key={axis.key}
                label={axis.label}
                color={axis.color}
                value={item.scores[axis.key as ScoreKey]}
                delay={0.3 + i * 0.08}
              />
            ))}
          </motion.div>

          {/* 자세히 보기 버튼 */}
          <motion.button
            type="button"
            onClick={() => onDetail(item.outfit_id)}
            style={{
              width: '100%',
              padding: '14px',
              borderRadius: 'var(--radius-md)',
              background: 'var(--accent)',
              border: 'none',
              fontFamily: 'var(--font-body)',
              fontSize: '15px',
              fontWeight: 600,
              color: '#fff',
              cursor: 'pointer',
              WebkitTapHighlightColor: 'transparent',
            }}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.45 }}
          >
            자세히 보기
          </motion.button>
        </div>
      </div>
    </motion.div>
  )
}

/* ── 저장 그리드 카드 ────────────────────────────────── */

interface SavedCardProps {
  outfit: OutfitItem
  onLongPress: (outfitId: string) => void
  onClick: (outfitId: string) => void
  index: number
}

function SavedCard({ outfit, onLongPress, onClick, index }: SavedCardProps) {
  const longPressTimer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const didLongPress = useRef(false)
  const heroImage = outfit.items[0]?.image_url ?? ''

  const handlePointerDown = useCallback(() => {
    didLongPress.current = false
    longPressTimer.current = setTimeout(() => {
      didLongPress.current = true
      onLongPress(outfit.outfit_id)
    }, 600)
  }, [outfit.outfit_id, onLongPress])

  const handlePointerUp = useCallback(() => {
    if (longPressTimer.current) {
      clearTimeout(longPressTimer.current)
      longPressTimer.current = null
    }
  }, [])

  const handleClick = useCallback(() => {
    if (!didLongPress.current) {
      onClick(outfit.outfit_id)
    }
  }, [outfit.outfit_id, onClick])

  return (
    <motion.article
      className="cursor-pointer overflow-hidden"
      style={{
        borderRadius: 'var(--radius-md)',
        background: 'var(--surface)',
        border: '1px solid var(--border)',
      }}
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05, duration: 0.3 }}
      onPointerDown={handlePointerDown}
      onPointerUp={handlePointerUp}
      onPointerLeave={handlePointerUp}
      onClick={handleClick}
    >
      {/* 이미지 (3:4) */}
      <div className="relative w-full" style={{ aspectRatio: '3/4' }}>
        {heroImage ? (
          <Image
            src={heroImage}
            alt="저장 코디"
            fill
            sizes="(max-width: 768px) 50vw, 25vw"
            className="object-cover"
            style={{ borderRadius: 'var(--radius-md) var(--radius-md) 0 0' }}
            loading="lazy"
            unoptimized
            draggable={false}
          />
        ) : (
          <div
            className="w-full h-full flex items-center justify-center"
            style={{
              background: 'var(--border)',
              borderRadius: 'var(--radius-md) var(--radius-md) 0 0',
            }}
          >
            <span style={{ fontFamily: 'var(--font-body)', fontSize: '11px', color: 'var(--text-tertiary)' }}>
              이미지 없음
            </span>
          </div>
        )}

        {/* 아이템 수 뱃지 */}
        <span
          className="absolute top-1.5 left-1.5"
          style={{
            background: 'rgba(34,34,34,0.65)',
            color: '#fff',
            fontFamily: 'var(--font-body)',
            fontSize: '10px',
            fontWeight: 600,
            borderRadius: 'var(--radius-sm)',
            padding: '1px 6px',
          }}
        >
          {outfit.items.length}件
        </span>
      </div>

      {/* 카드 하단 */}
      <div className="flex flex-col gap-0.5 p-2.5">
        {outfit.reasons[0] && (
          <p
            className="line-clamp-1"
            style={{
              fontFamily: 'var(--font-display)',
              fontSize: '13px',
              fontWeight: 700,
              color: 'var(--text-primary)',
              margin: 0,
              lineHeight: 1.3,
            }}
          >
            {outfit.reasons[0]}
          </p>
        )}
        {outfit.total_price != null && (
          <p
            style={{
              fontFamily: 'var(--font-body)',
              fontSize: '13px',
              fontWeight: 600,
              color: 'var(--text-secondary)',
              margin: 0,
            }}
          >
            {formatPrice(outfit.total_price)}
          </p>
        )}
      </div>
    </motion.article>
  )
}

/* ── 메인 페이지 ─────────────────────────────────────── */

export default function SavedPage() {
  const router = useRouter()

  const [outfits, setOutfits] = useState<OutfitItem[]>([])
  const [sort, setSort] = useState<SortKey>('recent')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null)
  useBodyScrollLock(deleteTarget !== null)
  const [topPick, setTopPick] = useState<TopPickItem | null>(null)
  const [showTopPick, setShowTopPick] = useState(false)
  const [topPickLoading, setTopPickLoading] = useState(false)
  const [compareMode, setCompareMode] = useState(false)
  const [compareSelected, setCompareSelected] = useState<string[]>([])

  // localStorage에서 사용자 정보 로드
  const getUserParams = () => ({
    userId: localStorage.getItem('onboarding_user_id') ?? '',
    toneId: localStorage.getItem('onboarding_tone_id') ?? '',
    gender: localStorage.getItem('onboarding_gender') ?? 'female',
    budgetMin: Number(localStorage.getItem('onboarding_budget_min') ?? 0),
    budgetMax: Number(localStorage.getItem('onboarding_budget_max') ?? 300000),
    tpo: localStorage.getItem('onboarding_tpo') ?? '',
  })

  const load = useCallback(async (sortKey: SortKey) => {
    const { userId, toneId, gender, budgetMin, budgetMax, tpo } = getUserParams()
    // 로그인 게이트: JWT 없고 user_id도 없으면 로그인 유도
    const hasToken = !!localStorage.getItem('auth_token')
    if (!userId || !toneId) {
      setLoading(false)
      if (!hasToken) router.push('/login')
      return
    }
    setLoading(true)
    setError(null)
    try {
      const data = await fetchSaved({
        user_id: userId,
        tone_id: toneId,
        gender,
        budget_min: budgetMin,
        budget_max: budgetMax,
        tpo,
        sort: sortKey,
      })
      setOutfits(data.outfits)
    } catch {
      setError('저장 목록을 불러오지 못했어요.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load(sort)
  }, [sort, load])

  const handleSortChange = (key: SortKey) => {
    if (key !== sort) setSort(key)
  }

  // 롱프레스 → 삭제 시트
  const handleLongPress = useCallback((outfitId: string) => {
    setDeleteTarget(outfitId)
  }, [])

  // 삭제 확인
  const handleDeleteConfirm = async () => {
    if (!deleteTarget) return
    const { userId } = getUserParams()
    setOutfits(prev => prev.filter(o => o.outfit_id !== deleteTarget))
    setDeleteTarget(null)
    if (userId) {
      await postReaction({ user_id: userId, outfit_id: deleteTarget, reaction_type: 'save' }).catch(() => {})
    }
  }

  // Top Pick 열기
  const handleTopPickOpen = async () => {
    setTopPickLoading(true)
    const { userId, toneId, gender, budgetMin, budgetMax, tpo } = getUserParams()
    try {
      const data = await fetchTopPick({
        tone_id: toneId,
        gender,
        budget_min: budgetMin,
        budget_max: budgetMax,
        tpo,
        user_id: userId || undefined,
      })
      setTopPick(data)
      setShowTopPick(true)
    } catch {
      // Top Pick 없음 — 무시
    } finally {
      setTopPickLoading(false)
    }
  }

  // 비교 모드 카드 탭
  const handleCompareTap = useCallback((outfitId: string) => {
    setCompareSelected(prev => {
      if (prev.includes(outfitId)) return prev.filter(id => id !== outfitId)
      if (prev.length >= 2) return prev
      return [...prev, outfitId]
    })
  }, [])

  // 비교하기 실행
  const handleCompareGo = useCallback(() => {
    if (compareSelected.length < 2) return
    const { toneId, gender, budgetMin, budgetMax, tpo } = getUserParams()
    const q = new URLSearchParams({
      ids: compareSelected.join(','),
      tone_id: toneId,
      gender,
      budget_min: String(budgetMin),
      budget_max: String(budgetMax),
      tpo,
    })
    router.push(`/compare?${q}`)
  }, [compareSelected, router])

  const handleCardClick = useCallback((outfitId: string) => {
    const { toneId, gender, budgetMin, budgetMax, tpo } = getUserParams()
    const q = new URLSearchParams({
      tone_id: toneId,
      gender,
      budget_min: String(budgetMin),
      budget_max: String(budgetMax),
      tpo,
    })
    router.push(`/outfit/${outfitId}?${q}`)
  }, [router])

  return (
    <div className="min-h-screen flex flex-col" style={{ background: 'var(--bg)' }}>

      {/* ══════════════ 헤더 ══════════════ */}
      <header
        className="sticky top-0 z-30 flex items-center justify-between px-5 py-4"
        style={{ background: 'var(--bg)', borderBottom: '1px solid var(--border)' }}
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
          저장
        </h1>
        {outfits.length > 0 && (
          <div className="flex items-center gap-2">
            {/* 비교 모드 토글 */}
            <button
              type="button"
              onClick={() => { setCompareMode(m => !m); setCompareSelected([]) }}
              style={{
                display: 'flex', alignItems: 'center', gap: 5,
                padding: '7px 14px',
                borderRadius: 'var(--radius-full)',
                background: compareMode ? 'var(--surface)' : 'transparent',
                border: '1px solid var(--border)',
                fontFamily: 'var(--font-body)',
                fontSize: '13px',
                fontWeight: compareMode ? 700 : 500,
                color: compareMode ? 'var(--text-primary)' : 'var(--text-secondary)',
                cursor: 'pointer',
                WebkitTapHighlightColor: 'transparent',
              }}
            >
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <line x1="18" y1="20" x2="18" y2="10" /><line x1="12" y1="20" x2="12" y2="4" /><line x1="6" y1="20" x2="6" y2="14" />
              </svg>
              {compareMode ? '취소' : '비교'}
            </button>

            {/* Top Pick 버튼 */}
            <button
              type="button"
              onClick={handleTopPickOpen}
              disabled={topPickLoading}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              padding: '7px 14px',
              borderRadius: 'var(--radius-full)',
              background: topPickLoading ? 'var(--surface)' : 'var(--accent)',
              border: 'none',
              fontFamily: 'var(--font-body)',
              fontSize: '13px',
              fontWeight: 600,
              color: topPickLoading ? 'var(--text-tertiary)' : '#fff',
              cursor: topPickLoading ? 'default' : 'pointer',
              WebkitTapHighlightColor: 'transparent',
              transition: 'background 0.15s',
            }}
          >
            {topPickLoading ? (
              <motion.span
                animate={{ rotate: 360 }}
                transition={{ repeat: Infinity, duration: 0.8, ease: 'linear' }}
                style={{ display: 'flex' }}
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
                  <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
                </svg>
              </motion.span>
            ) : (
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
              </svg>
            )}
            Top Pick
            </button>
          </div>
        )}
      </header>

      <div className="flex flex-col gap-4 px-4 pt-4 pb-28">

        {/* ══════════════ 정렬 드롭다운 ══════════════ */}
        {!loading && outfits.length > 0 && (
          <motion.div
            className="flex gap-2"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.2 }}
          >
            {SORT_OPTIONS.map(opt => (
              <button
                key={opt.key}
                type="button"
                onClick={() => handleSortChange(opt.key)}
                style={{
                  padding: '6px 14px',
                  borderRadius: 'var(--radius-full)',
                  background: sort === opt.key ? 'var(--accent)' : 'var(--surface)',
                  border: sort === opt.key ? 'none' : '1px solid var(--border)',
                  fontFamily: 'var(--font-body)',
                  fontSize: '13px',
                  fontWeight: sort === opt.key ? 600 : 500,
                  color: sort === opt.key ? '#fff' : 'var(--text-secondary)',
                  cursor: 'pointer',
                  WebkitTapHighlightColor: 'transparent',
                  transition: 'background 0.15s, color 0.15s',
                }}
              >
                {opt.label}
              </button>
            ))}
          </motion.div>
        )}

        {/* ══════════════ 콘텐츠 ══════════════ */}

        {/* 로딩 스켈레톤 */}
        {loading && (
          <div className="grid grid-cols-2 gap-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <SkeletonCard key={i} />
            ))}
          </div>
        )}

        {/* 에러 */}
        {!loading && error && (
          <div className="flex flex-col items-center gap-4 pt-16">
            <p style={{ fontFamily: 'var(--font-body)', fontSize: '14px', color: 'var(--text-secondary)' }}>
              {error}
            </p>
            <button
              type="button"
              onClick={() => load(sort)}
              style={{
                padding: '10px 24px',
                borderRadius: 'var(--radius-md)',
                background: 'var(--surface)',
                border: '1px solid var(--border)',
                fontFamily: 'var(--font-body)',
                fontSize: '14px',
                color: 'var(--text-primary)',
                cursor: 'pointer',
              }}
            >
              다시 시도
            </button>
          </div>
        )}

        {/* 빈 상태 */}
        {!loading && !error && outfits.length === 0 && (
          <EmptyState onGoFeed={() => router.push('/feed')} />
        )}

        {/* 비교 모드 안내 */}
        {compareMode && (
          <motion.p
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            style={{
              fontFamily: 'var(--font-body)',
              fontSize: '13px',
              color: 'var(--text-secondary)',
              margin: 0,
              textAlign: 'center',
            }}
          >
            비교할 코디 2개를 선택해주세요 ({compareSelected.length}/2)
          </motion.p>
        )}

        {/* 2열 그리드 */}
        {!loading && !error && outfits.length > 0 && (
          <div className="grid grid-cols-2 gap-3">
            {outfits.map((outfit, i) => {
              const isSelected = compareSelected.includes(outfit.outfit_id)
              return (
                <div
                  key={outfit.outfit_id}
                  style={{ position: 'relative' }}
                  onClick={compareMode ? () => handleCompareTap(outfit.outfit_id) : undefined}
                >
                  {/* 비교 모드 선택 오버레이 */}
                  {compareMode && (
                    <div
                      style={{
                        position: 'absolute', inset: 0, zIndex: 10,
                        borderRadius: 'var(--radius-md)',
                        border: isSelected ? '2.5px solid var(--accent)' : '2px dashed var(--border)',
                        background: isSelected ? 'rgba(150,79,76,0.08)' : 'transparent',
                        pointerEvents: 'none',
                      }}
                    />
                  )}
                  {compareMode && isSelected && (
                    <div
                      style={{
                        position: 'absolute', top: 8, right: 8, zIndex: 11,
                        width: 22, height: 22,
                        borderRadius: 'var(--radius-full)',
                        background: 'var(--accent)',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        pointerEvents: 'none',
                      }}
                    >
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                        <polyline points="20 6 9 17 4 12" />
                      </svg>
                    </div>
                  )}
                  <SavedCard
                    outfit={outfit}
                    index={i}
                    onLongPress={compareMode ? () => {} : handleLongPress}
                    onClick={compareMode ? () => handleCompareTap(outfit.outfit_id) : handleCardClick}
                  />
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* ══════════════ 비교하기 플로팅 CTA ══════════════ */}
      <AnimatePresence>
        {compareMode && compareSelected.length === 2 && (
          <motion.div
            className="fixed bottom-20 left-4 right-4 z-40"
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 16 }}
            transition={{ type: 'spring', stiffness: 350, damping: 28 }}
          >
            <button
              type="button"
              onClick={handleCompareGo}
              style={{
                width: '100%',
                padding: '15px',
                borderRadius: 'var(--radius-md)',
                background: 'var(--accent)',
                border: 'none',
                fontFamily: 'var(--font-body)',
                fontSize: '16px',
                fontWeight: 700,
                color: '#fff',
                cursor: 'pointer',
                WebkitTapHighlightColor: 'transparent',
                boxShadow: '0 4px 20px rgba(150,79,76,0.35)',
              }}
            >
              선택한 2개 비교하기
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ══════════════ 삭제 확인 바텀시트 ══════════════ */}
      <AnimatePresence>
        {deleteTarget && (
          <DeleteSheet
            onConfirm={handleDeleteConfirm}
            onCancel={() => setDeleteTarget(null)}
          />
        )}
      </AnimatePresence>

      {/* ══════════════ Top Pick 모달 ══════════════ */}
      <AnimatePresence>
        {showTopPick && topPick && (
          <TopPickModal
            item={topPick}
            onClose={() => setShowTopPick(false)}
            onDetail={(outfitId) => {
              setShowTopPick(false)
              handleCardClick(outfitId)
            }}
          />
        )}
      </AnimatePresence>

      <BottomTabBar />
    </div>
  )
}
