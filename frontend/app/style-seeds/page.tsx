'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import { fetchReactionCount, deleteReactions } from '@/lib/api'

/* ── 4축 메타 ─────────────────────────────────────────── */

interface SeedAxis {
  key: 'mood' | 'silhouette' | 'color' | 'price'
  label: string
  color: string
  icon: React.ReactNode
}

const AXES: SeedAxis[] = [
  {
    key: 'mood',
    label: '무드',
    color: 'var(--score-pcf)',
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10" />
        <path d="M8 14s1.5 2 4 2 4-2 4-2" />
        <line x1="9" y1="9" x2="9.01" y2="9" />
        <line x1="15" y1="9" x2="15.01" y2="9" />
      </svg>
    ),
  },
  {
    key: 'silhouette',
    label: '실루엣',
    color: 'var(--score-of)',
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
      </svg>
    ),
  },
  {
    key: 'color',
    label: '색감',
    color: 'var(--score-ch)',
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="13.5" cy="6.5" r="2.5" />
        <circle cx="17.5" cy="10.5" r="2.5" />
        <circle cx="8.5" cy="7.5" r="2.5" />
        <circle cx="6.5" cy="12.5" r="2.5" />
        <path d="M12 22a9.5 9.5 0 0 0 0-19 9 9 0 0 0-9 9 4.5 4.5 0 0 0 4.5 4.5H12v5.5z" />
      </svg>
    ),
  },
  {
    key: 'price',
    label: '가격대',
    color: 'var(--score-pe)',
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <line x1="12" y1="1" x2="12" y2="23" />
        <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
      </svg>
    ),
  },
]

/* ── 스타일 키워드 한글 ────────────────────────────────── */

const STYLE_KO: Record<string, string> = {
  minimal:   '미니멀',
  casual:    '캐주얼',
  classic:   '클래식',
  street:    '스트릿',
  editorial: '에디토리얼',
  lovely:    '러블리',
  dandy:     '댄디',
  amekaji:   '아메카지',
}

/* ── 학습 진행바 목표 ─────────────────────────────────── */

const FEEDBACK_GOAL = 30

/* ── 확인 다이얼로그 ──────────────────────────────────── */

type ResetMode = 'full' | 'feedback_only'

interface ConfirmDialogProps {
  mode: ResetMode
  onConfirm: () => void
  onCancel: () => void
}

function ConfirmDialog({ mode, onConfirm, onCancel }: ConfirmDialogProps) {
  return (
    <>
      <motion.div
        className="fixed inset-0 z-40"
        style={{ background: 'rgba(0,0,0,0.5)' }}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={onCancel}
      />
      <motion.div
        className="fixed inset-0 z-50 flex items-center justify-center px-6"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
      >
        <motion.div
          className="w-full flex flex-col gap-4"
          style={{
            background: 'var(--bg)',
            borderRadius: 'var(--radius-xl)',
            padding: '24px',
            maxWidth: 320,
          }}
          initial={{ scale: 0.92, y: 12 }}
          animate={{ scale: 1, y: 0 }}
          exit={{ scale: 0.92, y: 12 }}
          transition={{ type: 'spring', stiffness: 350, damping: 28 }}
        >
          <h3
            style={{
              fontFamily: 'var(--font-display)',
              fontSize: '18px',
              fontWeight: 700,
              color: 'var(--text-primary)',
              margin: 0,
            }}
          >
            {mode === 'full' ? '취향 초기화' : '피드백 초기화'}
          </h3>
          <p
            style={{
              fontFamily: 'var(--font-body)',
              fontSize: '14px',
              color: 'var(--text-secondary)',
              lineHeight: 1.6,
              margin: 0,
            }}
          >
            {mode === 'full'
              ? '취향 분석 결과와 피드백 학습 데이터를 모두 초기화할까요? 이 작업은 되돌릴 수 없어요.'
              : '피드백 학습 데이터만 초기화할까요? 취향 분석 결과(Style Seed)는 유지돼요.'}
          </p>
          <div className="flex gap-3">
            <button
              type="button"
              onClick={onCancel}
              style={{
                flex: 1,
                padding: '12px',
                borderRadius: 'var(--radius-md)',
                background: 'transparent',
                border: '1px solid var(--border)',
                fontFamily: 'var(--font-body)',
                fontSize: '14px',
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
                padding: '12px',
                borderRadius: 'var(--radius-md)',
                background: 'var(--error-bg)',
                border: '1px solid var(--error-border)',
                fontFamily: 'var(--font-body)',
                fontSize: '14px',
                fontWeight: 600,
                color: 'var(--error-text)',
                cursor: 'pointer',
              }}
            >
              초기화
            </button>
          </div>
        </motion.div>
      </motion.div>
    </>
  )
}

