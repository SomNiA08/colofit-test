'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import { useBodyScrollLock } from '@/hooks/useBodyScrollLock'

// ── 타입 ─────────────────────────────────────────────────────────────────────

type SeasonKey = 'spring' | 'summer' | 'autumn' | 'winter'

interface ToneData {
  id: string
  name: string
  hex: string
}

interface SeasonData {
  key: SeasonKey
  label: string
  gradient: string
  tones: ToneData[]
}

// ── 시즌 & 톤 데이터 ─────────────────────────────────────────────────────────

const SEASONS: SeasonData[] = [
  {
    key: 'spring',
    label: '봄 웜',
    gradient: 'linear-gradient(to right, #FF9E8A, #FFC8A0, #FFF5E4)',
    tones: [
      { id: 'spring_warm_light',  name: '봄웜라이트',   hex: '#FFCBA4' },
      { id: 'spring_warm_bright', name: '봄웜브라이트', hex: '#FF8066' },
      { id: 'spring_warm_mute',   name: '봄웜뮤트',    hex: '#D4A574' },
    ],
  },
  {
    key: 'summer',
    label: '여름 쿨',
    gradient: 'linear-gradient(to right, #C8B8E8, #98D0E8, #C0E8E0)',
    tones: [
      { id: 'summer_cool_light', name: '여름쿨라이트', hex: '#9FB5D4' },
      { id: 'summer_cool_soft',  name: '여름쿨소프트', hex: '#B0A6C6' },
      { id: 'summer_cool_mute',  name: '여름쿨뮤트',  hex: '#8B8B9E' },
    ],
  },
  {
    key: 'autumn',
    label: '가을 웜',
    gradient: 'linear-gradient(to right, #722F37, #9C4A2C, #D4A574)',
    tones: [
      { id: 'autumn_warm_bright', name: '가을웜브라이트', hex: '#D4722A' },
      { id: 'autumn_warm_mute',   name: '가을웜뮤트',   hex: '#A0856C' },
      { id: 'autumn_warm_deep',   name: '가을웜딥',    hex: '#8B5A2B' },
    ],
  },
  {
    key: 'winter',
    label: '겨울 쿨',
    gradient: 'linear-gradient(to right, #1E1E2E, #1A2898, #E8B4C8)',
    tones: [
      { id: 'winter_cool_bright', name: '겨울쿨브라이트', hex: '#CC0066' },
      { id: 'winter_cool_deep',   name: '겨울쿨딥',    hex: '#2A2A5E' },
      { id: 'winter_cool_light',  name: '겨울쿨라이트', hex: '#C8C8E8' },
    ],
  },
]

// 간이 진단 → 톤 ID 매핑
const DIAGNOSIS_MAP: Record<SeasonKey, Record<string, string>> = {
  spring: { 베이직: 'spring_warm_mute',   어스톤: 'spring_warm_mute',   파스텔: 'spring_warm_light',  비비드: 'spring_warm_bright' },
  summer: { 베이직: 'summer_cool_mute',   어스톤: 'summer_cool_mute',   파스텔: 'summer_cool_light',  비비드: 'summer_cool_soft'   },
  autumn: { 베이직: 'autumn_warm_mute',   어스톤: 'autumn_warm_mute',   파스텔: 'autumn_warm_bright', 비비드: 'autumn_warm_bright' },
  winter: { 베이직: 'winter_cool_deep',   어스톤: 'winter_cool_light',  파스텔: 'winter_cool_light',  비비드: 'winter_cool_bright' },
}

// ── 톤 칩 ────────────────────────────────────────────────────────────────────

interface ToneChipProps {
  tone: ToneData
  isSelected: boolean
  onSelect: () => void
}

