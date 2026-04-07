'use client'

import Image from 'next/image'
import { motion, useAnimation, AnimatePresence } from 'framer-motion'
import { useState, useRef, useCallback, useEffect } from 'react'

/* ── 타입 ─────────────────────────────────────────────── */

interface OutfitScores {
  pcf: number
  of: number
  ch: number
  pe: number
  sf: number
  total: number
}

interface OutfitItem {
  product_id: string
  name?: string | null
  image_url?: string | null
  price?: number | null
}

interface OutfitCardProps {
  outfitId: string
  items: OutfitItem[]
  totalPrice?: number | null
  scores: OutfitScores
  reasons: string[]
  designedTpo?: string | null
  index?: number
  saved?: boolean
  onSaveToggle?: (outfitId: string) => void
  onDislike?: (outfitId: string) => void
  onClick?: (outfitId: string) => void
}

/* ── 스코어 상위 2축 추출 ─────────────────────────────── */

const SCORE_LABELS: Record<string, string> = {
  pcf: 'PCF',
  of: 'OF',
  ch: 'CH',
  pe: 'PE',
  sf: 'SF',
}

const SCORE_COLORS: Record<string, string> = {
  pcf: 'var(--score-pcf)',
  of: 'var(--score-of)',
  ch: 'var(--score-ch)',
  pe: 'var(--score-pe)',
  sf: 'var(--score-sf)',
}

function getTopScores(scores: OutfitScores) {
  const entries = Object.entries(scores).filter(
    ([k]) => k !== 'total' && k !== 'total_reranked',
  )
  entries.sort((a, b) => b[1] - a[1])
  return entries.slice(0, 2)
}

/* ── 가격 포맷 ────────────────────────────────────────── */

function formatPrice(price: number) {
  return price.toLocaleString('ko-KR') + '원'
}

/* ── 하트 SVG ─────────────────────────────────────────── */

function HeartIcon({ filled }: { filled: boolean }) {
  return (
    <svg
      width="20"
      height="20"
      viewBox="0 0 24 24"
      fill={filled ? 'var(--accent)' : 'none'}
      stroke={filled ? 'var(--accent)' : '#fff'}
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
    </svg>
  )
}

/* ── 스와이프 임계값 ──────────────────────────────────── */

const SWIPE_THRESHOLD = -80

/* ── 컴포넌트 ─────────────────────────────────────────── */

