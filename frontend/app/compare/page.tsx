'use client'

import { useState, useEffect, Suspense } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import Image from 'next/image'
import { motion } from 'framer-motion'
import { fetchCompare, type CompareResult, type OutfitItem } from '@/lib/api'

/* ── 5축 메타 ─────────────────────────────────────────── */

const SCORE_AXES = [
  { key: 'pcf', label: '퍼스널컬러', color: '#964F4C' },
  { key: 'of',  label: 'TPO',        color: '#4F97A3' },
  { key: 'ch',  label: '색상 조화',  color: '#DDB67D' },
  { key: 'pe',  label: '가격 효율',  color: '#D1933F' },
  { key: 'sf',  label: '스타일',     color: '#6B5876' },
] as const

type ScoreKey = typeof SCORE_AXES[number]['key']

/* ── 가격 포맷 ────────────────────────────────────────── */

function formatPrice(price: number): string {
  if (price >= 10000) return `${Math.floor(price / 10000)}만원`
  return `${price.toLocaleString()}원`
}

/* ── 코디 이미지 패널 ─────────────────────────────────── */

interface OutfitPanelProps {
  outfit: OutfitItem
  side: 'a' | 'b'
  isWinner: boolean
  onDetail: () => void
}

function OutfitPanel({ outfit, side, isWinner, onDetail }: OutfitPanelProps) {
  const heroImage = outfit.items[0]?.image_url ?? ''
  const label = side === 'a' ? 'A' : 'B'

  return (
    <motion.div
      className="flex flex-col"
      style={{ flex: 1, minWidth: 0 }}
      initial={{ opacity: 0, x: side === 'a' ? -20 : 20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.4, ease: 'easeOut' }}
    >
      {/* 이미지 */}
      <button
        type="button"
        onClick={onDetail}
        style={{ display: 'block', position: 'relative', width: '100%', aspectRatio: '3/4', cursor: 'pointer' }}
      >
        {heroImage ? (
          <Image
            src={heroImage}
            alt={`코디 ${label}`}
            fill
            sizes="50vw"
            className="object-cover"
            style={{
              borderRadius: 'var(--radius-md)',
              outline: isWinner ? '2.5px solid var(--accent)' : 'none',
            }}
            unoptimized
            loading="lazy"
          />
        ) : (
          <div
            className="w-full h-full flex items-center justify-center"
            style={{
              background: 'var(--border)',
              borderRadius: 'var(--radius-md)',
            }}
          >
            <span style={{ fontFamily: 'var(--font-body)', fontSize: '11px', color: 'var(--text-tertiary)' }}>
              이미지 없음
            </span>
          </div>
        )}

        {/* A / B 라벨 */}
        <span
          className="absolute top-2 left-2 flex items-center justify-center"
          style={{
            width: 28, height: 28,
            borderRadius: 'var(--radius-full)',
            background: isWinner ? 'var(--accent)' : 'rgba(34,34,34,0.6)',
            color: '#fff',
            fontFamily: 'var(--font-display)',
            fontSize: '14px',
            fontWeight: 700,
          }}
        >
          {label}
        </span>

        {/* 승자 왕관 */}
        {isWinner && (
          <motion.span
            className="absolute top-2 right-2"
            initial={{ scale: 0, rotate: -20 }}
            animate={{ scale: 1, rotate: 0 }}
            transition={{ delay: 0.5, type: 'spring', stiffness: 400, damping: 20 }}
            style={{ fontSize: '20px', lineHeight: 1 }}
          >
            👑
          </motion.span>
        )}
      </button>

      {/* 가격 */}
      {outfit.total_price != null && (
        <p
          style={{
            fontFamily: 'var(--font-body)',
            fontSize: '13px',
            fontWeight: 700,
            color: isWinner ? 'var(--accent)' : 'var(--text-primary)',
            margin: '8px 0 0',
            textAlign: 'center',
          }}
        >
          {formatPrice(outfit.total_price)}
        </p>
      )}
    </motion.div>
  )
}

/* ── 5축 비교 바 ──────────────────────────────────────── */

interface AxisRowProps {
  label: string
  color: string
  scoreA: number
  scoreB: number
  winner: 'a' | 'b' | 'tie'
  isDecisive: boolean
  delay: number
}

