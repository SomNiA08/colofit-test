'use client'

import { useState, useCallback, useRef } from 'react'
import { useRouter } from 'next/navigation'
import { motion } from 'framer-motion'

// ── 상수 ─────────────────────────────────────────────────────────────────────

const MIN_BUDGET = 0
const MAX_BUDGET = 300000
const STEP       = 5000

interface Preset {
  label: string
  min: number
  max: number
}

const PRESETS: Preset[] = [
  { label: '~3만원',    min: 0,      max: 30000  },
  { label: '3~7만원',  min: 30000,  max: 70000  },
  { label: '7~15만원', min: 70000,  max: 150000 },
  { label: '15만원~',  min: 150000, max: MAX_BUDGET },
]

// ── 유틸 ─────────────────────────────────────────────────────────────────────

function formatWon(value: number): string {
  if (value === 0) return '0원'
  if (value >= 10000) {
    const man = Math.floor(value / 10000)
    const remainder = value % 10000
    if (remainder === 0) return `${man}만원`
    return `${man}만 ${remainder.toLocaleString()}원`
  }
  return `${value.toLocaleString()}원`
}

function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value))
}

function snapToStep(value: number): number {
  return Math.round(value / STEP) * STEP
}

// ── 듀얼 썸 슬라이더 ──────────────────────────────────────────────────────────

interface DualSliderProps {
  minVal: number
  maxVal: number
  onChange: (min: number, max: number) => void
}

