'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import BottomTabBar from '@/components/BottomTabBar'
import { useTheme } from '@/hooks/useTheme'
import { useBodyScrollLock } from '@/hooks/useBodyScrollLock'

/* ── 톤 데이터 (12종) ─────────────────────────────────── */

interface SwatchColor {
  hex: string
  name: string
}

interface ToneInfo {
  name: string
  gradient: string
  goodColors: SwatchColor[]
  avoidColors: SwatchColor[]
}

const TONE_DATA: Record<string, ToneInfo> = {
  spring_warm_light: {
    name: '봄웜라이트',
    gradient: 'linear-gradient(135deg, #FF9E8A 0%, #FFC8A0 50%, #FFF5E4 100%)',
    goodColors: [
      { hex: '#FFCBA4', name: '복숭아' },
      { hex: '#FFF5E4', name: '아이보리' },
      { hex: '#FF7F5E', name: '코랄' },
      { hex: '#A8C44E', name: '라임' },
      { hex: '#E8B84B', name: '골든' },
      { hex: '#C8916A', name: '카멜' },
    ],
    avoidColors: [
      { hex: '#1A1A2E', name: '블랙' },
      { hex: '#1A2A4A', name: '네이비' },
      { hex: '#444444', name: '차콜' },
      { hex: '#722F37', name: '와인' },
    ],
  },
  spring_warm_bright: {
    name: '봄웜브라이트',
    gradient: 'linear-gradient(135deg, #FF8066 0%, #FFA07A 50%, #FFD580 100%)',
    goodColors: [
      { hex: '#FF6B6B', name: '코랄레드' },
      { hex: '#FF8C42', name: '오렌지' },
      { hex: '#FFD166', name: '옐로우' },
      { hex: '#6BCB77', name: '그린' },
      { hex: '#4ECDC4', name: '터콰이즈' },
      { hex: '#A8E063', name: '라임' },
    ],
    avoidColors: [
      { hex: '#1A1A2E', name: '블랙' },
      { hex: '#6B2737', name: '버건디' },
      { hex: '#1A2A4A', name: '네이비' },
      { hex: '#444444', name: '차콜' },
    ],
  },
  spring_warm_mute: {
    name: '봄웜뮤트',
    gradient: 'linear-gradient(135deg, #D4A574 0%, #C8916A 50%, #E8D5B7 100%)',
    goodColors: [
      { hex: '#C8916A', name: '카멜' },
      { hex: '#C1735A', name: '테라코타' },
      { hex: '#8B9E5E', name: '올리브' },
      { hex: '#F5C5A3', name: '피치' },
      { hex: '#D4A852', name: '골든' },
      { hex: '#F5ECD7', name: '웜화이트' },
    ],
    avoidColors: [
      { hex: '#1A1A2E', name: '블랙' },
      { hex: '#444444', name: '차콜' },
      { hex: '#F8F8F8', name: '퓨어화이트' },
      { hex: '#A89CC8', name: '쿨라벤더' },
    ],
  },
  summer_cool_light: {
    name: '여름쿨라이트',
    gradient: 'linear-gradient(135deg, #C8B8E8 0%, #98D0E8 50%, #C0E8E0 100%)',
    goodColors: [
      { hex: '#C8A8E8', name: '라벤더' },
      { hex: '#9BB8D4', name: '파우더블루' },
      { hex: '#F0A0B0', name: '로즈' },
      { hex: '#F5C5CC', name: '소프트핑크' },
      { hex: '#98DCC8', name: '민트' },
      { hex: '#C4A8D8', name: '라일락' },
    ],
    avoidColors: [
      { hex: '#FF8C42', name: '오렌지' },
      { hex: '#D4A852', name: '머스타드' },
      { hex: '#E8B84B', name: '골든' },
      { hex: '#C8916A', name: '카멜' },
    ],
  },
  summer_cool_soft: {
    name: '여름쿨소프트',
    gradient: 'linear-gradient(135deg, #B0A6C6 0%, #98B8D4 50%, #C0D8E8 100%)',
    goodColors: [
      { hex: '#F5C5CC', name: '소프트핑크' },
      { hex: '#C4A8D8', name: '라벤더' },
      { hex: '#A8C4DC', name: '파스텔블루' },
      { hex: '#E8A4B0', name: '로즈' },
      { hex: '#B8A8C4', name: '모브' },
      { hex: '#C8C8C8', name: '그레이' },
    ],
    avoidColors: [
      { hex: '#FF8C42', name: '오렌지' },
      { hex: '#D4A852', name: '머스타드' },
      { hex: '#8B9E5E', name: '어스톤' },
      { hex: '#8B7355', name: '카키' },
    ],
  },
  summer_cool_mute: {
    name: '여름쿨뮤트',
    gradient: 'linear-gradient(135deg, #8B8B9E 0%, #8AAAB8 50%, #A8B8C0 100%)',
    goodColors: [
      { hex: '#7A9AB0', name: '스모키블루' },
      { hex: '#A890A8', name: '모브' },
      { hex: '#A89898', name: '로즈그레이' },
      { hex: '#D4A8B0', name: '더스티핑크' },
      { hex: '#9898B8', name: '라벤더' },
      { hex: '#B8B0A8', name: '그레이지' },
    ],
    avoidColors: [
      { hex: '#FF8C42', name: '오렌지' },
      { hex: '#FFD166', name: '브라이트옐로' },
      { hex: '#C8916A', name: '카멜' },
      { hex: '#8B9E5E', name: '어스톤' },
    ],
  },
  autumn_warm_bright: {
    name: '가을웜브라이트',
    gradient: 'linear-gradient(135deg, #D4722A 0%, #C1735A 50%, #E8B84B 100%)',
    goodColors: [
      { hex: '#E0722A', name: '오렌지' },
      { hex: '#C1735A', name: '테라코타' },
      { hex: '#B85C28', name: '버니' },
      { hex: '#D4A852', name: '골든' },
      { hex: '#8B9E5E', name: '카키' },
      { hex: '#6B8A44', name: '올리브' },
    ],
    avoidColors: [
      { hex: '#FF69B4', name: '핫핑크' },
      { hex: '#F8F8F8', name: '퓨어화이트' },
      { hex: '#C4A8D8', name: '라벤더' },
      { hex: '#6BADB9', name: '쿨블루' },
    ],
  },
  autumn_warm_mute: {
    name: '가을웜뮤트',
    gradient: 'linear-gradient(135deg, #A0856C 0%, #9C7A58 50%, #D4B896 100%)',
    goodColors: [
      { hex: '#C8916A', name: '카멜' },
      { hex: '#C1735A', name: '테라코타' },
      { hex: '#A08060', name: '어스톤' },
      { hex: '#C4943A', name: '머스타드' },
      { hex: '#8B9E5E', name: '올리브' },
      { hex: '#8B6040', name: '브라운' },
    ],
    avoidColors: [
      { hex: '#FF69B4', name: '핫핑크' },
      { hex: '#9B59B6', name: '퍼플' },
      { hex: '#00FF7F', name: '네온' },
      { hex: '#ADD8E6', name: '아이시블루' },
    ],
  },
  autumn_warm_deep: {
    name: '가을웜딥',
    gradient: 'linear-gradient(135deg, #8B5A2B 0%, #722F37 50%, #9C4A2C 100%)',
    goodColors: [
      { hex: '#722F37', name: '버건디' },
      { hex: '#5C3A1E', name: '다크브라운' },
      { hex: '#C1735A', name: '테라코타' },
      { hex: '#2D5A27', name: '포레스트그린' },
      { hex: '#C4943A', name: '머스타드' },
      { hex: '#A05A3A', name: '카퍼' },
    ],
    avoidColors: [
      { hex: '#F5DDE8', name: '파스텔' },
      { hex: '#C4A8D8', name: '라벤더' },
      { hex: '#FF69B4', name: '핫핑크' },
      { hex: '#F0F8FF', name: '아이시화이트' },
    ],
  },
  winter_cool_bright: {
    name: '겨울쿨브라이트',
    gradient: 'linear-gradient(135deg, #1A2898 0%, #CC0066 50%, #E8B4C8 100%)',
    goodColors: [
      { hex: '#FFFFFF', name: '퓨어화이트' },
      { hex: '#1A1A2E', name: '블랙' },
      { hex: '#1A2898', name: '로열블루' },
      { hex: '#CC0066', name: '마젠타' },
      { hex: '#008080', name: '에메랄드' },
      { hex: '#6B2780', name: '퍼플' },
    ],
    avoidColors: [
      { hex: '#FF8C42', name: '오렌지' },
      { hex: '#C8916A', name: '카멜' },
      { hex: '#E8B84B', name: '골든' },
      { hex: '#8B9E5E', name: '어스톤' },
    ],
  },
  winter_cool_deep: {
    name: '겨울쿨딥',
    gradient: 'linear-gradient(135deg, #1E1E2E 0%, #2A2A5E 50%, #4A2060 100%)',
    goodColors: [
      { hex: '#1A1A2E', name: '블랙' },
      { hex: '#1A2A4A', name: '네이비' },
      { hex: '#722F37', name: '버건디' },
      { hex: '#3D1A5E', name: '다크퍼플' },
      { hex: '#006666', name: '에메랄드' },
      { hex: '#333333', name: '차콜' },
    ],
    avoidColors: [
      { hex: '#F5DDE8', name: '파스텔' },
      { hex: '#F5C5A3', name: '피치' },
      { hex: '#C8916A', name: '카멜' },
      { hex: '#E8B84B', name: '골든' },
    ],
  },
  winter_cool_light: {
    name: '겨울쿨라이트',
    gradient: 'linear-gradient(135deg, #C8C8E8 0%, #A0B8E8 50%, #D4E8F4 100%)',
    goodColors: [
      { hex: '#FFFFFF', name: '화이트' },
      { hex: '#ADD8E6', name: '아이시블루' },
      { hex: '#C0C0C0', name: '실버' },
      { hex: '#C4A8D8', name: '라벤더' },
      { hex: '#FFB6C1', name: '소프트핑크' },
      { hex: '#AAAACC', name: '페리윙클' },
    ],
    avoidColors: [
      { hex: '#FF8C42', name: '오렌지' },
      { hex: '#D4A852', name: '머스타드' },
      { hex: '#C8916A', name: '카멜' },
      { hex: '#8B7355', name: '카키' },
    ],
  },
}