function AxisRow({ label, color, scoreA, scoreB, winner, isDecisive, delay }: AxisRowProps) {
  const maxVal = Math.max(scoreA, scoreB, 1)

  return (
    <motion.div
      className="flex flex-col gap-1"
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.3 }}
    >
      {/* 축 이름 */}
      <div className="flex items-center justify-center gap-2">
        <span
          style={{
            width: 6, height: 6,
            borderRadius: '50%',
            background: color,
            flexShrink: 0,
          }}
        />
        <span
          style={{
            fontFamily: 'var(--font-body)',
            fontSize: '11px',
            fontWeight: isDecisive ? 700 : 500,
            color: isDecisive ? 'var(--text-primary)' : 'var(--text-secondary)',
            letterSpacing: '0.02em',
          }}
        >
          {label}
          {isDecisive && (
            <span style={{ color: 'var(--accent)', marginLeft: 4 }}>★</span>
          )}
        </span>
      </div>

      {/* 좌우 바 */}
      <div className="flex items-center gap-2">
        {/* A 바 (오른쪽 정렬) */}
        <div className="flex items-center justify-end" style={{ flex: 1 }}>
          <span
            style={{
              fontFamily: 'var(--font-body)',
              fontSize: '11px',
              fontWeight: 600,
              color: winner === 'a' ? color : 'var(--text-tertiary)',
              marginRight: 4,
              minWidth: 24,
              textAlign: 'right',
            }}
          >
            {Math.round(scoreA)}
          </span>
          <div
            style={{
              height: 8,
              borderRadius: 'var(--radius-full) 0 0 var(--radius-full)',
              background: 'var(--border)',
              overflow: 'hidden',
              width: 80,
              display: 'flex',
              justifyContent: 'flex-end',
            }}
          >
            <motion.div
              style={{
                height: '100%',
                borderRadius: 'var(--radius-full) 0 0 var(--radius-full)',
                background: winner === 'a' ? color : 'var(--text-tertiary)',
                opacity: winner === 'a' ? 1 : 0.4,
              }}
              initial={{ width: '0%' }}
              animate={{ width: `${(scoreA / maxVal) * 100}%` }}
              transition={{ duration: 0.7, ease: 'easeOut', delay: delay + 0.1 }}
            />
          </div>
        </div>

        {/* 중앙 구분선 */}
        <div style={{ width: 1, height: 16, background: 'var(--border)', flexShrink: 0 }} />

        {/* B 바 (왼쪽 정렬) */}
        <div className="flex items-center" style={{ flex: 1 }}>
          <div
            style={{
              height: 8,
              borderRadius: '0 var(--radius-full) var(--radius-full) 0',
              background: 'var(--border)',
              overflow: 'hidden',
              width: 80,
            }}
          >
            <motion.div
              style={{
                height: '100%',
                borderRadius: '0 var(--radius-full) var(--radius-full) 0',
                background: winner === 'b' ? color : 'var(--text-tertiary)',
                opacity: winner === 'b' ? 1 : 0.4,
              }}
              initial={{ width: '0%' }}
              animate={{ width: `${(scoreB / maxVal) * 100}%` }}
              transition={{ duration: 0.7, ease: 'easeOut', delay: delay + 0.1 }}
            />
          </div>
          <span
            style={{
              fontFamily: 'var(--font-body)',
              fontSize: '11px',
              fontWeight: 600,
              color: winner === 'b' ? color : 'var(--text-tertiary)',
              marginLeft: 4,
              minWidth: 24,
            }}
          >
            {Math.round(scoreB)}
          </span>
        </div>
      </div>
    </motion.div>
  )
}

/* ── 결론 카드 ────────────────────────────────────────── */

function ConclusionCard({ winner, conclusion }: { winner: 'a' | 'b' | 'tie'; conclusion: string }) {
  return (
    <motion.div
      className="flex items-center gap-3 px-4 py-4"
      style={{
        background: winner === 'tie' ? 'var(--surface)' : 'var(--bg)',
        border: winner === 'tie' ? '1px solid var(--border)' : '1.5px solid var(--accent)',
        borderRadius: 'var(--radius-lg)',
      }}
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.6, duration: 0.35 }}
    >
      <span style={{ fontSize: '20px', flexShrink: 0 }}>
        {winner === 'tie' ? '🤝' : '✨'}
      </span>
      <p
        style={{
          fontFamily: 'var(--font-body)',
          fontSize: '14px',
          fontWeight: 600,
          color: 'var(--text-primary)',
          lineHeight: 1.5,
          margin: 0,
        }}
      >
        {conclusion}
      </p>
    </motion.div>
  )
}

