'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Image from 'next/image'
import { motion, AnimatePresence } from 'framer-motion'
import { fetchTone, type ToneDetail, type ToneSwatch, type ToneSampleOutfit } from '@/lib/api'

/* ── 가격 포맷 ────────────────────────────────────────── */

function formatPrice(price: number) {
  if (price >= 10000) return `${Math.floor(price / 10000)}만원`
  return `${price.toLocaleString()}원`
}

/* ── TPO 한글 ─────────────────────────────────────────── */

const TPO_LABEL: Record<string, string> = {
  commute: '출근', date: '데이트', interview: '면접',
  weekend: '주말', campus: '캠퍼스', travel: '여행',
  event: '행사', workout: '운동',
}

/* ── 색상 스와치 칩 ───────────────────────────────────── */

function SwatchChip({
  color,
  avoid,
  index,
}: {
  color: ToneSwatch
  avoid?: boolean
  index: number
}) {
  return (
    <motion.div
      className="flex flex-col items-center gap-1.5 flex-shrink-0"
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ delay: 0.3 + index * 0.05, duration: 0.25 }}
    >
      <div className="relative" style={{ width: 44, height: 44 }}>
        <div
          style={{
            width: 44,
            height: 44,
            borderRadius: '50%',
            background: color.hex,
            border: '1.5px solid rgba(0,0,0,0.08)',
          }}
        />
        {avoid && (
          <div
            className="absolute inset-0 flex items-center justify-center"
            style={{ borderRadius: '50%', background: 'rgba(0,0,0,0.35)' }}
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <line x1="4" y1="4" x2="12" y2="12" stroke="white" strokeWidth="2" strokeLinecap="round" />
              <line x1="12" y1="4" x2="4" y2="12" stroke="white" strokeWidth="2" strokeLinecap="round" />
            </svg>
          </div>
        )}
      </div>
      <span
        style={{
          fontFamily: 'var(--font-body)',
          fontSize: '10px',
          color: 'var(--text-tertiary)',
          lineHeight: 1.3,
          textAlign: 'center',
          whiteSpace: 'nowrap',
        }}
      >
        {color.name}
      </span>
    </motion.div>
  )
}

/* ── 코디 캐러셀 카드 ─────────────────────────────────── */

function OutfitCarouselCard({
  outfit,
  index,
}: {
  outfit: ToneSampleOutfit
  index: number
}) {
  const router = useRouter()

  return (
    <motion.button
      type="button"
      onClick={() => router.push(`/outfit/${outfit.outfit_id}`)}
      className="flex-shrink-0 flex flex-col overflow-hidden"
      style={{
        width: 160,
        borderRadius: 'var(--radius-md)',
        background: 'var(--surface)',
        border: '1px solid var(--border)',
        cursor: 'pointer',
        WebkitTapHighlightColor: 'transparent',
      }}
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: 0.2 + index * 0.1, duration: 0.35 }}
      whileTap={{ scale: 0.97 }}
    >
      {/* 이미지 (3:4) */}
      <div
        className="relative w-full"
        style={{ aspectRatio: '3/4', background: 'var(--border)' }}
      >
        {outfit.image_url ? (
          <Image
            src={outfit.image_url}
            alt="코디"
            fill
            sizes="160px"
            className="object-cover"
            loading="lazy"
            unoptimized
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <span style={{ fontSize: '11px', color: 'var(--text-tertiary)' }}>
              이미지 없음
            </span>
          </div>
        )}
      </div>

      {/* 정보 */}
      <div className="flex flex-col gap-1 p-2.5">
        {outfit.designed_tpo && (
          <span
            style={{
              fontFamily: 'var(--font-body)',
              fontSize: '11px',
              color: 'var(--accent)',
              fontWeight: 600,
            }}
          >
            {TPO_LABEL[outfit.designed_tpo] ?? outfit.designed_tpo}
          </span>
        )}
        {outfit.total_price != null && (
          <span
            style={{
              fontFamily: 'var(--font-body)',
              fontSize: '13px',
              fontWeight: 700,
              color: 'var(--text-primary)',
            }}
          >
            {formatPrice(outfit.total_price)}
          </span>
        )}
      </div>
    </motion.button>
  )
}

