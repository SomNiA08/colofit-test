'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'

/* ── 카카오 아이콘 ────────────────────────────────────── */

function KakaoIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="#191919">
      <path d="M12 3C6.477 3 2 6.477 2 10.8c0 2.7 1.63 5.08 4.1 6.54L5.2 21l4.62-2.46C10.24 18.7 11.1 18.8 12 18.8c5.523 0 10-3.477 10-7.8C22 6.477 17.523 3 12 3z" />
    </svg>
  )
}

/* ── 구글 아이콘 ──────────────────────────────────────── */

function GoogleIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24">
      <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
      <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
      <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z" />
      <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" />
    </svg>
  )
}

/* ── 퍼스널컬러 장식 스트립 ──────────────────────────── */

const TONE_COLORS = [
  '#F7D9C4', // 봄웜
  '#C4D9E0', // 여름쿨
  '#C4A882', // 가을웜
  '#8BA3BA', // 겨울쿨
]

function ColorStrip() {
  return (
    <div className="flex w-full overflow-hidden" style={{ borderRadius: 'var(--radius-sm)', height: 4 }}>
      {TONE_COLORS.map((color, i) => (
        <motion.div
          key={i}
          style={{ flex: 1, background: color }}
          initial={{ scaleX: 0 }}
          animate={{ scaleX: 1 }}
          transition={{ delay: 0.3 + i * 0.1, duration: 0.5, ease: 'easeOut' }}
        />
      ))}
    </div>
  )
}

/* ── 토스트 ────────────────────────────────────────────── */

function Toast({ message }: { message: string }) {
  return (
    <motion.div
      className="fixed bottom-10 left-1/2 z-50 pointer-events-none"
      style={{ transform: 'translateX(-50%)', whiteSpace: 'nowrap' }}
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 8 }}
      transition={{ duration: 0.22 }}
    >
      <div
        style={{
          fontFamily: 'var(--font-body)',
          fontSize: '14px',
          fontWeight: 500,
          color: '#fff',
          background: 'rgba(34,34,34,0.82)',
          borderRadius: 'var(--radius-full)',
          padding: '9px 22px',
        }}
      >
        {message}
      </div>
    </motion.div>
  )
}

/* ── 메인 페이지 ─────────────────────────────────────── */