function DualSlider({ minVal, maxVal, onChange }: DualSliderProps) {
  const trackRef = useRef<HTMLDivElement>(null)

  // 퍼센트 변환
  const toPercent = (v: number) => ((v - MIN_BUDGET) / (MAX_BUDGET - MIN_BUDGET)) * 100
  const fromPercent = (pct: number) =>
    snapToStep(clamp(MIN_BUDGET + (pct / 100) * (MAX_BUDGET - MIN_BUDGET), MIN_BUDGET, MAX_BUDGET))

  // 트랙 좌표 → 값
  const coordToValue = useCallback((clientX: number): number => {
    const track = trackRef.current
    if (!track) return 0
    const rect = track.getBoundingClientRect()
    const pct = clamp(((clientX - rect.left) / rect.width) * 100, 0, 100)
    return fromPercent(pct)
  }, [])

  // ── 드래그 핸들러 생성 ──────────────────────────────────────────────────────
  const makeDragHandlers = (thumb: 'min' | 'max') => {
    const onMove = (clientX: number) => {
      const val = coordToValue(clientX)
      if (thumb === 'min') {
        onChange(clamp(val, MIN_BUDGET, maxVal - STEP), maxVal)
      } else {
        onChange(minVal, clamp(val, minVal + STEP, MAX_BUDGET))
      }
    }

    const onPointerDown = (e: React.PointerEvent) => {
      e.preventDefault()
      const target = e.currentTarget as HTMLElement
      target.setPointerCapture(e.pointerId)
      onMove(e.clientX)

      const handleMove = (ev: PointerEvent) => onMove(ev.clientX)
      const handleUp   = () => {
        target.removeEventListener('pointermove', handleMove as EventListener)
        target.removeEventListener('pointerup',   handleUp)
      }
      target.addEventListener('pointermove', handleMove as EventListener)
      target.addEventListener('pointerup',   handleUp)
    }

    return { onPointerDown }
  }

  const minPct = toPercent(minVal)
  const maxPct = toPercent(maxVal)

  return (
    <div className="relative" style={{ paddingTop: 20, paddingBottom: 20 }}>
      {/* 트랙 배경 */}
      <div
        ref={trackRef}
        className="relative h-1.5 rounded-full"
        style={{ background: 'var(--border)' }}
      >
        {/* 선택 범위 하이라이트 */}
        <div
          className="absolute h-full rounded-full"
          style={{
            left: `${minPct}%`,
            width: `${maxPct - minPct}%`,
            background: 'var(--accent)',
            transition: 'left 0.05s, width 0.05s',
          }}
        />

        {/* Min 썸 */}
        <motion.div
          {...makeDragHandlers('min')}
          role="slider"
          aria-label="최소 예산"
          aria-valuenow={minVal}
          aria-valuemin={MIN_BUDGET}
          aria-valuemax={maxVal - STEP}
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === 'ArrowLeft')  onChange(clamp(minVal - STEP, MIN_BUDGET, maxVal - STEP), maxVal)
            if (e.key === 'ArrowRight') onChange(clamp(minVal + STEP, MIN_BUDGET, maxVal - STEP), maxVal)
          }}
          whileTap={{ scale: 1.2 }}
          style={{
            position: 'absolute',
            top: '50%',
            left: `${minPct}%`,
            transform: 'translate(-50%, -50%)',
            width: 28,
            height: 28,
            borderRadius: '50%',
            background: '#FFFFFF',
            border: '2.5px solid var(--accent)',
            boxShadow: '0 2px 8px rgba(150,79,76,0.25)',
            cursor: 'grab',
            touchAction: 'none',
            userSelect: 'none',
            zIndex: minPct > 90 ? 3 : 2,
          }}
        />

        {/* Max 썸 */}
        <motion.div
          {...makeDragHandlers('max')}
          role="slider"
          aria-label="최대 예산"
          aria-valuenow={maxVal}
          aria-valuemin={minVal + STEP}
          aria-valuemax={MAX_BUDGET}
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === 'ArrowLeft')  onChange(minVal, clamp(maxVal - STEP, minVal + STEP, MAX_BUDGET))
            if (e.key === 'ArrowRight') onChange(minVal, clamp(maxVal + STEP, minVal + STEP, MAX_BUDGET))
          }}
          whileTap={{ scale: 1.2 }}
          style={{
            position: 'absolute',
            top: '50%',
            left: `${maxPct}%`,
            transform: 'translate(-50%, -50%)',
            width: 28,
            height: 28,
            borderRadius: '50%',
            background: '#FFFFFF',
            border: '2.5px solid var(--accent)',
            boxShadow: '0 2px 8px rgba(150,79,76,0.25)',
            cursor: 'grab',
            touchAction: 'none',
            userSelect: 'none',
            zIndex: 2,
          }}
        />
      </div>

      {/* 눈금 레이블 */}
      <div
        className="flex justify-between mt-3"
        style={{ fontFamily: 'var(--font-body)', fontSize: '11px', color: 'var(--text-tertiary)' }}
      >
        <span>0원</span>
        <span>15만원</span>
        <span>30만원</span>
      </div>
    </div>
  )
}

// ── 메인 페이지 ───────────────────────────────────────────────────────────────

