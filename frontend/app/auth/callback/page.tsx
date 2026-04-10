'use client'

import { useEffect, Suspense } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { motion } from 'framer-motion'

/* ── OAuth 콜백 처리 ─────────────────────────────────── */

function CallbackContent() {
  const router = useRouter()
  const searchParams = useSearchParams()

  useEffect(() => {
    const token   = searchParams.get('token')
    const userId  = searchParams.get('user_id')
    const isNew   = searchParams.get('is_new') === 'true'

    if (!token || !userId) {
      // 파라미터 없음 → 로그인 페이지로
      router.replace('/login')
      return
    }

    // 토큰 & user_id 저장
    localStorage.setItem('auth_token', token)
    localStorage.setItem('onboarding_user_id', userId)

    if (isNew) {
      // 신규 유저 → 온보딩
      router.replace('/onboarding/step1')
    } else {
      // 기존 유저 → 피드
      router.replace('/feed')
    }
  }, [router, searchParams])

  return (
    <div
      className="min-h-screen flex flex-col items-center justify-center gap-4"
      style={{ background: 'var(--bg)' }}
    >
      <motion.div
        animate={{ rotate: 360 }}
        transition={{ repeat: Infinity, duration: 1, ease: 'linear' }}
        style={{
          width: 36, height: 36,
          borderRadius: 'var(--radius-full)',
          border: '3px solid var(--border)',
          borderTopColor: 'var(--accent)',
        }}
      />
      <p
        style={{
          fontFamily: 'var(--font-body)',
          fontSize: '14px',
          color: 'var(--text-secondary)',
        }}
      >
        로그인 처리 중...
      </p>
    </div>
  )
}

export default function AuthCallbackPage() {
  return (
    <Suspense>
      <CallbackContent />
    </Suspense>
  )
}