/* ── 스켈레톤 ─────────────────────────────────────────── */

function Skeleton() {
  return (
    <div className="flex flex-col gap-5 px-4 pt-4">
      <div className="flex gap-3">
        {[0, 1].map(i => (
          <div key={i} style={{ flex: 1 }}>
            <motion.div
              style={{ width: '100%', aspectRatio: '3/4', borderRadius: 'var(--radius-md)', background: 'var(--border)' }}
              animate={{ opacity: [0.5, 1, 0.5] }}
              transition={{ repeat: Infinity, duration: 1.4, ease: 'easeInOut', delay: i * 0.15 }}
            />
          </div>
        ))}
      </div>
      <div className="flex flex-col gap-3">
        {[0, 1, 2, 3, 4].map(i => (
          <motion.div
            key={i}
            style={{ height: 20, borderRadius: 4, background: 'var(--border)' }}
            animate={{ opacity: [0.5, 1, 0.5] }}
            transition={{ repeat: Infinity, duration: 1.4, ease: 'easeInOut', delay: i * 0.08 }}
          />
        ))}
      </div>
    </div>
  )
}

/* ── 메인 내용 ────────────────────────────────────────── */

function CompareContent() {
  const router = useRouter()
  const searchParams = useSearchParams()

  const ids    = searchParams.get('ids') ?? ''
  const toneId = searchParams.get('tone_id') ?? ''
  const gender = searchParams.get('gender') ?? 'female'
  const budgetMin = Number(searchParams.get('budget_min') ?? 0)
  const budgetMax = Number(searchParams.get('budget_max') ?? 300000)
  const tpo    = searchParams.get('tpo') ?? ''

  const [result, setResult] = useState<CompareResult | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!ids || !toneId) {
      setError('비교할 코디 정보가 없어요.')
      setLoading(false)
      return
    }
    fetchCompare({ ids, tone_id: toneId, gender, budget_min: budgetMin, budget_max: budgetMax, tpo })
      .then(setResult)
      .catch(() => setError('비교 정보를 불러오지 못했어요.'))
      .finally(() => setLoading(false))
  }, [ids, toneId, gender, budgetMin, budgetMax, tpo])

  const goDetail = (outfit: OutfitItem) => {
    const q = new URLSearchParams({ tone_id: toneId, gender, budget_min: String(budgetMin), budget_max: String(budgetMax), tpo })
    router.push(`/outfit/${outfit.outfit_id}?${q}`)
  }

  return (
    <div className="min-h-screen flex flex-col" style={{ background: 'var(--bg)' }}>

      {/* 헤더 */}
      <header
        className="sticky top-0 z-30 flex items-center gap-3 px-4 py-3"
        style={{ background: 'var(--bg)', borderBottom: '1px solid var(--border)' }}
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
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            flexShrink: 0,
          }}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--text-primary)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M15 18l-6-6 6-6" />
          </svg>
        </button>
        <h1
          style={{
            fontFamily: 'var(--font-display)',
            fontSize: '20px',
            fontWeight: 700,
            color: 'var(--text-primary)',
            margin: 0,
          }}
        >
          A vs B 비교
        </h1>
      </header>

      {loading && <Skeleton />}

      {!loading && error && (
        <div className="flex flex-col items-center gap-4 pt-24 px-8 text-center">
          <p style={{ fontFamily: 'var(--font-body)', fontSize: '15px', color: 'var(--text-secondary)' }}>
            {error}
          </p>
          <button
            type="button"
            onClick={() => router.back()}
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
            돌아가기
          </button>
        </div>
      )}

      {!loading && result && (
        <div className="flex flex-col gap-6 px-4 pt-5 pb-12">

          {/* ── 이미지 패널 + VS ── */}
          <div className="flex gap-3 items-start">
            <OutfitPanel
              outfit={result.outfit_a}
              side="a"
              isWinner={result.winner === 'a'}
              onDetail={() => goDetail(result.outfit_a)}
            />

            {/* VS 배지 */}
            <div
              className="flex items-center justify-center shrink-0"
              style={{
                width: 32, height: 32,
                borderRadius: 'var(--radius-full)',
                background: 'var(--surface)',
                border: '1px solid var(--border)',
                fontFamily: 'var(--font-display)',
                fontSize: '11px',
                fontWeight: 700,
                color: 'var(--text-secondary)',
                marginTop: 'calc(50% - 16px)',
              }}
            >
              VS
            </div>

            <OutfitPanel
              outfit={result.outfit_b}
              side="b"
              isWinner={result.winner === 'b'}
              onDetail={() => goDetail(result.outfit_b)}
            />
          </div>

          {/* ── 총점 요약 ── */}
          <motion.div
            className="flex items-center justify-center gap-3"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3, duration: 0.3 }}
          >
            <span
              style={{
                fontFamily: 'var(--font-body)',
                fontSize: '22px',
                fontWeight: 700,
                color: result.winner === 'a' ? 'var(--accent)' : 'var(--text-tertiary)',
              }}
            >
              {result.score_a}
            </span>
            <span
              style={{
                fontFamily: 'var(--font-body)',
                fontSize: '12px',
                color: 'var(--text-tertiary)',
              }}
            >
              총점
            </span>
            <span
              style={{
                fontFamily: 'var(--font-body)',
                fontSize: '22px',
                fontWeight: 700,
                color: result.winner === 'b' ? 'var(--accent)' : 'var(--text-tertiary)',
              }}
            >
              {result.score_b}
            </span>
          </motion.div>

          {/* ── 5축 비교 ── */}
          <motion.section
            className="flex flex-col gap-4 px-2 py-4"
            style={{
              background: 'var(--surface)',
              borderRadius: 'var(--radius-lg)',
              border: '1px solid var(--border)',
            }}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.35, duration: 0.3 }}
          >
            {/* A / B 헤더 */}
            <div className="flex items-center">
              <span style={{ flex: 1, textAlign: 'right', fontFamily: 'var(--font-display)', fontSize: '13px', fontWeight: 700, color: result.winner === 'a' ? 'var(--accent)' : 'var(--text-secondary)', paddingRight: 12 }}>A</span>
              <div style={{ width: 1 }} />
              <span style={{ flex: 1, textAlign: 'left', fontFamily: 'var(--font-display)', fontSize: '13px', fontWeight: 700, color: result.winner === 'b' ? 'var(--accent)' : 'var(--text-secondary)', paddingLeft: 12 }}>B</span>
            </div>

            {SCORE_AXES.map((axis, i) => {
              const diff = result.axis_diffs[axis.key] ?? 0
              const axisWinner: 'a' | 'b' | 'tie' =
                Math.abs(diff) < 3 ? 'tie' : diff > 0 ? 'a' : 'b'
              return (
                <AxisRow
                  key={axis.key}
                  label={axis.label}
                  color={axis.color}
                  scoreA={result.outfit_a.scores[axis.key as ScoreKey]}
                  scoreB={result.outfit_b.scores[axis.key as ScoreKey]}
                  winner={axisWinner}
                  isDecisive={result.decisive_axis === axis.key}
                  delay={0.4 + i * 0.07}
                />
              )
            })}
          </motion.section>

          {/* ── 결론 ── */}
          <ConclusionCard winner={result.winner} conclusion={result.conclusion} />

          {/* ── 상세 보기 버튼 ── */}
          <motion.div
            className="flex gap-3"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.7, duration: 0.3 }}
          >
            {(['a', 'b'] as const).map(side => {
              const outfit = side === 'a' ? result.outfit_a : result.outfit_b
              const isWinner = result.winner === side
              return (
                <button
                  key={side}
                  type="button"
                  onClick={() => goDetail(outfit)}
                  style={{
                    flex: 1,
                    padding: '13px',
                    borderRadius: 'var(--radius-md)',
                    background: isWinner ? 'var(--accent)' : 'transparent',
                    border: isWinner ? 'none' : '1px solid var(--border)',
                    fontFamily: 'var(--font-body)',
                    fontSize: '14px',
                    fontWeight: 600,
                    color: isWinner ? '#fff' : 'var(--text-secondary)',
                    cursor: 'pointer',
                    WebkitTapHighlightColor: 'transparent',
                  }}
                >
                  {side.toUpperCase()} 자세히 보기
                </button>
              )
            })}
          </motion.div>
        </div>
      )}
    </div>
  )
}

/* ── 페이지 ───────────────────────────────────────────── */

export default function ComparePage() {
  return (
    <Suspense>
      <CompareContent />
    </Suspense>
  )
}