const FALLBACK_TONE: ToneInfo = {
  name: '퍼스널컬러',
  gradient: 'linear-gradient(135deg, #D4A5A5 0%, #964F4C 100%)',
  goodColors: [],
  avoidColors: [],
}

/* ── TPO 한글 ─────────────────────────────────────────── */

const TPO_LABELS: Record<string, string> = {
  commute: '출근', date: '데이트', interview: '면접',
  weekend: '주말', campus: '캠퍼스', travel: '여행',
  event: '행사', workout: '운동',
}

/* ── 가격 포맷 ────────────────────────────────────────── */

function formatWon(value: number) {
  if (value >= 10000) return `${Math.floor(value / 10000)}만원`
  return `${value.toLocaleString()}원`
}

/* ── 색상 스와치 ──────────────────────────────────────── */

function ColorSwatch({
  color,
  avoid,
  index,
}: {
  color: SwatchColor
  avoid?: boolean
  index: number
}) {
  return (
    <motion.div
      className="flex flex-col items-center gap-1"
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ delay: 0.3 + index * 0.05, duration: 0.25 }}
    >
      <div className="relative" style={{ width: 40, height: 40 }}>
        <div
          style={{
            width: 40,
            height: 40,
            borderRadius: '50%',
            background: color.hex,
            border: '1.5px solid rgba(0,0,0,0.08)',
          }}
        />
        {avoid && (
          <div
            className="absolute inset-0 flex items-center justify-center"
            style={{
              borderRadius: '50%',
              background: 'rgba(0,0,0,0.35)',
            }}
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <line x1="4" y1="4" x2="12" y2="12" stroke="white" strokeWidth="2" strokeLinecap="round" />
              <line x1="12" y1="4" x2="4" y2="12" stroke="white" strokeWidth="2" strokeLinecap="round" />
            </svg>
          </div>
        )}
      </div>
      <span
        style={{
          fontFamily: 'var(--font-body)',
          fontSize: '10px',
          color: 'var(--text-tertiary)',
          lineHeight: 1.3,
          textAlign: 'center',
          whiteSpace: 'nowrap',
        }}
      >
        {color.name}
      </span>
    </motion.div>
  )
}

