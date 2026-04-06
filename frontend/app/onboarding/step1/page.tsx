'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'

type Gender = 'female' | 'male'

interface GenderCard {
  gender: Gender
  label: string
  glyph: string
}

const GENDER_CARDS: GenderCard[] = [
  { gender: 'female', label: '여성', glyph: 'W' },
  { gender: 'male',   label: '남성', glyph: 'M' },
]

export default function Step1Page() {
  const router = useRouter()
  const [selected, setSelected] = useState<Gender | null>(null)

  const proceed = (gender: Gender) => {
    localStorage.setItem('onboarding_gender', gender)
    router.push('/onboarding/step2')
  }

  const handleSelect = (gender: Gender) => {
    if (selected !== null) return
    setSelected(gender)
    // 선택 애니메이션이 끝난 뒤 자동 전환
    setTimeout(() => proceed(gender), 400)
  }

  const handleSkip = () => {
    proceed('female')
  }

  return (
    <div className="flex flex-col flex-1 px-5 pt-8 pb-10">

      {/* ── 헤드라인 ──────────────────────────────────── */}
      <motion.div
        className="mb-10 text-center"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: 'easeOut' }}
      >
        <h1
          style={{
            fontFamily: 'var(--font-display)',
            fontSize: '28px',
            fontWeight: 700,
            color: 'var(--text-primary)',
            lineHeight: 1.25,
          }}
        >
          나에 대해 알려주세요
        </h1>
        <p
          style={{
            fontFamily: 'var(--font-body)',
            fontSize: '15px',
            color: 'var(--text-secondary)',
            marginTop: '8px',
          }}
        >
          맞춤 코디를 위해 필요해요
        </p>
      </motion.div>

      {/* ── 성별 카드 (가로 배치, 3:4 비율) ─────────────── */}
      <div className="flex gap-4 justify-center">
        {GENDER_CARDS.map(({ gender, label, glyph }, i) => {
          const isSelected = selected === gender
          return (
            <motion.button
              key={gender}
              type="button"
              onClick={() => handleSelect(gender)}
              disabled={selected !== null}
              className="w-[45%] aspect-[3/4] flex flex-col items-center justify-center gap-3"
              style={{
                borderRadius: 'var(--radius-xl)',
                background: '#FFFFFF',
                border: `2px solid ${isSelected ? 'var(--accent)' : 'var(--border)'}`,
                cursor: selected !== null ? 'default' : 'pointer',
                transition: 'border-color 0.2s, color 0.2s',
                WebkitTapHighlightColor: 'transparent',
              }}
              // 진입 애니메이션 (fadeInUp, stagger)
              initial={{ opacity: 0, y: 30 }}
              animate={{
                opacity: 1,
                y: 0,
                scale: isSelected ? 1.05 : 1,
              }}
              transition={{
                opacity: { duration: 0.4, ease: 'easeOut', delay: 0.1 + i * 0.15 },
                y:       { duration: 0.4, ease: 'easeOut', delay: 0.1 + i * 0.15 },
                scale:   { duration: 0.3, ease: 'easeOut' },
              }}
            >
              {/* 성별 기호 */}
              <span
                aria-hidden="true"
                style={{
                  fontFamily: 'var(--font-display)',
                  fontSize: '56px',
                  fontWeight: 700,
                  lineHeight: 1,
                  color: isSelected ? 'var(--accent)' : 'var(--text-primary)',
                  transition: 'color 0.2s',
                }}
              >
                {glyph}
              </span>

              {/* 성별 레이블 */}
              <span
                style={{
                  fontFamily: 'var(--font-body)',
                  fontSize: '16px',
                  fontWeight: 500,
                  color: isSelected ? 'var(--accent)' : 'var(--text-secondary)',
                  transition: 'color 0.2s',
                }}
              >
                {label}
              </span>
            </motion.button>
          )
        })}
      </div>

      {/* ── 건너뛰기 ──────────────────────────────────── */}
      <motion.div
        className="mt-auto pt-8 text-center"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5, duration: 0.3 }}
      >
        <button
          type="button"
          onClick={handleSkip}
          style={{
            fontFamily: 'var(--font-body)',
            fontSize: '14px',
            color: 'var(--text-secondary)',
            textDecoration: 'underline',
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            padding: '8px',
          }}
        >
          건너뛰기
        </button>
      </motion.div>

    </div>
  )
}
