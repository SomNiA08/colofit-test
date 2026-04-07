'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'

// ── 타입 ─────────────────────────────────────────────────────────────────────

type Gender = 'female' | 'male'

interface TpoItem {
  id: string
  label: string
}

interface MoodItem {
  id: string
  label: string
}

// ── 데이터 ───────────────────────────────────────────────────────────────────

const FEMALE_TPO: TpoItem[] = [
  { id: 'commute', label: '출근' },
  { id: 'date',    label: '데이트' },
  { id: 'interview', label: '면접' },
  { id: 'weekend', label: '주말' },
  { id: 'campus',  label: '캠퍼스' },
  { id: 'travel',  label: '여행' },
  { id: 'event',   label: '행사' },
  { id: 'workout', label: '운동' },
]

const MALE_TPO: TpoItem[] = [
  { id: 'commute',   label: '출근' },
  { id: 'date',      label: '데이트' },
  { id: 'interview', label: '면접' },
  { id: 'weekend',   label: '주말' },
  { id: 'campus',    label: '캠퍼스' },
  { id: 'travel',    label: '여행' },
  { id: 'event',     label: '행사' },
  { id: 'workout',   label: '운동' },
]

const FEMALE_MOOD: MoodItem[] = [
  { id: 'casual',     label: '캐주얼' },
  { id: 'minimal',    label: '미니멀' },
  { id: 'lovely',     label: '러블리' },
  { id: 'classic',    label: '클래식' },
  { id: 'street',     label: '스트릿' },
  { id: 'editorial',  label: '에디토리얼' },
]

const MALE_MOOD: MoodItem[] = [
  { id: 'casual',    label: '캐주얼' },
  { id: 'minimal',   label: '미니멀' },
  { id: 'dandy',     label: '댄디' },
  { id: 'classic',   label: '클래식' },
  { id: 'street',    label: '스트릿' },
  { id: 'amekaji',   label: '아메카지' },
]

// tone id → hex 매핑 (step2 데이터와 동일)
const TONE_HEX: Record<string, string> = {
  spring_warm_light:   '#FFCBA4',
  spring_warm_bright:  '#FF8066',
  spring_warm_mute:    '#D4A574',
  summer_cool_light:   '#9FB5D4',
  summer_cool_soft:    '#B0A6C6',
  summer_cool_mute:    '#8B8B9E',
  autumn_warm_bright:  '#D4722A',
  autumn_warm_mute:    '#A0856C',
  autumn_warm_deep:    '#8B5A2B',
  winter_cool_bright:  '#CC0066',
  winter_cool_deep:    '#2A2A5E',
  winter_cool_light:   '#C8C8E8',
}

const TONE_NAME: Record<string, string> = {
  spring_warm_light:   '봄웜라이트',
  spring_warm_bright:  '봄웜브라이트',
  spring_warm_mute:    '봄웜뮤트',
  summer_cool_light:   '여름쿨라이트',
  summer_cool_soft:    '여름쿨소프트',
  summer_cool_mute:    '여름쿨뮤트',
  autumn_warm_bright:  '가을웜브라이트',
  autumn_warm_mute:    '가을웜뮤트',
  autumn_warm_deep:    '가을웜딥',
  winter_cool_bright:  '겨울쿨브라이트',
  winter_cool_deep:    '겨울쿨딥',
  winter_cool_light:   '겨울쿨라이트',
}

const MAX_TPO  = 3
const MAX_MOOD = 5

// ── 메인 페이지 ───────────────────────────────────────────────────────────────