/* ── 시드 축 카드 ─────────────────────────────────────── */

function SeedCard({
  axis,
  value,
  index,
}: {
  axis: SeedAxis
  value: string | null
  index: number
}) {
  return (
    <motion.div
      className="flex items-center gap-4 px-4 py-4"
      style={{
        background: 'var(--surface)',
        borderRadius: 'var(--radius-lg)',
        border: '1px solid var(--border)',
      }}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.1 + index * 0.07, duration: 0.3 }}
    >
      {/* 아이콘 */}
      <div
        style={{
          width: 44,
          height: 44,
          borderRadius: 'var(--radius-md)',
          background: 'var(--bg)',
          border: '1px solid var(--border)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: axis.color,
          flexShrink: 0,
        }}
      >
        {axis.icon}
      </div>

      {/* 라벨 + 값 */}
      <div className="flex flex-col gap-0.5 flex-1">
        <span
          style={{
            fontFamily: 'var(--font-body)',
            fontSize: '12px',
            color: 'var(--text-tertiary)',
          }}
        >
          {axis.label}
        </span>
        <span
          style={{
            fontFamily: 'var(--font-body)',
            fontSize: '16px',
            fontWeight: 600,
            color: value ? 'var(--text-primary)' : 'var(--text-tertiary)',
          }}
        >
          {value ? (STYLE_KO[value] ?? value) : '미설정'}
        </span>
      </div>

      {/* 값이 있으면 컬러 뱃지 */}
      {value && (
        <span
          style={{
            fontFamily: 'var(--font-body)',
            fontSize: '11px',
            fontWeight: 600,
            color: axis.color,
            background: 'var(--bg)',
            border: `1px solid ${axis.color}`,
            borderRadius: 'var(--radius-full)',
            padding: '3px 10px',
            whiteSpace: 'nowrap',
          }}
        >
          {STYLE_KO[value] ?? value}
        </span>
      )}
    </motion.div>
  )
}

/* ── 메인 페이지 ─────────────────────────────────────── */

