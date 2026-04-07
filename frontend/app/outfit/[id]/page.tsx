'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Image from 'next/image'
import { motion, AnimatePresence } from 'framer-motion'
import { fetchOutfit, postReaction, type OutfitItem, type ProductItem } from '@/lib/api'

/* ── 스코어 축 메타 ──────────────────────────────────── */

interface ScoreAxis {
  key: keyof Pick<OutfitItem['scores'], 'pcf' | 'of' | 'ch' | 'pe' | 'sf'>
  label: string
  fullLabel: string
  color: string
}

const AXES: ScoreAxis[] = [
  { key: 'pcf', label: 'PCF', fullLabel: '퍼스널컬러', color: 'var(--score-pcf)' },
  { key: 'of',  label: 'OF',  fullLabel: 'TPO 적합도', color: 'var(--score-of)' },
  { key: 'ch',  label: 'CH',  fullLabel: '색상 조화',  color: 'var(--score-ch)' },
  { key: 'pe',  label: 'PE',  fullLabel: '가격 효율',  color: 'var(--score-pe)' },
  { key: 'sf',  label: 'SF',  fullLabel: '스타일 핏',  color: 'var(--score-sf)' },
]

/* ── 가격 포맷 ────────────────────────────────────────── */

function formatPrice(price: number) {
  return price.toLocaleString('ko-KR') + '원'
}

/* ── 스코어 바 ────────────────────────────────────────── */

function ScoreBar({
  axis,
  value,
  index,
}: {
  axis: ScoreAxis
  value: number
  index: number
}) {
  return (
    <div className="flex items-center gap-3">
      {/* 축 라벨 */}
      <div className="flex flex-col" style={{ width: 60 }}>
        <span
          style={{
            fontFamily: 'var(--font-body)',
            fontSize: '12px',
            fontWeight: 600,
            color: axis.color,
            lineHeight: 1.4,
          }}
        >
          {axis.label}
        </span>
        <span
          style={{
            fontFamily: 'var(--font-body)',
            fontSize: '11px',
            color: 'var(--text-tertiary)',
            lineHeight: 1.3,
          }}
        >
          {axis.fullLabel}
        </span>
      </div>

      {/* 바 트랙 */}
      <div
        className="flex-1 relative"
        style={{
          height: 8,
          borderRadius: 'var(--radius-full)',
          background: 'var(--score-track)',
          overflow: 'hidden',
        }}
      >
        <motion.div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            height: '100%',
            borderRadius: 'var(--radius-full)',
            background: axis.color,
          }}
          initial={{ width: '0%' }}
          animate={{ width: `${Math.min(100, Math.round(value))}%` }}
          transition={{
            duration: 0.8,
            ease: 'easeOut',
            delay: 0.3 + index * 0.15,
          }}
        />
      </div>

      {/* 점수 */}
      <span
        style={{
          fontFamily: 'var(--font-body)',
          fontSize: '13px',
          fontWeight: 600,
          color: 'var(--text-primary)',
          width: 32,
          textAlign: 'right',
          fontVariantNumeric: 'tabular-nums',
        }}
      >
        {Math.round(value)}
      </span>
    </div>
  )
}

/* ── 아이템 썸네일 ────────────────────────────────────── */

function ItemThumbnail({
  item,
  index,
}: {
  item: ProductItem
  index: number
}) {
  return (
    <motion.a
      href={item.mall_url ?? '#'}
      target="_blank"
      rel="noopener noreferrer"
      className="flex-shrink-0 flex flex-col items-center gap-1"
      style={{ width: 80, textDecoration: 'none' }}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.2 + index * 0.08, duration: 0.3 }}
    >
      <div
        className="relative"
        style={{
          width: 80,
          height: 80,
          borderRadius: 'var(--radius-md)',
          overflow: 'hidden',
          border: '1px solid var(--border)',
          background: 'var(--border)',
        }}
      >
        {item.image_url ? (
          <Image
            src={item.image_url}
            alt={item.name ?? '아이템'}
            fill
            sizes="80px"
            className="object-cover"
            loading="lazy"
            unoptimized
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <span style={{ fontSize: '11px', color: 'var(--text-tertiary)' }}>
              N/A
            </span>
          </div>
        )}
      </div>
      <span
        className="line-clamp-1 text-center"
        style={{
          fontFamily: 'var(--font-body)',
          fontSize: '11px',
          color: 'var(--text-secondary)',
          width: 80,
          lineHeight: 1.3,
        }}
      >
        {item.category ?? item.name ?? '아이템'}
      </span>
      {item.price != null && (
        <span
          style={{
            fontFamily: 'var(--font-body)',
            fontSize: '11px',
            fontWeight: 600,
            color: 'var(--text-primary)',
            lineHeight: 1.3,
          }}
        >
          {formatPrice(item.price)}
        </span>
      )}
    </motion.a>
  )
}

/* ── 스켈레톤 ─────────────────────────────────────────── */