export default function Step4Page() {
  const router = useRouter()

  const [minBudget, setMinBudget] = useState(0)
  const [maxBudget, setMaxBudget] = useState(100000)
  const [activePreset, setActivePreset] = useState<number | null>(null)

  const handleSliderChange = (min: number, max: number) => {
    setMinBudget(min)
    setMaxBudget(max)
    setActivePreset(null)
  }

  const handlePreset = (index: number, preset: Preset) => {
    setMinBudget(preset.min)
    setMaxBudget(preset.max)
    setActivePreset(index)
  }

  const handleFinish = () => {
    localStorage.setItem('onboarding_budget_min', String(minBudget))
    localStorage.setItem('onboarding_budget_max', String(maxBudget))
    router.push('/onboarding/step5')
  }

  const isMaxOpen = maxBudget >= MAX_BUDGET

  // 표시 텍스트 생성
  const rangeText = isMaxOpen
    ? `${formatWon(minBudget)} 이상`
    : `${formatWon(minBudget)} ~ ${formatWon(maxBudget)}`

  return (
    <div className="flex flex-col flex-1 px-5 pt-4 pb-8">

      {/* ── 헤드라인 ──────────────────────────────────── */}
      <motion.div
        className="mb-8"
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: 'easeOut' }}
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
          예산은 어느 정도예요?
        </h1>
        <p
          style={{
            fontFamily: 'var(--font-body)',
            fontSize: '15px',
            color: 'var(--text-secondary)',
            marginTop: '6px',
          }}
        >
          코디 한 벌 기준이에요
        </p>
      </motion.div>

      {/* ── 선택된 금액 표시 ─────────────────────────── */}
      <motion.div
        className="mb-6"
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: 'easeOut', delay: 0.07 }}
      >
        <div
          className="rounded-xl flex items-center justify-center"
          style={{
            background: 'var(--surface)',
            padding: '20px 24px',
            border: '1px solid var(--border)',
          }}
        >
          <motion.span
            key={rangeText}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.2 }}
            style={{
              fontFamily: 'var(--font-display)',
              fontSize: '22px',
              fontWeight: 700,
              color: 'var(--accent)',
              letterSpacing: '-0.02em',
            }}
          >
            {rangeText}
          </motion.span>
        </div>
      </motion.div>

      {/* ── 듀얼 슬라이더 ───────────────────────────── */}
      <motion.div
        className="mb-8"
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: 'easeOut', delay: 0.12 }}
      >
        <DualSlider
          minVal={minBudget}
          maxVal={maxBudget}
          onChange={handleSliderChange}
        />
      </motion.div>

      {/* ── 빠른 프리셋 버튼 ─────────────────────────── */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: 'easeOut', delay: 0.18 }}
      >
        <p
          style={{
            fontFamily: 'var(--font-body)',
            fontSize: '13px',
            color: 'var(--text-secondary)',
            marginBottom: '10px',
          }}
        >
          빠른 선택
        </p>
        <div className="grid grid-cols-2 gap-2">
          {PRESETS.map((preset, i) => {
            const isActive = activePreset === i
            return (
              <motion.button
                key={preset.label}
                type="button"
                onClick={() => handlePreset(i, preset)}
                whileTap={{ scale: 0.97 }}
                transition={{ duration: 0.12 }}
                style={{
                  padding: '12px 16px',
                  borderRadius: 'var(--radius-md)',
                  border: `1.5px solid ${isActive ? 'var(--accent)' : 'var(--border)'}`,
                  background: isActive ? 'rgba(150,79,76,0.08)' : '#FFFFFF',
                  color: isActive ? 'var(--accent)' : 'var(--text-primary)',
                  fontFamily: 'var(--font-body)',
                  fontSize: '14px',
                  fontWeight: isActive ? 600 : 400,
                  cursor: 'pointer',
                  WebkitTapHighlightColor: 'transparent',
                  transition: 'border-color 0.2s, background 0.2s, color 0.2s',
                  textAlign: 'center' as const,
                }}
              >
                {preset.label}
              </motion.button>
            )
          })}
        </div>
      </motion.div>

      {/* ── CTA 버튼 ──────────────────────────────────── */}
      <div className="mt-auto pt-8">
        <motion.button
          type="button"
          onClick={handleFinish}
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, ease: 'easeOut', delay: 0.25 }}
          whileTap={{ scale: 0.98 }}
          className="w-full"
          style={{
            padding: '17px',
            borderRadius: 'var(--radius-lg)',
            background: 'var(--accent)',
            color: '#FFFFFF',
            fontFamily: 'var(--font-body)',
            fontSize: '16px',
            fontWeight: 600,
            border: 'none',
            cursor: 'pointer',
            boxShadow: '0 4px 16px rgba(150,79,76,0.3)',
            transition: 'box-shadow 0.2s',
            letterSpacing: '-0.01em',
          }}
        >
          추천 코디 보러가기
        </motion.button>
      </div>

    </div>
  )
}