function ToneChip({ tone, isSelected, onSelect }: ToneChipProps) {
  return (
    <button
      type="button"
      onClick={onSelect}
      className="flex flex-col items-center gap-1.5"
      style={{ WebkitTapHighlightColor: 'transparent' }}
      aria-label={tone.name}
      aria-pressed={isSelected}
    >
      <motion.div
        animate={{ scale: isSelected ? 1.15 : 1 }}
        transition={{ duration: 0.2, ease: 'easeOut' }}
        style={{
          width: 36,
          height: 36,
          borderRadius: '50%',
          background: tone.hex,
          border: isSelected ? '2.5px solid var(--accent)' : '2.5px solid transparent',
          boxShadow: isSelected
            ? '0 0 0 2px var(--bg), 0 0 0 4px var(--accent)'
            : '0 1px 4px rgba(0,0,0,0.15)',
        }}
      />
      <span
        style={{
          fontSize: '11px',
          lineHeight: 1.4,
          fontFamily: 'var(--font-body)',
          color: isSelected ? 'var(--accent)' : 'var(--text-secondary)',
          fontWeight: isSelected ? 600 : 400,
          textAlign: 'center',
          whiteSpace: 'nowrap',
        }}
      >
        {tone.name}
      </span>
    </button>
  )
}

// ── 시즌 스트립 ───────────────────────────────────────────────────────────────

interface SeasonStripProps {
  season: SeasonData
  isExpanded: boolean
  isDimmed: boolean
  selectedTone: string | null
  onTap: () => void
  onToneSelect: (toneId: string) => void
  delay: number
}

