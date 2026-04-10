'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Image from 'next/image'
import { motion } from 'framer-motion'
import {
  fetchItem,
  fetchSimilarItems,
  type ItemDetail,
  type PriceEntry,
  type SimilarProduct,
} from '@/lib/api'
import PurchaseFeedbackSheet from '@/components/PurchaseFeedbackSheet'

/* ── 가격 포맷 ────────────────────────────────────────── */

function formatPrice(price: number) {
  return price.toLocaleString('ko-KR') + '원'
}

/* ── 스켈레톤 ─────────────────────────────────────────── */

function ItemSkeleton() {
  return (
    <div className="flex flex-col" style={{ background: 'var(--bg)', minHeight: '100vh' }}>
      {/* 이미지 */}
      <div
        className="w-full animate-pulse"
        style={{ aspectRatio: '1/1', background: 'var(--border)' }}
      />
      <div className="px-5 py-5 flex flex-col gap-4">
        {/* 브랜드 + 상품명 */}
        <div className="animate-pulse" style={{ width: '30%', height: 14, borderRadius: 4, background: 'var(--border)' }} />
        <div className="animate-pulse" style={{ width: '70%', height: 20, borderRadius: 4, background: 'var(--border)' }} />
        <div className="animate-pulse" style={{ width: '25%', height: 22, borderRadius: 4, background: 'var(--border)' }} />
        {/* 테이블 */}
        <div className="flex flex-col gap-2 mt-2">
          {[0, 1, 2].map((i) => (
            <div key={i} className="animate-pulse" style={{ height: 44, borderRadius: 8, background: 'var(--border)' }} />
          ))}
        </div>
      </div>
    </div>
  )
}

/* ── 가격 비교 테이블 행 ──────────────────────────────── */

function PriceRow({
  entry,
  isLowest,
  index,
  onExternalClick,
}: {
  entry: PriceEntry
  isLowest: boolean
  index: number
  onExternalClick?: () => void
}) {
  return (
    <motion.a
      href={entry.mall_url ?? '#'}
      target="_blank"
      rel="noopener noreferrer"
      aria-label={`${entry.mall_name ?? '쇼핑몰'}에서 보기`}
      onClick={onExternalClick}
      className="flex items-center gap-3 px-4 py-3"
      style={{
        background: isLowest ? 'var(--surface)' : 'transparent',
        borderRadius: 'var(--radius-md)',
        border: isLowest ? '1px solid var(--border)' : '1px solid transparent',
        textDecoration: 'none',
        cursor: 'pointer',
        WebkitTapHighlightColor: 'transparent',
      }}
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.1 + index * 0.06, duration: 0.3 }}
      whileTap={{ opacity: 0.7 }}
    >
      {/* 판매처 */}
      <span
        className="flex-1 truncate"
        style={{
          fontFamily: 'var(--font-body)',
          fontSize: '14px',
          color: 'var(--text-primary)',
          fontWeight: isLowest ? 600 : 400,
        }}
      >
        {entry.mall_name ?? '쇼핑몰'}
      </span>

      {/* 가격 */}
      <span
        style={{
          fontFamily: 'var(--font-body)',
          fontSize: '14px',
          fontWeight: 700,
          color: isLowest ? 'var(--accent)' : 'var(--text-primary)',
          fontVariantNumeric: 'tabular-nums',
          minWidth: 80,
          textAlign: 'right',
        }}
      >
        {entry.price != null ? formatPrice(entry.price) : '-'}
      </span>

      {/* 유형 뱃지 */}
      {isLowest ? (
        <span
          style={{
            fontFamily: 'var(--font-body)',
            fontSize: '11px',
            fontWeight: 600,
            color: '#fff',
            background: 'var(--accent)',
            borderRadius: 'var(--radius-sm)',
            padding: '2px 8px',
            whiteSpace: 'nowrap',
          }}
        >
          최저가
        </span>
      ) : (
        <span
          style={{
            fontFamily: 'var(--font-body)',
            fontSize: '11px',
            color: 'var(--text-tertiary)',
            borderRadius: 'var(--radius-sm)',
            padding: '2px 8px',
            border: '1px solid var(--border)',
            whiteSpace: 'nowrap',
          }}
        >
          {entry.match_type === 'base' ? '기본가' : 'Exact'}
        </span>
      )}

      {/* 바로가기 아이콘 (시각 표시용) */}
      <span
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          width: 28,
          height: 28,
          borderRadius: 'var(--radius-sm)',
          background: 'var(--border)',
          color: 'var(--text-secondary)',
          flexShrink: 0,
        }}
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
          <polyline points="15 3 21 3 21 9" />
          <line x1="10" y1="14" x2="21" y2="3" />
        </svg>
      </span>
    </motion.a>
  )
}