/* ── 바텀시트 ─────────────────────────────────────────── */

interface BottomSheetProps {
  title: string
  onClose: () => void
  children: React.ReactNode
}

function BottomSheet({ title, onClose, children }: BottomSheetProps) {
  return (
    <>
      <motion.div
        className="fixed inset-0 z-40"
        style={{ background: 'rgba(0,0,0,0.45)' }}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={onClose}
      />
      <motion.div
        className="fixed bottom-0 z-50 flex flex-col"
        style={{
          left: 'var(--app-offset)',
          right: 'var(--app-offset)',
          background: 'var(--bg)',
          borderRadius: '20px 20px 0 0',
          maxHeight: 'var(--sheet-max-h-80)',
          overflowY: 'auto',
          paddingBottom: 'env(safe-area-inset-bottom, 24px)',
        }}
        initial={{ y: '100%' }}
        animate={{ y: 0 }}
        exit={{ y: '100%' }}
        transition={{ type: 'spring', stiffness: 300, damping: 30 }}
      >
        <div className="flex justify-center pt-3 pb-2">
          <div style={{ width: 36, height: 4, borderRadius: 2, background: 'var(--border)' }} />
        </div>
        <div className="flex items-center justify-between px-5 pb-4">
          <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '18px', fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
            {title}
          </h3>
          <button
            type="button"
            onClick={onClose}
            style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 4 }}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--text-secondary)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>
        <div className="px-5 pb-6">{children}</div>
      </motion.div>
    </>
  )
}