export default function OutfitCard({
  outfitId,
  items,
  totalPrice,
  scores,
  reasons,
  index = 0,
  saved = false,
  onSaveToggle,
  onDislike,
  onClick,
}: OutfitCardProps) {
  const [isSaved, setIsSaved] = useState(saved)
  const [showHeartBurst, setShowHeartBurst] = useState(false)
  const controls = useAnimation()
  const heroImage = items[0]?.image_url ?? ''
  const topScores = getTopScores(scores)

  // 초기 fadeInUp 애니메이션
  useEffect(() => {
    controls.start({
      opacity: 1,
      y: 0,
      x: 0,
      transition: { duration: 0.4, ease: 'easeOut', delay: index * 0.1 },
    })
  }, [controls, index])

  // 더블탭 감지
  const lastTapRef = useRef(0)
  const isDraggingRef = useRef(false)

  // 하트 버튼 탭 → save 토글
  const handleSave = (e: React.MouseEvent) => {
    e.stopPropagation()
    const next = !isSaved
    setIsSaved(next)
    onSaveToggle?.(outfitId)
    if (next) {
      setShowHeartBurst(true)
      setTimeout(() => setShowHeartBurst(false), 600)
    }
  }

  // 더블탭 → save
  const handleTap = useCallback(() => {
    if (isDraggingRef.current) return
    const now = Date.now()
    if (now - lastTapRef.current < 300) {
      // 더블탭
      if (!isSaved) {
        setIsSaved(true)
        onSaveToggle?.(outfitId)
      }
      setShowHeartBurst(true)
      setTimeout(() => setShowHeartBurst(false), 600)
      lastTapRef.current = 0
    } else {
      lastTapRef.current = now
      // 싱글탭 딜레이 후 클릭 처리
      setTimeout(() => {
        if (lastTapRef.current === now) {
          onClick?.(outfitId)
        }
      }, 300)
    }
  }, [isSaved, outfitId, onSaveToggle, onClick])

  // 스와이프 → dislike
  const handleDragEnd = async (
    _: unknown,
    info: { offset: { x: number }; velocity: { x: number } },
  ) => {
    isDraggingRef.current = false
    if (info.offset.x < SWIPE_THRESHOLD || info.velocity.x < -500) {
      // 왼쪽으로 충분히 드래그 → slide out
      await controls.start({
        x: -400,
        opacity: 0,
        transition: { duration: 0.25, ease: 'easeIn' },
      })
      onDislike?.(outfitId)
    } else {
      // 복귀
      controls.start({
        x: 0,
        transition: { type: 'spring', stiffness: 300, damping: 30 },
      })
    }
  }

  return (
    <motion.article
      className="relative cursor-pointer overflow-hidden touch-pan-y"
      style={{
        borderRadius: 'var(--radius-md)',
        background: 'var(--surface)',
        border: '1px solid var(--border)',
      }}
      initial={{ opacity: 0, y: 30 }}
      animate={controls}
      // 스와이프
      drag="x"
      dragConstraints={{ left: 0, right: 0 }}
      dragElastic={0.15}
      onDragStart={() => { isDraggingRef.current = true }}
      onDragEnd={handleDragEnd}
      // 더블탭 + 클릭
      onClick={handleTap}
    >
      {/* ── 히어로 이미지 (3:4) ── */}
      <div className="relative w-full" style={{ aspectRatio: '3/4' }}>
        {heroImage ? (
          <Image
            src={heroImage}
            alt="코디 이미지"
            fill
            sizes="(max-width: 768px) 100vw, 50vw"
            className="object-cover"
            style={{ borderRadius: 'var(--radius-md) var(--radius-md) 0 0' }}
            loading="lazy"
            unoptimized
            draggable={false}
          />
        ) : (
          <div
            className="w-full h-full flex items-center justify-center"
            style={{ background: 'var(--border)' }}
          >
            <span
              style={{
                fontFamily: 'var(--font-body)',
                fontSize: '13px',
                color: 'var(--text-tertiary)',
              }}
            >
              이미지 없음
            </span>
          </div>
        )}

        {/* 아이템 수 뱃지 */}
        <span
          className="absolute top-2 left-2 flex items-center justify-center"
          style={{
            background: 'rgba(34,34,34,0.65)',
            color: '#fff',
            fontFamily: 'var(--font-body)',
            fontSize: '11px',
            fontWeight: 600,
            borderRadius: 'var(--radius-sm)',
            padding: '2px 8px',
            lineHeight: 1.4,
          }}
        >
          {items.length}件
        </span>

        {/* 하트 아이콘 (우상단 탭 → save 토글) */}
        <motion.button
          type="button"
          aria-label={isSaved ? '저장 취소' : '저장'}
          className="absolute top-2 right-2 flex items-center justify-center"
          style={{
            width: 32,
            height: 32,
            borderRadius: 'var(--radius-full)',
            background: 'rgba(34,34,34,0.3)',
            border: 'none',
            cursor: 'pointer',
            WebkitTapHighlightColor: 'transparent',
          }}
          onClick={handleSave}
          animate={{ scale: isSaved ? [1, 1.2, 1] : 1 }}
          transition={{ duration: 0.3, ease: 'easeOut' }}
        >
          <HeartIcon filled={isSaved} />
        </motion.button>

        {/* 더블탭 하트 뿅 애니메이션 */}
        <AnimatePresence>
          {showHeartBurst && (
            <motion.div
              className="absolute inset-0 flex items-center justify-center pointer-events-none"
              initial={{ opacity: 0, scale: 0.5 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 1.3 }}
              transition={{ duration: 0.3, ease: 'easeOut' }}
            >
              <svg
                width="64"
                height="64"
                viewBox="0 0 24 24"
                fill="var(--accent)"
                stroke="none"
              >
                <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
              </svg>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* ── 카드 하단 정보 ── */}
      <div className="flex flex-col gap-1 p-3">
        {/* 스코어 뱃지 미니 필 2개 */}
        <div className="flex gap-1.5">
          {topScores.map(([key, value]) => (
            <span
              key={key}
              style={{
                fontFamily: 'var(--font-body)',
                fontSize: '11px',
                fontWeight: 600,
                color: SCORE_COLORS[key],
                background: 'var(--bg)',
                borderRadius: 'var(--radius-sm)',
                padding: '1px 6px',
                lineHeight: 1.4,
              }}
            >
              {SCORE_LABELS[key]} {Math.round(value)}
            </span>
          ))}
        </div>

        {/* 추천 이유 1줄 */}
        {reasons[0] && (
          <p
            className="line-clamp-1"
            style={{
              fontFamily: 'var(--font-display)',
              fontSize: '16px',
              fontWeight: 700,
              color: 'var(--text-primary)',
              lineHeight: 1.3,
              margin: 0,
            }}
          >
            {reasons[0]}
          </p>
        )}

        {/* 가격 */}
        {totalPrice != null && (
          <p
            style={{
              fontFamily: 'var(--font-body)',
              fontSize: '15px',
              fontWeight: 700,
              color: 'var(--text-primary)',
              margin: 0,
              lineHeight: 1.5,
            }}
          >
            {formatPrice(totalPrice)}
          </p>
        )}
      </div>
    </motion.article>
  )
}