export default function StyleSeedsPage() {
  const router = useRouter()

  // 시드 데이터 (localStorage)
  const [seeds, setSeeds] = useState<string[]>([])
  const [feedbackCount, setFeedbackCount] = useState(0)
  const [dialog, setDialog] = useState<ResetMode | null>(null)
  const [resetDone, setResetDone] = useState(false)

  useEffect(() => {
    const raw = localStorage.getItem('onboarding_visual_seeds')
    setSeeds(raw ? (JSON.parse(raw) as string[]) : [])

    const userId = localStorage.getItem('onboarding_user_id')
    if (userId) {
      fetchReactionCount(userId).then(setFeedbackCount).catch(() => {})
    }
  }, [])

  // 전체 초기화
  const handleFullReset = async () => {
    const userId = localStorage.getItem('onboarding_user_id')
    if (userId) await deleteReactions(userId).catch(() => {})
    localStorage.removeItem('onboarding_visual_seeds')
    setSeeds([])
    setFeedbackCount(0)
    setDialog(null)
    setResetDone(true)
  }

  // 피드백만 초기화 (seeds 유지, DB 반응만 삭제)
  const handleFeedbackReset = async () => {
    const userId = localStorage.getItem('onboarding_user_id')
    if (userId) await deleteReactions(userId).catch(() => {})
    setFeedbackCount(0)
    setDialog(null)
    setResetDone(true)
  }

  const progress = Math.min(feedbackCount / FEEDBACK_GOAL, 1)

  return (
    <div className="min-h-screen flex flex-col" style={{ background: 'var(--bg)' }}>

      {/* ══════════════ 헤더 ══════════════ */}
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
        <h1
          style={{
            fontFamily: 'var(--font-display)',
            fontSize: '20px',
            fontWeight: 700,
            color: 'var(--text-primary)',
            margin: 0,
          }}
        >
          취향 관리
        </h1>
      </header>

      <div className="flex flex-col gap-6 px-5 pt-5 pb-24">

        {/* ══════════════ Style Seed 4축 ══════════════ */}
        <section>
          <p
            style={{
              fontFamily: 'var(--font-body)',
              fontSize: '13px',
              fontWeight: 600,
              color: 'var(--text-secondary)',
              margin: '0 0 12px',
            }}
          >
            현재 취향
          </p>
          <div className="flex flex-col gap-3">
            {AXES.map((axis, i) => (
              <SeedCard
                key={axis.key}
                axis={axis}
                value={seeds[i] ?? null}
                index={i}
              />
            ))}
          </div>
        </section>

        {/* ══════════════ 학습 상태 진행바 ══════════════ */}
        <motion.section
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.35, duration: 0.3 }}
        >
          <div className="flex items-center justify-between mb-2">
            <p
              style={{
                fontFamily: 'var(--font-body)',
                fontSize: '13px',
                fontWeight: 600,
                color: 'var(--text-secondary)',
                margin: 0,
              }}
            >
              학습 상태
            </p>
            <span
              style={{
                fontFamily: 'var(--font-body)',
                fontSize: '13px',
                color: feedbackCount >= FEEDBACK_GOAL ? 'var(--accent)' : 'var(--text-tertiary)',
                fontWeight: feedbackCount >= FEEDBACK_GOAL ? 600 : 400,
              }}
            >
              {feedbackCount} / {FEEDBACK_GOAL}건
            </span>
          </div>

          {/* 진행바 트랙 */}
          <div
            style={{
              height: 8,
              borderRadius: 'var(--radius-full)',
              background: 'var(--border)',
              overflow: 'hidden',
            }}
          >
            <motion.div
              style={{
                height: '100%',
                borderRadius: 'var(--radius-full)',
                background: feedbackCount >= FEEDBACK_GOAL
                  ? 'var(--score-pcf)'
                  : 'var(--accent)',
              }}
              initial={{ width: '0%' }}
              animate={{ width: `${progress * 100}%` }}
              transition={{ duration: 0.8, ease: 'easeOut', delay: 0.4 }}
            />
          </div>

          <p
            style={{
              fontFamily: 'var(--font-body)',
              fontSize: '12px',
              color: 'var(--text-tertiary)',
              margin: '6px 0 0',
            }}
          >
            {feedbackCount >= FEEDBACK_GOAL
              ? '충분한 피드백이 쌓였어요! 추천이 더욱 정확해졌어요.'
              : `피드백 ${FEEDBACK_GOAL - feedbackCount}건 더 남았어요. 코디를 저장하거나 넘기면 학습돼요.`}
          </p>
        </motion.section>

        {/* ══════════════ 액션 버튼 ══════════════ */}
        <motion.section
          className="flex flex-col gap-3"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.45, duration: 0.3 }}
        >
          {/* 취향 다시 분석하기 */}
          <button
            type="button"
            onClick={() => router.push('/onboarding/step5')}
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
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 8,
            }}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="1 4 1 10 7 10" />
              <path d="M3.51 15a9 9 0 1 0 .49-4" />
            </svg>
            취향 다시 분석하기
          </button>

          {/* 피드백만 초기화 */}
          <button
            type="button"
            onClick={() => setDialog('feedback_only')}
            style={{
              width: '100%',
              padding: '14px',
              borderRadius: 'var(--radius-md)',
              background: 'transparent',
              border: '1px solid var(--border)',
              fontFamily: 'var(--font-body)',
              fontSize: '15px',
              fontWeight: 500,
              color: 'var(--text-secondary)',
              cursor: 'pointer',
              WebkitTapHighlightColor: 'transparent',
            }}
          >
            피드백만 초기화
          </button>

          {/* 취향 초기화 */}
          <button
            type="button"
            onClick={() => setDialog('full')}
            style={{
              width: '100%',
              padding: '14px',
              borderRadius: 'var(--radius-md)',
              background: 'transparent',
              border: 'none',
              fontFamily: 'var(--font-body)',
              fontSize: '15px',
              fontWeight: 600,
              color: 'var(--error-text)',
              cursor: 'pointer',
              WebkitTapHighlightColor: 'transparent',
            }}
          >
            취향 초기화
          </button>
        </motion.section>

        {/* 초기화 완료 토스트 */}
        <AnimatePresence>
          {resetDone && (
            <motion.div
              className="fixed bottom-8 left-1/2 z-50 pointer-events-none"
              style={{ transform: 'translateX(-50%)' }}
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 8 }}
              transition={{ duration: 0.25 }}
              onAnimationComplete={() => setTimeout(() => setResetDone(false), 1800)}
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
                초기화 완료
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* ══════════════ 확인 다이얼로그 ══════════════ */}
      <AnimatePresence>
        {dialog && (
          <ConfirmDialog
            mode={dialog}
            onConfirm={dialog === 'full' ? handleFullReset : handleFeedbackReset}
            onCancel={() => setDialog(null)}
          />
        )}
      </AnimatePresence>
    </div>
  )
}