/* ── 성별 변경 시트 ───────────────────────────────────── */

function GenderSheet({ current, onSave, onClose }: { current: string; onSave: (v: string) => void; onClose: () => void }) {
  const [selected, setSelected] = useState(current)
  return (
    <BottomSheet title="성별 변경" onClose={onClose}>
      <div className="flex gap-3 mb-6">
        {[{ id: 'female', label: '여성' }, { id: 'male', label: '남성' }].map((opt) => (
          <button
            key={opt.id}
            type="button"
            onClick={() => setSelected(opt.id)}
            style={{
              flex: 1,
              padding: '14px',
              borderRadius: 'var(--radius-md)',
              border: `2px solid ${selected === opt.id ? 'var(--accent)' : 'var(--border)'}`,
              background: selected === opt.id ? 'rgba(150,79,76,0.06)' : 'transparent',
              fontFamily: 'var(--font-body)',
              fontSize: '15px',
              fontWeight: selected === opt.id ? 600 : 400,
              color: selected === opt.id ? 'var(--accent)' : 'var(--text-primary)',
              cursor: 'pointer',
            }}
          >
            {opt.label}
          </button>
        ))}
      </div>
      <button
        type="button"
        onClick={() => { onSave(selected); onClose() }}
        style={{
          width: '100%',
          padding: '14px',
          borderRadius: 'var(--radius-md)',
          background: 'var(--accent)',
          color: '#fff',
          fontFamily: 'var(--font-body)',
          fontSize: '15px',
          fontWeight: 600,
          border: 'none',
          cursor: 'pointer',
        }}
      >
        저장
      </button>
    </BottomSheet>
  )
}

