'use client'

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { postFeedback } from '@/lib/api'
import { useBodyScrollLock } from '@/hooks/useBodyScrollLock'

interface PurchaseFeedbackSheetProps {
  outfitId: string
  visible: boolean
  onClose: () => void
}

type Step = 'initial' | 'dislike_reason' | 'done'

const DISLIKE_TAGS = [
  '가격이 맞지 않아요',
  '스타일이 달라요',
  '품절이에요',
  '기타',
]

export default function PurchaseFeedbackSheet({
  outfitId,
  visible,
  onClose,
}: PurchaseFeedbackSheetProps) {
  const [step, setStep] = useState<Step>('initial')
  const [submitting, setSubmitting] = useState(false)

  useBodyScrollLock(visible)

  // 닫힐 때 step 초기화
  useEffect(() => {
    if (!visible) {
      const timer = setTimeout(() => setStep('initial'), 300)
      return () => clearTimeout(timer)
    }
  }, [visible])

  function getToken(): string {
    return typeof window !== 'undefined'
      ? (localStorage.getItem('auth_token') ?? '')
      : ''
  }

  async function sendFeedback(eventType: 'like' | 'click' | 'dislike') {
    const token = getToken()
    if (!token) return // 게스트는 전송 생략
    setSubmitting(true)
    try {
      await postFeedback({ outfit_id: outfitId, event_type: eventType }, token)
    } catch {
      // 피드백 전송 실패는 조용히 넘어감
    } finally {
      setSubmitting(false)
    }
  }

  async function handlePositive() {
    await sendFeedback('like')
    setStep('done')
    setTimeout(onClose, 900)
  }

  async function handleNeutral() {
    await sendFeedback('click')
    setStep('done')
    setTimeout(onClose, 900)
  }

  function handleDislike() {
    setStep('dislike_reason')
  }

  async function handleTag() {
    await sendFeedback('dislike')
    setStep('done')
    setTimeout(onClose, 900)
  }

  return (
    <AnimatePresence>
      {visible && (
        <>
          {/* 배경 오버레이 */}
          <motion.div
            key="overlay"
            className="fixed inset-0 z-40"
            style={{ background: 'rgba(34,34,34,0.4)' }}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            onClick={onClose}
          />

          {/* 바텀 시트 */}
          <motion.div
            key="sheet"
            className="fixed bottom-0 z-50 flex flex-col"
            style={{
              left: 'var(--app-offset)',
              right: 'var(--app-offset)',
              background: 'var(--bg)',
              borderRadius: '16px 16px 0 0',
              padding: '12px 24px 32px',
              paddingBottom: 'calc(32px + env(safe-area-inset-bottom, 0px))',
            }}
            initial={{ y: '100%' }}
            animate={{ y: 0 }}
            exit={{ y: '100%' }}
            transition={{ type: 'spring', damping: 30, stiffness: 280 }}
          >
            {/* 핸들 바 */}
            <div
              className="mx-auto mb-6"
              style={{
                width: 36,
                height: 4,
                borderRadius: 'var(--radius-full)',
                background: 'var(--border)',
              }}
            />

            <AnimatePresence mode="wait">
              {/* ── 초기 화면 ── */}
              {step === 'initial' && (
                <motion.div
                  key="initial"
                  className="flex flex-col gap-6"
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -8 }}
                  transition={{ duration: 0.15 }}
                >
                  <h2
                    style={{
                      fontFamily: 'var(--font-display)',
                      fontSize: '18px',
                      fontWeight: 700,
                      color: 'var(--text-primary)',
                      margin: 0,
                      textAlign: 'center',
                      lineHeight: 1.4,
                    }}
                  >
                    이 추천이 도움이 됐나요?
                  </h2>

                  {/* 3개 이모지 버튼 */}
                  <div className="flex gap-3">
                    {([
                      { emoji: '👍', label: '구매했어요', handler: handlePositive },
                      { emoji: '🤔', label: '고민 중이에요', handler: handleNeutral },
                      { emoji: '👎', label: '아니에요',    handler: handleDislike },
                    ] as const).map(({ emoji, label, handler }) => (
                      <motion.button
                        key={label}
                        type="button"
                        onClick={handler}
                        disabled={submitting}
                        className="flex-1 flex flex-col items-center gap-2"
                        style={{
                          background: 'var(--surface)',
                          border: '1px solid var(--border)',
                          borderRadius: 'var(--radius-lg)',
                          padding: '16px 8px',
                          cursor: 'pointer',
                          WebkitTapHighlightColor: 'transparent',
                        }}
                        whileTap={{ scale: 0.95 }}
                      >
                        <span style={{ fontSize: '28px', lineHeight: 1 }}>{emoji}</span>
                        <span
                          style={{
                            fontFamily: 'var(--font-body)',
                            fontSize: '12px',
                            color: 'var(--text-secondary)',
                            lineHeight: 1.3,
                            textAlign: 'center',
                          }}
                        >
                          {label}
                        </span>
                      </motion.button>
                    ))}
                  </div>

                  {/* 나중에 */}
                  <button
                    type="button"
                    onClick={onClose}
                    style={{
                      fontFamily: 'var(--font-body)',
                      fontSize: '14px',
                      color: 'var(--text-tertiary)',
                      background: 'none',
                      border: 'none',
                      cursor: 'pointer',
                      padding: '4px 0',
                      alignSelf: 'center',
                    }}
                  >
                    나중에
                  </button>
                </motion.div>
              )}

              {/* ── 싫어요 이유 태그 ── */}
              {step === 'dislike_reason' && (
                <motion.div
                  key="reason"
                  className="flex flex-col gap-6"
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -8 }}
                  transition={{ duration: 0.15 }}
                >
                  <h2
                    style={{
                      fontFamily: 'var(--font-display)',
                      fontSize: '18px',
                      fontWeight: 700,
                      color: 'var(--text-primary)',
                      margin: 0,
                      textAlign: 'center',
                      lineHeight: 1.4,
                    }}
                  >
                    어떤 점이 아쉬웠나요?
                  </h2>

                  <div className="flex flex-wrap gap-2 justify-center">
                    {DISLIKE_TAGS.map((tag) => (
                      <motion.button
                        key={tag}
                        type="button"
                        onClick={handleTag}
                        disabled={submitting}
                        style={{
                          fontFamily: 'var(--font-body)',
                          fontSize: '14px',
                          color: 'var(--text-primary)',
                          background: 'var(--surface)',
                          border: '1px solid var(--border)',
                          borderRadius: 'var(--radius-full)',
                          padding: '10px 18px',
                          cursor: 'pointer',
                          WebkitTapHighlightColor: 'transparent',
                        }}
                        whileTap={{ scale: 0.95 }}
                      >
                        {tag}
                      </motion.button>
                    ))}
                  </div>

                  <button
                    type="button"
                    onClick={onClose}
                    style={{
                      fontFamily: 'var(--font-body)',
                      fontSize: '14px',
                      color: 'var(--text-tertiary)',
                      background: 'none',
                      border: 'none',
                      cursor: 'pointer',
                      padding: '4px 0',
                      alignSelf: 'center',
                    }}
                  >
                    나중에
                  </button>
                </motion.div>
              )}

              {/* ── 완료 ── */}
              {step === 'done' && (
                <motion.div
                  key="done"
                  className="flex flex-col items-center gap-3 py-4"
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ duration: 0.2 }}
                >
                  <span style={{ fontSize: '40px', lineHeight: 1 }}>✨</span>
                  <p
                    style={{
                      fontFamily: 'var(--font-display)',
                      fontSize: '16px',
                      fontWeight: 700,
                      color: 'var(--text-primary)',
                      margin: 0,
                      textAlign: 'center',
                    }}
                  >
                    감사해요! 추천이 개선될 거예요.
                  </p>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}