export default function Step3Page() {
  const router = useRouter()
  const [gender, setGender]       = useState<Gender>('female')
  const [toneId, setToneId]       = useState<string | null>(null)
  const [selectedTpo,  setSelectedTpo]  = useState<string[]>([])
  const [selectedMood, setSelectedMood] = useState<string[]>([])

  // localStorage에서 성별·톤 읽기
  useEffect(() => {
    const g = localStorage.getItem('onboarding_gender') as Gender | null
    if (g) setGender(g)
    const t = localStorage.getItem('onboarding_tone_id')
    if (t) setToneId(t)
  }, [])

  const tpoList  = gender === 'female' ? FEMALE_TPO  : MALE_TPO
  const moodList = gender === 'female' ? FEMALE_MOOD : MALE_MOOD

  const toggleTpo = (id: string) => {
    setSelectedTpo((prev) => {
      if (prev.includes(id)) return prev.filter((x) => x !== id)
      if (prev.length >= MAX_TPO) return prev
      return [...prev, id]
    })
  }

  const toggleMood = (id: string) => {
    setSelectedMood((prev) => {
      if (prev.includes(id)) return prev.filter((x) => x !== id)
      if (prev.length >= MAX_MOOD) return prev
      return [...prev, id]
    })
  }

  const canProceed = selectedTpo.length > 0

  const handleNext = () => {
    if (!canProceed) return
    localStorage.setItem('onboarding_tpo',  JSON.stringify(selectedTpo))
    localStorage.setItem('onboarding_mood', JSON.stringify(selectedMood))
    router.push('/onboarding/step4')
  }

  const toneHex  = toneId ? (TONE_HEX[toneId]  ?? '#D4A574') : null
  const toneName = toneId ? (TONE_NAME[toneId]  ?? toneId)   : null

  return (
    <div className="flex flex-col flex-1 px-5 pt-4 pb-8">

      {/* ── 상단 맥락: 퍼스널컬러 칩 ───────────────────── */}
      {toneHex && toneName && (
        <motion.div
          className="flex items-center gap-2 mb-5"
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, ease: 'easeOut' }}
        >
          <div
            aria-hidden="true"
            style={{
              width: 24,
              height: 24,
              borderRadius: '50%',
              background: toneHex,
              border: '1.5px solid var(--border)',
              flexShrink: 0,
            }}
          />
          <span
            style={{
              fontFamily: 'var(--font-body)',
              fontSize: '13px',
              color: 'var(--text-secondary)',
            }}
          >
            {toneName}
          </span>
        </motion.div>
      )}

      {/* ── 헤드라인 ──────────────────────────────────── */}
      <motion.div
        className="mb-6"
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: 'easeOut', delay: 0.05 }}
      >
        <h1
          style={{
            fontFamily: 'var(--font-display)',
            fontSize: '24px',
            fontWeight: 700,
            color: 'var(--text-primary)',
            lineHeight: 1.3,
          }}
        >
          어떤 상황의 코디를 찾으세요?
        </h1>
        <p
          style={{
            fontFamily: 'var(--font-body)',
            fontSize: '15px',
            color: 'var(--text-secondary)',
            marginTop: '6px',
          }}
        >
          최대 {MAX_TPO}개 선택할 수 있어요
        </p>
      </motion.div>

      {/* ── TPO 필 버튼 (가로 스크롤) ────────────────── */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: 'easeOut', delay: 0.1 }}
      >
        <div
          className="flex gap-2 flex-wrap"
          role="group"
          aria-label="TPO 선택"
        >
          {tpoList.map((tpo) => {
            const isSelected = selectedTpo.includes(tpo.id)
            return (
              <motion.button
                key={tpo.id}
                type="button"
                onClick={() => toggleTpo(tpo.id)}
                whileTap={{ scale: 0.96 }}
                transition={{ duration: 0.15 }}
                aria-pressed={isSelected}
                style={{
                  padding: '9px 16px',
                  borderRadius: '9999px',
                  border: `1.5px solid ${isSelected ? 'var(--accent)' : '#E0DCD7'}`,
                  background: isSelected ? 'var(--accent)' : '#FFFFFF',
                  color: isSelected ? '#FFFFFF' : 'var(--text-primary)',
                  fontFamily: 'var(--font-body)',
                  fontSize: '14px',
                  fontWeight: isSelected ? 600 : 400,
                  cursor: 'pointer',
                  WebkitTapHighlightColor: 'transparent',
                  transition: 'background 0.2s, border-color 0.2s, color 0.2s',
                }}
              >
                {tpo.label}
              </motion.button>
            )
          })}
        </div>

        {/* 선택 개수 */}
        <p
          style={{
            fontFamily: 'var(--font-body)',
            fontSize: '12px',
            color: 'var(--text-tertiary)',
            marginTop: '8px',
          }}
        >
          {selectedTpo.length} / {MAX_TPO}
        </p>
      </motion.div>

      {/* ── 무드 태그 클라우드 ─────────────────────────── */}
      <motion.div
        className="mt-8"
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: 'easeOut', delay: 0.18 }}
      >
        <h2
          style={{
            fontFamily: 'var(--font-display)',
            fontSize: '18px',
            fontWeight: 700,
            color: 'var(--text-primary)',
            marginBottom: '4px',
          }}
        >
          분위기도 골라보세요
        </h2>
        <p
          style={{
            fontFamily: 'var(--font-body)',
            fontSize: '13px',
            color: 'var(--text-secondary)',
            marginBottom: '14px',
          }}
        >
          최대 {MAX_MOOD}개, 선택 안 해도 돼요
        </p>

        <div
          className="flex gap-x-5 gap-y-3 flex-wrap"
          role="group"
          aria-label="무드 선택"
        >
          {moodList.map((mood, i) => {
            const isSelected = selectedMood.includes(mood.id)
            return (
              <motion.button
                key={mood.id}
                type="button"
                onClick={() => toggleMood(mood.id)}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, ease: 'easeOut', delay: 0.2 + i * 0.05 }}
                whileTap={{ scale: 0.95 }}
                aria-pressed={isSelected}
                style={{
                  background: 'none',
                  border: 'none',
                  padding: '2px 0',
                  cursor: 'pointer',
                  fontFamily: 'var(--font-body)',
                  fontSize: '16px',
                  fontWeight: isSelected ? 700 : 400,
                  color: isSelected ? 'var(--accent)' : 'var(--text-primary)',
                  textDecoration: isSelected ? 'underline' : 'none',
                  textDecorationColor: 'var(--accent)',
                  textUnderlineOffset: '4px',
                  textDecorationThickness: '2px',
                  transition: 'color 0.2s, font-weight 0.1s',
                  WebkitTapHighlightColor: 'transparent',
                }}
              >
                {mood.label}
              </motion.button>
            )
          })}
        </div>

        {/* 선택 개수 */}
        <p
          style={{
            fontFamily: 'var(--font-body)',
            fontSize: '12px',
            color: 'var(--text-tertiary)',
            marginTop: '10px',
          }}
        >
          {selectedMood.length} / {MAX_MOOD}
        </p>
      </motion.div>

      {/* ── 다음 버튼 ─────────────────────────────────── */}
      <div className="mt-auto pt-6">
        <motion.button
          type="button"
          onClick={handleNext}
          disabled={!canProceed}
          animate={{ opacity: canProceed ? 1 : 0.45 }}
          transition={{ duration: 0.2 }}
          className="w-full"
          style={{
            padding: '16px',
            borderRadius: 'var(--radius-lg)',
            background: canProceed ? 'var(--accent)' : '#C8C4BC',
            color: '#FFFFFF',
            fontFamily: 'var(--font-body)',
            fontSize: '16px',
            fontWeight: 600,
            border: 'none',
            cursor: canProceed ? 'pointer' : 'not-allowed',
            transition: 'background 0.25s',
          }}
        >
          다음
        </motion.button>
      </div>

    </div>
  )
}