/* ── 예산 변경 시트 ───────────────────────────────────── */

function BudgetSheet({
  currentMin,
  currentMax,
  onSave,
  onClose,
}: {
  currentMin: number
  currentMax: number
  onSave: (min: number, max: number) => void
  onClose: () => void
}) {
  const [min, setMin] = useState(currentMin)
  const [max, setMax] = useState(currentMax)
  return (
    <BottomSheet title="예산 변경" onClose={onClose}>
      <div className="flex flex-col gap-4 mb-6">
        <div className="flex justify-between">
          <span style={{ fontFamily: 'var(--font-body)', fontSize: '13px', color: 'var(--text-secondary)' }}>예산 범위</span>
          <span style={{ fontFamily: 'var(--font-body)', fontSize: '13px', fontWeight: 600, color: 'var(--text-primary)' }}>
            {formatWon(min)} ~ {formatWon(max)}
          </span>
        </div>
        <div className="flex items-center gap-3">
          <span style={{ fontFamily: 'var(--font-body)', fontSize: '11px', color: 'var(--text-tertiary)', width: 28 }}>MIN</span>
          <input
            type="range" min={0} max={300000} step={5000} value={min}
            onChange={(e) => setMin(Math.min(Number(e.target.value), max - 5000))}
            className="flex-1"
            style={{ accentColor: 'var(--accent)' }}
          />
        </div>
        <div className="flex items-center gap-3">
          <span style={{ fontFamily: 'var(--font-body)', fontSize: '11px', color: 'var(--text-tertiary)', width: 28 }}>MAX</span>
          <input
            type="range" min={0} max={300000} step={5000} value={max}
            onChange={(e) => setMax(Math.max(Number(e.target.value), min + 5000))}
            className="flex-1"
            style={{ accentColor: 'var(--accent)' }}
          />
        </div>
      </div>
      <button
        type="button"
        onClick={() => { onSave(min, max); onClose() }}
        style={{
          width: '100%',
          padding: '14px',
          borderRadius: 'var(--radius-md)',
          background: 'var(--accent)',
          color: '#fff',
          fontFamily: 'var(--font-body)',
          fontSize: '15px',
          fontWeight: 600,
          border: 'none',
          cursor: 'pointer',
        }}
      >
        저장
      </button>
    </BottomSheet>
  )
}

/* ── TPO 변경 시트 ────────────────────────────────────── */

const ALL_TPOS = ['commute', 'date', 'interview', 'weekend', 'campus', 'travel', 'event', 'workout']

function TpoSheet({ current, onSave, onClose }: { current: string[]; onSave: (v: string[]) => void; onClose: () => void }) {
  const [selected, setSelected] = useState<string[]>(current)
  const toggle = (id: string) =>
    setSelected((prev) => prev.includes(id) ? prev.filter((t) => t !== id) : [...prev, id])

  return (
    <BottomSheet title="TPO 변경" onClose={onClose}>
      <div className="flex flex-wrap gap-2 mb-6">
        {ALL_TPOS.map((id) => {
          const active = selected.includes(id)
          return (
            <button
              key={id}
              type="button"
              onClick={() => toggle(id)}
              style={{
                padding: '8px 16px',
                borderRadius: 'var(--radius-full)',
                border: `1.5px solid ${active ? 'var(--accent)' : 'var(--border)'}`,
                background: active ? 'var(--accent)' : 'transparent',
                color: active ? '#fff' : 'var(--text-secondary)',
                fontFamily: 'var(--font-body)',
                fontSize: '14px',
                fontWeight: active ? 600 : 400,
                cursor: 'pointer',
                WebkitTapHighlightColor: 'transparent',
              }}
            >
              {TPO_LABELS[id]}
            </button>
          )
        })}
      </div>
      <button
        type="button"
        onClick={() => { onSave(selected); onClose() }}
        style={{
          width: '100%',
          padding: '14px',
          borderRadius: 'var(--radius-md)',
          background: 'var(--accent)',
          color: '#fff',
          fontFamily: 'var(--font-body)',
          fontSize: '15px',
          fontWeight: 600,
          border: 'none',
          cursor: 'pointer',
        }}
      >
        저장
      </button>
    </BottomSheet>
  )
}