function DetailSkeleton() {
  return (
    <div className="flex flex-col" style={{ background: 'var(--bg)', minHeight: '100vh' }}>
      <div className="w-full animate-pulse" style={{ aspectRatio: '3/4', background: 'var(--border)' }} />
      <div className="px-5 py-5 flex flex-col gap-4">
        <div className="animate-pulse" style={{ width: '60%', height: 20, borderRadius: 4, background: 'var(--border)' }} />
        <div className="animate-pulse" style={{ width: '35%', height: 18, borderRadius: 4, background: 'var(--border)' }} />
        <div className="flex flex-col gap-3 mt-2">
          {[0, 1, 2, 3, 4].map((i) => (
            <div key={i} className="flex items-center gap-3">
              <div className="animate-pulse" style={{ width: 60, height: 14, borderRadius: 4, background: 'var(--border)' }} />
              <div className="animate-pulse flex-1" style={{ height: 8, borderRadius: 9999, background: 'var(--border)' }} />
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

/* ── 메인 페이지 ─────────────────────────────────────── */

export default function OutfitDetailPage() {
  const params = useParams()
  const router = useRouter()
  const outfitId = params.id as string

  const [outfit, setOutfit] = useState<OutfitItem | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isSaved, setIsSaved] = useState(false)

  useEffect(() => {
    const toneId = localStorage.getItem('onboarding_tone_id') || 'summer_cool_soft'
    const gender = localStorage.getItem('onboarding_gender') || 'female'
    const budgetMin = Number(localStorage.getItem('onboarding_budget_min') || '0')
    const budgetMax = Number(localStorage.getItem('onboarding_budget_max') || '300000')
    const tpoRaw = localStorage.getItem('onboarding_tpo')
    const tpo = tpoRaw ? JSON.parse(tpoRaw).join(',') : ''

    fetchOutfit({
      outfit_id: outfitId,
      tone_id: toneId,
      gender,
      budget_min: budgetMin,
      budget_max: budgetMax,
      tpo,
    })
      .then(setOutfit)
      .catch((err) => setError(err instanceof Error ? err.message : '로드 실패'))
      .finally(() => setIsLoading(false))
  }, [outfitId])

  const handleSaveToggle = () => {
    setIsSaved((prev) => !prev)
    const userId = localStorage.getItem('onboarding_user_id') || undefined
    postReaction({ user_id: userId, outfit_id: outfitId, reaction_type: 'save' }).catch(() => {})
  }

  // ── 로딩 ──
  if (isLoading) return <DetailSkeleton />

  // ── 에러 ──
  if (error || !outfit) {
    return (
      <div
        className="min-h-screen flex flex-col items-center justify-center gap-4 px-5"
        style={{ background: 'var(--bg)' }}
      >
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--error-text)" strokeWidth="1.5">
          <circle cx="12" cy="12" r="10" />
          <line x1="12" y1="8" x2="12" y2="12" />
          <line x1="12" y1="16" x2="12.01" y2="16" />
        </svg>
        <p style={{ fontFamily: 'var(--font-body)', fontSize: '15px', color: 'var(--text-secondary)' }}>
          {error ?? '코디를 찾을 수 없어요'}
        </p>
        <button
          type="button"
          onClick={() => router.back()}
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
          돌아가기
        </button>
      </div>
    )
  }

  const heroImage = outfit.items[0]?.image_url ?? ''

  return (
    <div className="min-h-screen flex flex-col" style={{ background: 'var(--bg)' }}>

      {/* ══════════════ 히어로 이미지 (풀블리드) ══════════════ */}
      <div className="relative w-full" style={{ aspectRatio: '3/4' }}>
        {heroImage ? (
          <Image
            src={heroImage}
            alt="코디 이미지"
            fill
            sizes="100vw"
            className="object-cover"
            priority
            unoptimized
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

        {/* 뒤로가기 */}
        <button
          type="button"
          aria-label="뒤로가기"
          onClick={() => router.back()}
          className="absolute top-3 left-3 flex items-center justify-center"
          style={{
            width: 36, height: 36,
            borderRadius: 'var(--radius-full)',
            background: 'rgba(34,34,34,0.4)',
            border: 'none',
            cursor: 'pointer',
          }}
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M15 18l-6-6 6-6" />
          </svg>
        </button>

        {/* 그라디언트 오버레이 (하단) */}
        <div
          className="absolute bottom-0 left-0 right-0"
          style={{
            height: 80,
            background: 'linear-gradient(transparent, rgba(248,246,243,0.9))',
            pointerEvents: 'none',
          }}
        />
      </div>

      {/* ══════════════ 콘텐츠 ══════════════ */}
      <div className="px-5 -mt-4 relative z-10 flex flex-col gap-5 pb-28">

        {/* ── 추천 이유 카드 ── */}
        <motion.div
          style={{
            background: 'var(--surface)',
            borderRadius: 'var(--radius-lg)',
            padding: '16px 20px',
          }}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, ease: 'easeOut' }}
        >
          {outfit.reasons.map((reason, i) => (
            <p
              key={i}
              style={{
                fontFamily: 'var(--font-display)',
                fontSize: '16px',
                fontWeight: 700,
                color: 'var(--text-primary)',
                lineHeight: 1.5,
                margin: i > 0 ? '4px 0 0' : 0,
              }}
            >
              {reason}
            </p>
          ))}
        </motion.div>

        {/* ── 가격 정보 ── */}
        <motion.div
          className="flex items-baseline gap-3"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.15, duration: 0.3 }}
        >
          {outfit.total_price != null && (
            <span style={{
              fontFamily: 'var(--font-body)',
              fontSize: '22px',
              fontWeight: 700,
              color: 'var(--text-primary)',
            }}>
              {formatPrice(outfit.total_price)}
            </span>
          )}
          {outfit.lowest_total_price != null && outfit.lowest_total_price !== outfit.total_price && (
            <span style={{
              fontFamily: 'var(--font-body)',
              fontSize: '14px',
              color: 'var(--accent)',
              fontWeight: 600,
            }}>
              최저가 {formatPrice(outfit.lowest_total_price)}
            </span>
          )}
        </motion.div>

        {/* ── 5축 스코어 바 차트 ── */}
        <motion.div
          className="flex flex-col gap-3"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2, duration: 0.3 }}
        >
          <p style={{
            fontFamily: 'var(--font-body)',
            fontSize: '13px',
            fontWeight: 600,
            color: 'var(--text-secondary)',
            margin: 0,
          }}>
            스코어
          </p>
          {AXES.map((axis, i) => (
            <ScoreBar
              key={axis.key}
              axis={axis}
              value={outfit.scores[axis.key]}
              index={i}
            />
          ))}
        </motion.div>

        {/* ── 아이템 캐러셀 ── */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3, duration: 0.3 }}
        >
          <p style={{
            fontFamily: 'var(--font-body)',
            fontSize: '13px',
            fontWeight: 600,
            color: 'var(--text-secondary)',
            margin: '0 0 12px',
          }}>
            아이템 {outfit.items.length}개
          </p>
          <div
            className="flex gap-3 overflow-x-auto pb-2"
            style={{ scrollbarWidth: 'none', WebkitOverflowScrolling: 'touch' }}
          >
            {outfit.items.map((item, i) => (
              <ItemThumbnail key={item.product_id} item={item} index={i} />
            ))}
          </div>
        </motion.div>
      </div>

      {/* ══════════════ 하단 CTA ══════════════ */}
      <div
        className="fixed bottom-0 left-0 right-0 z-30 flex gap-3 px-5 py-4"
        style={{
          background: 'var(--bg)',
          borderTop: '1px solid var(--border)',
        }}
      >
        {/* 저장 버튼 */}
        <motion.button
          type="button"
          onClick={handleSaveToggle}
          className="flex-1 flex items-center justify-center gap-2"
          style={{
            fontFamily: 'var(--font-body)',
            fontSize: '15px',
            fontWeight: 600,
            color: isSaved ? '#fff' : 'var(--accent)',
            background: isSaved ? 'var(--accent)' : 'transparent',
            border: `1.5px solid var(--accent)`,
            borderRadius: 'var(--radius-md)',
            padding: '12px 0',
            cursor: 'pointer',
            WebkitTapHighlightColor: 'transparent',
            transition: 'background 0.2s, color 0.2s',
          }}
          whileTap={{ scale: 0.97 }}
        >
          <svg
            width="18" height="18" viewBox="0 0 24 24"
            fill={isSaved ? '#fff' : 'none'}
            stroke={isSaved ? '#fff' : 'var(--accent)'}
            strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
          >
            <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
          </svg>
          {isSaved ? '저장됨' : '저장'}
        </motion.button>

        {/* A vs B 비교 버튼 */}
        <motion.button
          type="button"
          className="flex-1 flex items-center justify-center gap-2"
          style={{
            fontFamily: 'var(--font-body)',
            fontSize: '15px',
            fontWeight: 600,
            color: '#fff',
            background: 'var(--accent)',
            border: `1.5px solid var(--accent)`,
            borderRadius: 'var(--radius-md)',
            padding: '12px 0',
            cursor: 'pointer',
            WebkitTapHighlightColor: 'transparent',
          }}
          whileTap={{ scale: 0.97 }}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M8 3H5a2 2 0 0 0-2 2v3" />
            <path d="M21 8V5a2 2 0 0 0-2-2h-3" />
            <path d="M3 16v3a2 2 0 0 0 2 2h3" />
            <path d="M16 21h3a2 2 0 0 0 2-2v-3" />
            <line x1="12" y1="3" x2="12" y2="21" />
          </svg>
          A vs B 비교
        </motion.button>
      </div>
    </div>
  )
}