/* ── 유사 상품 카드 ───────────────────────────────────── */

function SimilarCard({
  item,
  index,
}: {
  item: SimilarProduct
  index: number
}) {
  const router = useRouter()

  return (
    <motion.button
      type="button"
      className="flex flex-col overflow-hidden text-left"
      style={{
        background: 'var(--surface)',
        borderRadius: 'var(--radius-md)',
        border: '1px solid var(--border)',
        cursor: 'pointer',
        WebkitTapHighlightColor: 'transparent',
      }}
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.2 + index * 0.07, duration: 0.3 }}
      whileTap={{ scale: 0.98 }}
      onClick={() => router.push(`/item/${item.product_id}`)}
    >
      {/* 이미지 (1:1) */}
      <div className="relative w-full" style={{ aspectRatio: '1/1', background: 'var(--border)' }}>
        {item.image_url ? (
          <Image
            src={item.image_url}
            alt={item.name ?? '상품'}
            fill
            sizes="(max-width: 768px) 50vw, 25vw"
            className="object-cover"
            loading="lazy"
            unoptimized
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <span style={{ fontSize: '11px', color: 'var(--text-tertiary)' }}>이미지 없음</span>
          </div>
        )}

        {/* 유사도 % 뱃지 */}
        <span
          className="absolute top-2 left-2"
          style={{
            fontFamily: 'var(--font-body)',
            fontSize: '11px',
            fontWeight: 600,
            color: '#fff',
            background: item.match_type === 'exact' ? 'var(--accent)' : 'rgba(34,34,34,0.65)',
            borderRadius: 'var(--radius-sm)',
            padding: '2px 7px',
            lineHeight: 1.4,
          }}
        >
          {item.match_type === 'exact' ? 'Exact' : `${item.similarity_pct}%`}
        </span>
      </div>

      {/* 정보 */}
      <div className="flex flex-col gap-0.5 p-3">
        {item.brand && (
          <span
            style={{
              fontFamily: 'var(--font-body)',
              fontSize: '11px',
              color: 'var(--text-tertiary)',
              lineHeight: 1.4,
            }}
          >
            {item.brand}
          </span>
        )}
        <span
          className="line-clamp-2"
          style={{
            fontFamily: 'var(--font-body)',
            fontSize: '13px',
            color: 'var(--text-primary)',
            lineHeight: 1.4,
          }}
        >
          {item.name ?? '상품명 없음'}
        </span>
        {item.price != null && (
          <span
            style={{
              fontFamily: 'var(--font-body)',
              fontSize: '14px',
              fontWeight: 700,
              color: 'var(--text-primary)',
              marginTop: 2,
            }}
          >
            {formatPrice(item.price)}
          </span>
        )}
      </div>
    </motion.button>
  )
}

/* ── 메인 페이지 ─────────────────────────────────────── */