/* ── 메인 페이지 ─────────────────────────────────────── */

type Sheet = 'gender' | 'tpo' | 'budget' | null

export default function ProfilePage() {
  const router = useRouter()
  const { isDark, toggle: toggleTheme } = useTheme()

  const [toneId, setToneId] = useState('')
  const [gender, setGender] = useState('female')
  const [tpo, setTpo] = useState<string[]>([])
  const [budgetMin, setBudgetMin] = useState(0)
  const [budgetMax, setBudgetMax] = useState(300000)
  const [activeSheet, setActiveSheet] = useState<Sheet>(null)
  useBodyScrollLock(activeSheet !== null)

  useEffect(() => {
    setToneId(localStorage.getItem('onboarding_tone_id') || 'summer_cool_soft')
    setGender(localStorage.getItem('onboarding_gender') || 'female')
    const tpoRaw = localStorage.getItem('onboarding_tpo')
    setTpo(tpoRaw ? JSON.parse(tpoRaw) : [])
    setBudgetMin(Number(localStorage.getItem('onboarding_budget_min') || '0'))
    setBudgetMax(Number(localStorage.getItem('onboarding_budget_max') || '300000'))
  }, [])

  const tone = TONE_DATA[toneId] ?? FALLBACK_TONE

  const saveGender = (v: string) => {
    setGender(v)
    localStorage.setItem('onboarding_gender', v)
  }
  const saveTpo = (v: string[]) => {
    setTpo(v)
    localStorage.setItem('onboarding_tpo', JSON.stringify(v))
  }
  const saveBudget = (min: number, max: number) => {
    setBudgetMin(min)
    setBudgetMax(max)
    localStorage.setItem('onboarding_budget_min', String(min))
    localStorage.setItem('onboarding_budget_max', String(max))
  }

  const InfoRow = ({
    label,
    value,
    onEdit,
  }: {
    label: string
    value: string
    onEdit: () => void
  }) => (
    <div
      className="flex items-center justify-between py-4"
      style={{ borderBottom: '1px solid var(--border)' }}
    >
      <div className="flex flex-col gap-0.5">
        <span style={{ fontFamily: 'var(--font-body)', fontSize: '12px', color: 'var(--text-tertiary)' }}>
          {label}
        </span>
        <span style={{ fontFamily: 'var(--font-body)', fontSize: '15px', color: 'var(--text-primary)', fontWeight: 500 }}>
          {value}
        </span>
      </div>
      <button
        type="button"
        onClick={onEdit}
        style={{
          fontFamily: 'var(--font-body)',
          fontSize: '13px',
          fontWeight: 600,
          color: 'var(--accent)',
          background: 'none',
          border: 'none',
          cursor: 'pointer',
          padding: '4px 8px',
        }}
      >
        변경
      </button>
    </div>
  )

  return (
    <div className="min-h-screen flex flex-col" style={{ background: 'var(--bg)' }}>

      {/* ══════════════ 헤더 ══════════════ */}
      <header
        className="sticky top-0 z-30 flex items-center justify-between px-5 py-3"
        style={{ background: 'var(--bg)', borderBottom: '1px solid var(--border)' }}
      >
        <h1
          style={{
            fontFamily: 'var(--font-display)',
            fontSize: '22px',
            fontWeight: 700,
            color: 'var(--text-primary)',
            margin: 0,
          }}
        >
          마이
        </h1>
      </header>

      <div className="flex flex-col gap-0 pb-24">

        {/* ══════════════ 톤 카드 ══════════════ */}
        <motion.button
          type="button"
          onClick={() => router.push(`/tone/${toneId}`)}
          className="relative w-full flex flex-col items-center justify-center"
          style={{
            background: tone.gradient,
            height: 180,
            border: 'none',
            cursor: 'pointer',
            WebkitTapHighlightColor: 'transparent',
          }}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.4 }}
          whileTap={{ opacity: 0.9 }}
        >
          <span
            style={{
              fontFamily: 'var(--font-display)',
              fontSize: '28px',
              fontWeight: 700,
              color: '#FFFFFF',
              textShadow: '0 1px 8px rgba(0,0,0,0.25)',
              lineHeight: 1.2,
            }}
          >
            {tone.name}
          </span>
          <span
            style={{
              fontFamily: 'var(--font-body)',
              fontSize: '13px',
              color: 'rgba(255,255,255,0.8)',
              marginTop: 6,
            }}
          >
            탭하여 자세히 보기
          </span>
          {/* chevron */}
          <div className="absolute bottom-4 right-5">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.7)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M9 18l6-6-6-6" />
            </svg>
          </div>
        </motion.button>

        {/* ══════════════ 색상 스와치 ══════════════ */}
        <div className="px-5 pt-5 pb-4" style={{ borderBottom: '1px solid var(--border)' }}>
          {/* 잘 어울리는 색 */}
          {tone.goodColors.length > 0 && (
            <div className="mb-4">
              <p style={{ fontFamily: 'var(--font-body)', fontSize: '13px', fontWeight: 600, color: 'var(--text-secondary)', margin: '0 0 12px' }}>
                잘 어울리는 색
              </p>
              <div className="flex gap-4">
                {tone.goodColors.map((c, i) => (
                  <ColorSwatch key={c.hex} color={c} index={i} />
                ))}
              </div>
            </div>
          )}
          {/* 피해야 할 색 */}
          {tone.avoidColors.length > 0 && (
            <div>
              <p style={{ fontFamily: 'var(--font-body)', fontSize: '13px', fontWeight: 600, color: 'var(--text-secondary)', margin: '0 0 12px' }}>
                피해야 할 색
              </p>
              <div className="flex gap-4">
                {tone.avoidColors.map((c, i) => (
                  <ColorSwatch key={c.hex} color={c} avoid index={i} />
                ))}
              </div>
            </div>
          )}
        </div>

        {/* ══════════════ 내 정보 ══════════════ */}
        <div className="px-5 pt-2">
          <p style={{ fontFamily: 'var(--font-body)', fontSize: '13px', fontWeight: 600, color: 'var(--text-secondary)', padding: '12px 0 4px' }}>
            내 정보
          </p>
          <InfoRow
            label="성별"
            value={gender === 'female' ? '여성' : '남성'}
            onEdit={() => setActiveSheet('gender')}
          />
          <InfoRow
            label="TPO"
            value={tpo.length > 0 ? tpo.map((t) => TPO_LABELS[t] ?? t).join(', ') : '설정 없음'}
            onEdit={() => setActiveSheet('tpo')}
          />
          <InfoRow
            label="예산"
            value={`${formatWon(budgetMin)} ~ ${formatWon(budgetMax)}`}
            onEdit={() => setActiveSheet('budget')}
          />
        </div>

        {/* ══════════════ 취향 관리 ══════════════ */}
        <div className="px-5 pt-2">
          <p style={{ fontFamily: 'var(--font-body)', fontSize: '13px', fontWeight: 600, color: 'var(--text-secondary)', padding: '12px 0 4px' }}>
            취향
          </p>
          <button
            type="button"
            onClick={() => router.push('/style-seeds')}
            className="flex items-center justify-between w-full py-4"
            style={{
              borderBottom: '1px solid var(--border)',
              background: 'none',
              cursor: 'pointer',
              WebkitTapHighlightColor: 'transparent',
            }}
          >
            <span style={{ fontFamily: 'var(--font-body)', fontSize: '15px', color: 'var(--text-primary)', fontWeight: 500 }}>
              취향 관리
            </span>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--text-tertiary)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M9 18l6-6-6-6" />
            </svg>
          </button>
        </div>

        {/* ══════════════ 설정 ══════════════ */}
        <div className="px-5 pt-2">
          <p style={{ fontFamily: 'var(--font-body)', fontSize: '13px', fontWeight: 600, color: 'var(--text-secondary)', padding: '12px 0 4px' }}>
            설정
          </p>
          <div className="flex items-center justify-between py-4" style={{ borderBottom: '1px solid var(--border)' }}>
            <span style={{ fontFamily: 'var(--font-body)', fontSize: '15px', color: 'var(--text-primary)', fontWeight: 500 }}>
              알림
            </span>
            <span style={{ fontFamily: 'var(--font-body)', fontSize: '13px', color: 'var(--text-tertiary)' }}>준비중</span>
          </div>
          <div className="flex items-center justify-between py-4" style={{ borderBottom: '1px solid var(--border)' }}>
            <span style={{ fontFamily: 'var(--font-body)', fontSize: '15px', color: 'var(--text-primary)', fontWeight: 500 }}>
              다크모드
            </span>
            <button
              type="button"
              onClick={toggleTheme}
              aria-label={isDark ? '라이트모드로 전환' : '다크모드로 전환'}
              style={{
                width: 44,
                height: 26,
                borderRadius: 13,
                background: isDark ? 'var(--accent)' : 'var(--border)',
                border: 'none',
                cursor: 'pointer',
                position: 'relative',
                padding: 0,
                flexShrink: 0,
                transition: 'background 0.2s',
                WebkitTapHighlightColor: 'transparent',
              }}
            >
              <motion.span
                animate={{ x: isDark ? 18 : 0 }}
                transition={{ type: 'spring', stiffness: 400, damping: 28 }}
                style={{
                  position: 'absolute',
                  top: 3,
                  left: 3,
                  width: 20,
                  height: 20,
                  borderRadius: '50%',
                  background: '#F0EDE8',
                  display: 'block',
                }}
              />
            </button>
          </div>
          <button
            type="button"
            onClick={() => {
              localStorage.clear()
              router.push('/onboarding/step1')
            }}
            className="flex items-center w-full py-4"
            style={{
              borderBottom: '1px solid var(--border)',
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              WebkitTapHighlightColor: 'transparent',
            }}
          >
            <span style={{ fontFamily: 'var(--font-body)', fontSize: '15px', color: 'var(--error-text)', fontWeight: 500 }}>
              로그아웃
            </span>
          </button>
        </div>
      </div>

      {/* ══════════════ 하단 탭바 ══════════════ */}
      <BottomTabBar />

      {/* ══════════════ 바텀시트 ══════════════ */}
      <AnimatePresence>
        {activeSheet === 'gender' && (
          <GenderSheet
            current={gender}
            onSave={saveGender}
            onClose={() => setActiveSheet(null)}
          />
        )}
        {activeSheet === 'tpo' && (
          <TpoSheet
            current={tpo}
            onSave={saveTpo}
            onClose={() => setActiveSheet(null)}
          />
        )}
        {activeSheet === 'budget' && (
          <BudgetSheet
            currentMin={budgetMin}
            currentMax={budgetMax}
            onSave={saveBudget}
            onClose={() => setActiveSheet(null)}
          />
        )}
      </AnimatePresence>
    </div>
  )
}