export default function LoginPage() {
  const router = useRouter()
  const [toast, setToast] = useState<string | null>(null)

  const showToast = (msg: string) => {
    setToast(msg)
    setTimeout(() => setToast(null), 2200)
  }

  const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

  const handleKakao = () => {
    if (!process.env.NEXT_PUBLIC_KAKAO_ENABLED) {
      showToast('카카오 로그인은 준비 중이에요')
      return
    }
    window.location.href = `${API_URL}/api/auth/kakao`
  }

  const handleGoogle = () => {
    if (!process.env.NEXT_PUBLIC_GOOGLE_ENABLED) {
      showToast('구글 로그인은 준비 중이에요')
      return
    }
    window.location.href = `${API_URL}/api/auth/google`
  }

  const handleGuest = () => router.push('/onboarding/step1')

  return (
    <div
      className="min-h-screen flex flex-col items-center justify-between px-6"
      style={{ background: 'var(--bg)', paddingTop: '15vh', paddingBottom: '10vh' }}
    >

      {/* ── 로고 + 서브카피 ── */}
      <motion.div
        className="flex flex-col items-center gap-4 w-full"
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: 'easeOut' }}
      >
        {/* 워드마크 */}
        <div className="flex flex-col items-center gap-1">
          <h1
            style={{
              fontFamily: 'var(--font-display)',
              fontSize: '52px',
              fontWeight: 800,
              color: 'var(--text-primary)',
              letterSpacing: '-0.02em',
              lineHeight: 1,
              margin: 0,
            }}
          >
            ColorFit
          </h1>
          <ColorStrip />
        </div>

        {/* 서브카피 */}
        <p
          style={{
            fontFamily: 'var(--font-body)',
            fontSize: '15px',
            color: 'var(--text-secondary)',
            lineHeight: 1.6,
            textAlign: 'center',
            margin: 0,
          }}
        >
          내 퍼스널컬러에 딱 맞는 코디를
          <br />AI가 골라드려요
        </p>
      </motion.div>

      {/* ── 에디토리얼 장식 ── */}
      <motion.div
        className="flex flex-col items-center gap-3"
        initial={{ opacity: 0, scale: 0.92 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: 0.25, duration: 0.5, ease: 'easeOut' }}
      >
        {/* 시즌 컬러 팔레트 카드 */}
        <div
          className="grid grid-cols-4 gap-2"
          style={{ padding: '20px', background: 'var(--surface)', borderRadius: 'var(--radius-xl)', border: '1px solid var(--border)' }}
        >
          {[
            { label: 'Spring', swatches: ['#F7D9C4', '#F2C4A0', '#E8B88A', '#F9E4D4'] },
            { label: 'Summer', swatches: ['#C4D9E0', '#A8C8D4', '#8CB8C8', '#D8ECF0'] },
            { label: 'Autumn', swatches: ['#C4A882', '#B8926A', '#A07850', '#D4BC98'] },
            { label: 'Winter', swatches: ['#8BA3BA', '#6888A4', '#4A6C8C', '#AABFCF'] },
          ].map((season, si) => (
            <motion.div
              key={season.label}
              className="flex flex-col items-center gap-2"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.35 + si * 0.08, duration: 0.35 }}
            >
              {season.swatches.map((color, ci) => (
                <div
                  key={ci}
                  style={{
                    width: 40,
                    height: 40,
                    borderRadius: 'var(--radius-sm)',
                    background: color,
                  }}
                />
              ))}
              <span
                style={{
                  fontFamily: 'var(--font-body)',
                  fontSize: '10px',
                  color: 'var(--text-tertiary)',
                  fontWeight: 500,
                }}
              >
                {season.label}
              </span>
            </motion.div>
          ))}
        </div>
      </motion.div>

      {/* ── 로그인 버튼 영역 ── */}
      <motion.div
        className="flex flex-col gap-3 w-full"
        style={{ maxWidth: 360 }}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.45, duration: 0.4, ease: 'easeOut' }}
      >
        {/* 카카오 로그인 */}
        <button
          type="button"
          onClick={handleKakao}
          style={{
            width: '100%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 10,
            padding: '15px',
            borderRadius: 'var(--radius-md)',
            background: '#FEE500',
            border: 'none',
            fontFamily: 'var(--font-body)',
            fontSize: '15px',
            fontWeight: 600,
            color: '#191919',
            cursor: 'pointer',
            WebkitTapHighlightColor: 'transparent',
          }}
        >
          <KakaoIcon />
          카카오로 시작하기
        </button>

        {/* 구글 로그인 */}
        <button
          type="button"
          onClick={handleGoogle}
          style={{
            width: '100%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: 10,
            padding: '15px',
            borderRadius: 'var(--radius-md)',
            background: '#FFFFFF',
            border: '1px solid var(--border)',
            fontFamily: 'var(--font-body)',
            fontSize: '15px',
            fontWeight: 600,
            color: '#222222',
            cursor: 'pointer',
            WebkitTapHighlightColor: 'transparent',
          }}
        >
          <GoogleIcon />
          구글로 시작하기
        </button>

        {/* 구분선 */}
        <div className="flex items-center gap-3">
          <div style={{ flex: 1, height: 1, background: 'var(--border)' }} />
          <span
            style={{
              fontFamily: 'var(--font-body)',
              fontSize: '12px',
              color: 'var(--text-tertiary)',
            }}
          >
            또는
          </span>
          <div style={{ flex: 1, height: 1, background: 'var(--border)' }} />
        </div>

        {/* 게스트로 둘러보기 */}
        <button
          type="button"
          onClick={handleGuest}
          style={{
            background: 'none',
            border: 'none',
            fontFamily: 'var(--font-body)',
            fontSize: '14px',
            fontWeight: 500,
            color: 'var(--text-secondary)',
            cursor: 'pointer',
            textDecoration: 'underline',
            textUnderlineOffset: '3px',
            WebkitTapHighlightColor: 'transparent',
            padding: '4px 0',
          }}
        >
          게스트로 둘러보기
        </button>

        {/* 약관 안내 */}
        <p
          style={{
            fontFamily: 'var(--font-body)',
            fontSize: '11px',
            color: 'var(--text-tertiary)',
            textAlign: 'center',
            lineHeight: 1.6,
            margin: 0,
          }}
        >
          로그인 시 서비스 이용약관 및 개인정보처리방침에
          <br />동의하는 것으로 간주됩니다
        </p>
      </motion.div>

      {/* ── 토스트 ── */}
      <AnimatePresence>
        {toast && <Toast message={toast} />}
      </AnimatePresence>
    </div>
  )
}