export default function ItemDetailPage() {
  const params = useParams()
  const router = useRouter()
  const productId = params.id as string

  const [item, setItem] = useState<ItemDetail | null>(null)
  const [similar, setSimilar] = useState<SimilarProduct[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [feedbackVisible, setFeedbackVisible] = useState(false)
  const [feedbackOutfitId, setFeedbackOutfitId] = useState('')

  const PENDING_KEY = 'colorfit_pending_feedback'

  // URL 쿼리에서 outfitId 추출
  useEffect(() => {
    const outfitId = new URLSearchParams(window.location.search).get('outfitId') ?? ''
    setFeedbackOutfitId(outfitId)
  }, [])

  // 외부 링크 클릭 시 sessionStorage에 기록
  function handleExternalLinkClick() {
    if (!feedbackOutfitId) return
    sessionStorage.setItem(
      PENDING_KEY,
      JSON.stringify({ outfitId: feedbackOutfitId, clickedAt: Date.now() }),
    )
  }

  // 복귀 감지 → 피드백 시트 표시
  useEffect(() => {
    function onVisibilityChange() {
      if (document.visibilityState !== 'visible') return
      const raw = sessionStorage.getItem(PENDING_KEY)
      if (!raw) return
      try {
        const { outfitId: pendingId, clickedAt } = JSON.parse(raw) as {
          outfitId: string
          clickedAt: number
        }
        const isRecent = Date.now() - clickedAt < 30 * 60 * 1000
        if (pendingId === feedbackOutfitId && isRecent) {
          sessionStorage.removeItem(PENDING_KEY)
          setFeedbackVisible(true)
        }
      } catch {
        sessionStorage.removeItem(PENDING_KEY)
      }
    }
    document.addEventListener('visibilitychange', onVisibilityChange)
    return () => document.removeEventListener('visibilitychange', onVisibilityChange)
  }, [feedbackOutfitId])

  useEffect(() => {
    Promise.all([
      fetchItem(productId),
      fetchSimilarItems(productId, 6),
    ])
      .then(([itemData, similarData]) => {
        setItem(itemData)
        setSimilar(similarData.items)
      })
      .catch((err) => setError(err instanceof Error ? err.message : '로드 실패'))
      .finally(() => setIsLoading(false))
  }, [productId])

  // ── 로딩 ──
  if (isLoading) return <ItemSkeleton />

  // ── 에러 ──
  if (error || !item) {
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
        <p style={{ fontFamily: 'var(--font-body)', fontSize: '15px', color: 'var(--text-secondary)', textAlign: 'center' }}>
          {error ?? '아이템을 찾을 수 없어요'}
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
            border: '1px solid var(--accent)',
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

  // 최저가 찾기 (가격 있는 항목 중 최소)
  const pricedEntries = item.price_comparison.filter((e) => e.price != null)
  const lowestPrice = pricedEntries.length > 0
    ? Math.min(...pricedEntries.map((e) => e.price!))
    : null
  const lowestEntry = pricedEntries.find((e) => e.price === lowestPrice) ?? null

  return (
    <div className="min-h-screen flex flex-col" style={{ background: 'var(--bg)' }}>

      {/* ══════════════ 헤더 (뒤로가기) ══════════════ */}
      <div
        className="sticky top-0 z-30 flex items-center gap-3 px-4 py-3"
        style={{
          background: 'var(--bg)',
          borderBottom: '1px solid var(--border)',
        }}
      >
        <button
          type="button"
          aria-label="뒤로가기"
          onClick={() => router.back()}
          style={{
            width: 36, height: 36,
            borderRadius: 'var(--radius-full)',
            background: 'var(--surface)',
            border: '1px solid var(--border)',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0,
          }}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--text-primary)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M15 18l-6-6 6-6" />
          </svg>
        </button>
        <span
          className="truncate"
          style={{
            fontFamily: 'var(--font-body)',
            fontSize: '15px',
            fontWeight: 600,
            color: 'var(--text-primary)',
          }}
        >
          {item.name ?? '아이템 상세'}
        </span>
      </div>

      {/* ══════════════ 아이템 이미지 (1:1) ══════════════ */}
      <motion.div
        className="relative w-full"
        style={{ aspectRatio: '1/1', background: 'var(--border)' }}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.4 }}
      >
        {item.image_url ? (
          <Image
            src={item.image_url}
            alt={item.name ?? '아이템'}
            fill
            sizes="100vw"
            className="object-cover"
            priority
            unoptimized
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <span style={{ fontFamily: 'var(--font-body)', fontSize: '13px', color: 'var(--text-tertiary)' }}>
              이미지 없음
            </span>
          </div>
        )}
      </motion.div>

      {/* ══════════════ 콘텐츠 ══════════════ */}
      <div className="flex flex-col gap-6 px-5 pt-5 pb-28">

        {/* ── 브랜드 + 상품명 + 가격 ── */}
        <motion.div
          className="flex flex-col gap-1"
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35, ease: 'easeOut' }}
        >
          {item.brand && (
            <span
              style={{
                fontFamily: 'var(--font-body)',
                fontSize: '13px',
                color: 'var(--text-tertiary)',
                letterSpacing: '0.02em',
              }}
            >
              {item.brand}
            </span>
          )}
          <h1
            style={{
              fontFamily: 'var(--font-display)',
              fontSize: '20px',
              fontWeight: 700,
              color: 'var(--text-primary)',
              lineHeight: 1.3,
              margin: 0,
            }}
          >
            {item.name ?? '상품명 없음'}
          </h1>
          {item.price != null && (
            <span
              style={{
                fontFamily: 'var(--font-body)',
                fontSize: '22px',
                fontWeight: 700,
                color: 'var(--text-primary)',
                marginTop: 4,
                fontVariantNumeric: 'tabular-nums',
              }}
            >
              {formatPrice(item.price)}
            </span>
          )}
        </motion.div>

        {/* ── 가격 비교 테이블 ── */}
        {item.price_comparison.length > 0 && (
          <motion.div
            className="flex flex-col gap-2"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.15, duration: 0.3 }}
          >
            <p
              style={{
                fontFamily: 'var(--font-body)',
                fontSize: '13px',
                fontWeight: 600,
                color: 'var(--text-secondary)',
                margin: '0 0 4px',
              }}
            >
              가격 비교
            </p>
            {item.price_comparison.map((entry, i) => (
              <PriceRow
                key={entry.product_id}
                entry={entry}
                isLowest={lowestEntry?.product_id === entry.product_id}
                index={i}
                onExternalClick={handleExternalLinkClick}
              />
            ))}
          </motion.div>
        )}

        {/* ── 유사 상품 ── */}
        {similar.length > 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.25, duration: 0.3 }}
          >
            <p
              style={{
                fontFamily: 'var(--font-body)',
                fontSize: '13px',
                fontWeight: 600,
                color: 'var(--text-secondary)',
                margin: '0 0 12px',
              }}
            >
              비슷한 상품
            </p>
            <div className="grid grid-cols-2 gap-3">
              {similar.map((s, i) => (
                <SimilarCard key={s.product_id} item={s} index={i} />
              ))}
            </div>
          </motion.div>
        )}
      </div>

      {/* ══════════════ 하단 CTA ══════════════ */}
      <div
        className="fixed bottom-0 z-30 px-5 py-4"
        style={{
          left: 'var(--app-offset)',
          right: 'var(--app-offset)',
          background: 'var(--bg)',
          borderTop: '1px solid var(--border)',
          paddingBottom: 'calc(16px + env(safe-area-inset-bottom, 0px))',
        }}
      >
        <motion.a
          href={lowestEntry?.mall_url ?? item.mall_url ?? '#'}
          target="_blank"
          rel="noopener noreferrer"
          onClick={handleExternalLinkClick}
          className="flex items-center justify-center gap-2 w-full"
          style={{
            fontFamily: 'var(--font-body)',
            fontSize: '15px',
            fontWeight: 600,
            color: '#fff',
            background: 'var(--accent)',
            borderRadius: 'var(--radius-md)',
            padding: '13px 0',
            textDecoration: 'none',
            cursor: 'pointer',
          }}
          whileTap={{ scale: 0.97 }}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
            <polyline points="15 3 21 3 21 9" />
            <line x1="10" y1="14" x2="21" y2="3" />
          </svg>
          최저가 쇼핑몰에서 보기
        </motion.a>
      </div>

      {/* 구매 후 피드백 바텀시트 (outfitId가 있을 때만 활성) */}
      {feedbackOutfitId && (
        <PurchaseFeedbackSheet
          outfitId={feedbackOutfitId}
          visible={feedbackVisible}
          onClose={() => setFeedbackVisible(false)}
        />
      )}
    </div>
  )
}