/* ── 스켈레톤 ─────────────────────────────────────────── */

function ToneSkeleton() {
  return (
    <div className="flex flex-col" style={{ background: 'var(--bg)', minHeight: '100vh' }}>
      <div className="animate-pulse w-full" style={{ height: 200, background: 'var(--border)' }} />
      <div className="px-5 py-5 flex flex-col gap-5">
        <div className="animate-pulse" style={{ width: '70%', height: 18, borderRadius: 4, background: 'var(--border)' }} />
        <div className="animate-pulse" style={{ width: '90%', height: 14, borderRadius: 4, background: 'var(--border)' }} />
        <div className="flex gap-4 mt-2">
          {[0, 1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="flex flex-col items-center gap-1.5">
              <div className="animate-pulse" style={{ width: 44, height: 44, borderRadius: '50%', background: 'var(--border)' }} />
              <div className="animate-pulse" style={{ width: 30, height: 10, borderRadius: 4, background: 'var(--border)' }} />
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

/* ── "다른 톤으로 변경" 바텀시트 ──────────────────────── */

function ChangeToneSheet({ onClose }: { onClose: () => void }) {
  const router = useRouter()

  const handleChange = () => {
    onClose()
    router.push('/onboarding/step2')
  }

  return (
    <>
      <motion.div
        className="fixed inset-0 z-40"
        style={{ background: 'rgba(0,0,0,0.45)' }}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={onClose}
      />
      <motion.div
        className="fixed bottom-0 z-50 flex flex-col px-5"
        style={{
          left: 'var(--app-offset)',
          right: 'var(--app-offset)',
          background: 'var(--bg)',
          borderRadius: '20px 20px 0 0',
          paddingBottom: 'env(safe-area-inset-bottom, 24px)',
        }}
        initial={{ y: '100%' }}
        animate={{ y: 0 }}
        exit={{ y: '100%' }}
        transition={{ type: 'spring', stiffness: 300, damping: 30 }}
      >
        <div className="flex justify-center pt-3 pb-4">
          <div style={{ width: 36, height: 4, borderRadius: 2, background: 'var(--border)' }} />
        </div>

        <h3
          style={{
            fontFamily: 'var(--font-display)',
            fontSize: '18px',
            fontWeight: 700,
            color: 'var(--text-primary)',
            margin: '0 0 8px',
          }}
        >
          톤 변경
        </h3>
        <p
          style={{
            fontFamily: 'var(--font-body)',
            fontSize: '14px',
            color: 'var(--text-secondary)',
            margin: '0 0 24px',
            lineHeight: 1.6,
          }}
        >
          퍼스널컬러 선택 화면으로 이동해서 톤을 변경할 수 있어요.
        </p>

        <button
          type="button"
          onClick={handleChange}
          style={{
            width: '100%',
            padding: '14px',
            borderRadius: 'var(--radius-md)',
            background: 'var(--accent)',
            color: '#fff',
            fontFamily: 'var(--font-body)',
            fontSize: '15px',
            fontWeight: 600,
            border: 'none',
            cursor: 'pointer',
            marginBottom: 12,
          }}
        >
          톤 선택 화면으로 이동
        </button>
        <button
          type="button"
          onClick={onClose}
          style={{
            width: '100%',
            padding: '14px',
            borderRadius: 'var(--radius-md)',
            background: 'transparent',
            color: 'var(--text-secondary)',
            fontFamily: 'var(--font-body)',
            fontSize: '15px',
            fontWeight: 500,
            border: '1px solid var(--border)',
            cursor: 'pointer',
            marginBottom: 16,
          }}
        >
          취소
        </button>
      </motion.div>
    </>
  )
}

/* ── 메인 페이지 ─────────────────────────────────────── */

export default function ToneDetailPage() {
  const params = useParams()
  const router = useRouter()
  const toneId = params.id as string

  const [tone, setTone] = useState<ToneDetail | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showChangeSheet, setShowChangeSheet] = useState(false)

  useEffect(() => {
    fetchTone(toneId)
      .then(setTone)
      .catch((err) => setError(err instanceof Error ? err.message : '로드 실패'))
      .finally(() => setIsLoading(false))
  }, [toneId])

  if (isLoading) return <ToneSkeleton />

  if (error || !tone) {
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
          {error ?? '톤 정보를 찾을 수 없어요'}
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

  return (
    <div className="min-h-screen flex flex-col" style={{ background: 'var(--bg)' }}>

      {/* ══════════════ 그라데이션 히어로 (200px) ══════════════ */}
      <div
        className="relative w-full flex flex-col items-center justify-center"
        style={{ height: 200, background: tone.gradient }}
      >
        {/* 뒤로가기 */}
        <button
          type="button"
          aria-label="뒤로가기"
          onClick={() => router.back()}
          className="absolute top-3 left-4 flex items-center justify-center"
          style={{
            width: 36, height: 36,
            borderRadius: 'var(--radius-full)',
            background: 'rgba(0,0,0,0.25)',
            border: 'none',
            cursor: 'pointer',
          }}
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M15 18l-6-6 6-6" />
          </svg>
        </button>

        {/* 톤 이름 */}
        <motion.h1
          style={{
            fontFamily: 'var(--font-display)',
            fontSize: '32px',
            fontWeight: 700,
            color: '#FFFFFF',
            textShadow: '0 2px 12px rgba(0,0,0,0.2)',
            margin: 0,
          }}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
        >
          {tone.name}
        </motion.h1>
      </div>

      {/* ══════════════ 콘텐츠 ══════════════ */}
      <div className="flex flex-col gap-6 px-5 pt-6 pb-28">

        {/* ── 시즌 설명 ── */}
        <motion.p
          style={{
            fontFamily: 'var(--font-body)',
            fontSize: '15px',
            color: 'var(--text-secondary)',
            lineHeight: 1.7,
            margin: 0,
          }}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1, duration: 0.35 }}
        >
          {tone.description}
        </motion.p>

        {/* ── 잘 어울리는 색 ── */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2, duration: 0.3 }}
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
            잘 어울리는 색
          </p>
          <div
            className="flex gap-4 overflow-x-auto pb-1"
            style={{ scrollbarWidth: 'none', WebkitOverflowScrolling: 'touch' }}
          >
            {tone.good_colors.map((c, i) => (
              <SwatchChip key={c.hex} color={c} index={i} />
            ))}
          </div>
        </motion.div>

        {/* ── 피해야 할 색 ── */}
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
            피해야 할 색
          </p>
          <div
            className="flex gap-4 overflow-x-auto pb-1"
            style={{ scrollbarWidth: 'none', WebkitOverflowScrolling: 'touch' }}
          >
            {tone.avoid_colors.map((c, i) => (
              <SwatchChip key={c.hex} color={c} avoid index={i} />
            ))}
          </div>
        </motion.div>

        {/* ── 어울리는 코디 캐러셀 ── */}
        {tone.sample_outfits.length > 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3, duration: 0.3 }}
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
              이런 코디를 추천해요
            </p>
            <div
              className="flex gap-3 overflow-x-auto pb-2"
              style={{ scrollbarWidth: 'none', WebkitOverflowScrolling: 'touch' }}
            >
              {tone.sample_outfits.map((outfit, i) => (
                <OutfitCarouselCard key={outfit.outfit_id} outfit={outfit} index={i} />
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
        <motion.button
          type="button"
          onClick={() => setShowChangeSheet(true)}
          className="w-full flex items-center justify-center gap-2"
          style={{
            fontFamily: 'var(--font-body)',
            fontSize: '15px',
            fontWeight: 600,
            color: 'var(--accent)',
            background: 'transparent',
            border: '1.5px solid var(--accent)',
            borderRadius: 'var(--radius-md)',
            padding: '13px 0',
            cursor: 'pointer',
            WebkitTapHighlightColor: 'transparent',
          }}
          whileTap={{ scale: 0.97 }}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="1 4 1 10 7 10" />
            <path d="M3.51 15a9 9 0 1 0 .49-4" />
          </svg>
          다른 톤으로 변경하기
        </motion.button>
      </div>

      {/* ══════════════ 톤 변경 바텀시트 ══════════════ */}
      <AnimatePresence>
        {showChangeSheet && (
          <ChangeToneSheet onClose={() => setShowChangeSheet(false)} />
        )}
      </AnimatePresence>
    </div>
  )
}