function SeasonStrip({
  season,
  isExpanded,
  isDimmed,
  selectedTone,
  onTap,
  onToneSelect,
  delay,
}: SeasonStripProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: isDimmed ? 0.35 : 1, y: 0 }}
      transition={{
        opacity: { duration: 0.25 },
        y: { duration: 0.4, ease: 'easeOut', delay },
      }}
    >
      {/* 시즌 레이블 */}
      <p
        style={{
          fontSize: '13px',
          fontFamily: 'var(--font-body)',
          fontWeight: 600,
          color: 'var(--text-primary)',
          marginBottom: '6px',
          paddingLeft: '4px',
        }}
      >
        {season.label}
      </p>

      {/* 그라데이션 바 */}
      <motion.button
        type="button"
        onClick={onTap}
        className="w-full rounded-full overflow-hidden"
        animate={{ height: isExpanded ? 56 : 44 }}
        transition={{ duration: 0.3, ease: 'easeOut' }}
        style={{
          background: season.gradient,
          border: isExpanded ? '2px solid var(--accent)' : '2px solid transparent',
          cursor: 'pointer',
          WebkitTapHighlightColor: 'transparent',
          display: 'block',
        }}
        aria-expanded={isExpanded}
        aria-label={`${season.label} 선택`}
      />

      {/* 톤 칩 (확장 시 표시) */}
      <AnimatePresence initial={false}>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.28, ease: 'easeInOut' }}
            style={{ overflow: 'hidden' }}
          >
            <div className="flex justify-around pt-4 pb-1 px-2">
              {season.tones.map((tone) => (
                <ToneChip
                  key={tone.id}
                  tone={tone}
                  isSelected={selectedTone === tone.id}
                  onSelect={() => onToneSelect(tone.id)}
                />
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

// ── 간이 진단 바텀시트 ────────────────────────────────────────────────────────

const Q2_OPTIONS = ['베이직', '어스톤', '파스텔', '비비드'] as const
type Q2Option = typeof Q2_OPTIONS[number]

interface QuickDiagnosisSheetProps {
  onClose: () => void
  onConfirm: (toneId: string, seasonKey: SeasonKey) => void
}

function QuickDiagnosisSheet({ onClose, onConfirm }: QuickDiagnosisSheetProps) {
  const [q1, setQ1] = useState<SeasonKey | null>(null)
  const [q2, setQ2] = useState<Q2Option | null>(null)

  const suggestedToneId = q1 && q2 ? DIAGNOSIS_MAP[q1][q2] : null

  return (
    <>
      {/* 배경 오버레이 */}
      <motion.div
        className="fixed inset-0 z-40"
        style={{ background: 'rgba(0,0,0,0.45)' }}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={onClose}
      />

      {/* 바텀시트 */}
      <motion.div
        className="fixed bottom-0 z-50 flex flex-col"
        style={{
          left: 'var(--app-offset)',
          right: 'var(--app-offset)',
          background: 'var(--bg)',
          borderRadius: '20px 20px 0 0',
          maxHeight: 'var(--sheet-max-h-85)',
          overflowY: 'auto',
          paddingBottom: 'env(safe-area-inset-bottom, 24px)',
        }}
        initial={{ y: '100%' }}
        animate={{ y: 0 }}
        exit={{ y: '100%' }}
        transition={{ type: 'spring', stiffness: 300, damping: 30 }}
      >
        {/* 핸들 바 */}
        <div className="flex justify-center pt-3 pb-4">
          <div
            style={{
              width: 36,
              height: 4,
              borderRadius: 2,
              background: 'var(--border)',
            }}
          />
        </div>

        <div className="px-5 pb-6">
          {/* Q1 */}
          <h3
            style={{
              fontFamily: 'var(--font-display)',
              fontSize: '17px',
              fontWeight: 700,
              color: 'var(--text-primary)',
              marginBottom: '12px',
            }}
          >
            피부톤에 가장 가까운 것은?
          </h3>
          <div className="grid grid-cols-4 gap-2">
            {SEASONS.map((s) => (
              <button
                key={s.key}
                type="button"
                onClick={() => setQ1(s.key)}
                className="flex flex-col items-center gap-1.5"
                style={{ WebkitTapHighlightColor: 'transparent' }}
              >
                <div
                  style={{
                    width: '100%',
                    height: 52,
                    borderRadius: 10,
                    background: s.gradient,
                    border: q1 === s.key ? '2px solid var(--accent)' : '2px solid var(--border)',
                    transition: 'border-color 0.2s',
                  }}
                />
                <span
                  style={{
                    fontSize: '12px',
                    fontFamily: 'var(--font-body)',
                    color: q1 === s.key ? 'var(--accent)' : 'var(--text-secondary)',
                    fontWeight: q1 === s.key ? 600 : 400,
                  }}
                >
                  {s.label}
                </span>
              </button>
            ))}
          </div>

          {/* Q2 */}
          <h3
            style={{
              fontFamily: 'var(--font-display)',
              fontSize: '17px',
              fontWeight: 700,
              color: 'var(--text-primary)',
              marginTop: '24px',
              marginBottom: '12px',
            }}
          >
            자주 입는 상의 색 계열은?
          </h3>
          <div className="grid grid-cols-4 gap-2">
            {Q2_OPTIONS.map((opt) => (
              <button
                key={opt}
                type="button"
                onClick={() => setQ2(opt)}
                style={{
                  padding: '10px 4px',
                  borderRadius: 10,
                  border: q2 === opt ? '2px solid var(--accent)' : '2px solid var(--border)',
                  background: q2 === opt ? 'rgba(150,79,76,0.06)' : 'transparent',
                  fontFamily: 'var(--font-body)',
                  fontSize: '13px',
                  fontWeight: q2 === opt ? 600 : 400,
                  color: q2 === opt ? 'var(--accent)' : 'var(--text-primary)',
                  cursor: 'pointer',
                  transition: 'border-color 0.2s, color 0.2s',
                  WebkitTapHighlightColor: 'transparent',
                }}
              >
                {opt}
              </button>
            ))}
          </div>

          {/* 확인 버튼 */}
          <AnimatePresence>
            {suggestedToneId && q1 && (
              <motion.button
                type="button"
                onClick={() => onConfirm(suggestedToneId, q1)}
                className="w-full mt-6"
                style={{
                  padding: '16px',
                  borderRadius: 'var(--radius-lg)',
                  background: 'var(--accent)',
                  color: '#FFFFFF',
                  fontFamily: 'var(--font-body)',
                  fontSize: '16px',
                  fontWeight: 600,
                  border: 'none',
                  cursor: 'pointer',
                }}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 8 }}
                transition={{ duration: 0.2 }}
              >
                이 톤으로 시작하기
              </motion.button>
            )}
          </AnimatePresence>
        </div>
      </motion.div>
    </>
  )
}

// ── 메인 페이지 ───────────────────────────────────────────────────────────────

export default function Step2Page() {
  const router = useRouter()
  const [expandedSeason, setExpandedSeason] = useState<SeasonKey | null>(null)
  const [selectedTone, setSelectedTone] = useState<string | null>(null)
  const [showDiagnosis, setShowDiagnosis] = useState(false)
  useBodyScrollLock(showDiagnosis)

  const handleSeasonTap = (key: SeasonKey) => {
    setExpandedSeason((prev) => (prev === key ? null : key))
  }

  const handleToneSelect = (toneId: string, seasonKey: SeasonKey) => {
    setSelectedTone(toneId)
    setExpandedSeason(seasonKey)
  }

  const handleDiagnosisConfirm = (toneId: string, seasonKey: SeasonKey) => {
    setSelectedTone(toneId)
    setExpandedSeason(seasonKey)
    setShowDiagnosis(false)
  }

  const handleNext = () => {
    if (!selectedTone) return
    localStorage.setItem('onboarding_tone_id', selectedTone)
    router.push('/onboarding/step3')
  }

  const anySeasonExpanded = expandedSeason !== null

  return (
    <div className="flex flex-col flex-1 px-5 pt-4 pb-8">

      {/* ── 헤드라인 ──────────────────────────────────── */}
      <motion.div
        className="mb-6"
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
          퍼스널컬러를 알려주세요
        </h1>
        <p
          style={{
            fontFamily: 'var(--font-body)',
            fontSize: '15px',
            color: 'var(--text-secondary)',
            marginTop: '6px',
          }}
        >
          잘 어울리는 컬러 계열을 골라보세요
        </p>
      </motion.div>

      {/* ── 시즌 스트립 목록 ───────────────────────────── */}
      <div className="flex flex-col gap-4">
        {SEASONS.map((season, i) => (
          <SeasonStrip
            key={season.key}
            season={season}
            isExpanded={expandedSeason === season.key}
            isDimmed={anySeasonExpanded && expandedSeason !== season.key}
            selectedTone={selectedTone}
            onTap={() => handleSeasonTap(season.key)}
            onToneSelect={(id) => handleToneSelect(id, season.key)}
            delay={i * 0.07}
          />
        ))}
      </div>

      {/* ── 잘 모르겠어요 ─────────────────────────────── */}
      <motion.div
        className="mt-5 text-center"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.4, duration: 0.3 }}
      >
        <button
          type="button"
          onClick={() => setShowDiagnosis(true)}
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
          잘 모르겠어요
        </button>
      </motion.div>

      {/* ── 다음 버튼 ─────────────────────────────────── */}
      <div className="mt-auto pt-6">
        <motion.button
          type="button"
          onClick={handleNext}
          disabled={!selectedTone}
          className="w-full"
          animate={{ opacity: selectedTone ? 1 : 0.45 }}
          transition={{ duration: 0.2 }}
          style={{
            padding: '16px',
            borderRadius: 'var(--radius-lg)',
            background: selectedTone ? 'var(--accent)' : '#C8C4BC',
            color: '#FFFFFF',
            fontFamily: 'var(--font-body)',
            fontSize: '16px',
            fontWeight: 600,
            border: 'none',
            cursor: selectedTone ? 'pointer' : 'not-allowed',
            transition: 'background 0.25s',
          }}
        >
          다음
        </motion.button>
      </div>

      {/* ── 간이 진단 바텀시트 ─────────────────────────── */}
      <AnimatePresence>
        {showDiagnosis && (
          <QuickDiagnosisSheet
            onClose={() => setShowDiagnosis(false)}
            onConfirm={handleDiagnosisConfirm}
          />
        )}
      </AnimatePresence>

    </div>
  )
}
