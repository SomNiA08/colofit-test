'use client'

import { usePathname, useRouter } from 'next/navigation'
import { AnimatePresence, motion, MotionConfig } from 'framer-motion'

const TOTAL_STEPS = 5

/** URL에서 현재 온보딩 스텝 번호를 추출한다. */
function getStep(pathname: string): number {
  const match = pathname.match(/\/onboarding\/step(\d)/)
  return match ? parseInt(match[1], 10) : 1
}

interface OnboardingLayoutProps {
  children: React.ReactNode
}

export default function OnboardingLayout({ children }: OnboardingLayoutProps) {
  const pathname = usePathname()
  const router = useRouter()
  const currentStep = getStep(pathname)

  return (
    // reducedMotion="user" — prefers-reduced-motion 미디어 쿼리 자동 반영
    <MotionConfig reducedMotion="user">
      <div
        className="flex flex-col min-h-screen"
        style={{ background: 'var(--bg)' }}
      >
        {/* ── 상단 헤더 ──────────────────────────────────── */}
        <div className="flex-shrink-0 px-5 pt-6 pb-3">

          {/* 뒤로가기 버튼 — Step 1에서는 숨김 */}
          <div className="h-8 mb-4">
            {currentStep > 1 && (
              <button
                type="button"
                onClick={() => router.back()}
                aria-label="이전 단계로 이동"
                className="flex items-center justify-center w-8 h-8 -ml-1 rounded-full transition-opacity active:opacity-50"
                style={{ color: 'var(--text-primary)' }}
              >
                <svg
                  width="20"
                  height="20"
                  viewBox="0 0 20 20"
                  fill="none"
                  aria-hidden="true"
                >
                  <path
                    d="M12.5 15L7.5 10L12.5 5"
                    stroke="currentColor"
                    strokeWidth="1.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              </button>
            )}
          </div>

          {/* 5단계 진행 바 */}
          <div className="flex gap-1.5 mb-2" role="progressbar" aria-valuenow={currentStep} aria-valuemin={1} aria-valuemax={TOTAL_STEPS} aria-label={`온보딩 진행 단계 ${currentStep} / ${TOTAL_STEPS}`}>
            {Array.from({ length: TOTAL_STEPS }).map((_, i) => (
              <div
                key={i}
                className="flex-1 h-1 rounded-full overflow-hidden"
                style={{ background: 'var(--border)' }}
              >
                {/* 현재 스텝까지 채워진 세그먼트 */}
                {i < currentStep && (
                  <motion.div
                    className="h-full rounded-full"
                    style={{ background: 'var(--accent)' }}
                    initial={{ width: '0%' }}
                    animate={{ width: '100%' }}
                    transition={{ duration: 0.4, ease: 'easeOut', delay: i * 0.05 }}
                  />
                )}
              </div>
            ))}
          </div>

          {/* Step N / 5 텍스트 */}
          <p
            className="text-[13px] leading-[1.5]"
            style={{
              color: 'var(--text-secondary)',
              fontFamily: 'var(--font-body)',
            }}
          >
            Step {currentStep} / {TOTAL_STEPS}
          </p>
        </div>

        {/* ── 페이지 콘텐츠 (슬라이드 전환) ───────────────── */}
        <AnimatePresence mode="wait" initial={false}>
          <motion.div
            key={pathname}
            className="flex-1 flex flex-col"
            initial={{ x: 40, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: -40, opacity: 0 }}
            transition={{ duration: 0.25, ease: 'easeInOut' }}
          >
            {children}
          </motion.div>
        </AnimatePresence>
      </div>
    </MotionConfig>
  )
}
