'use client'

import { useEffect } from 'react'

/**
 * layout.tsx에 삽입되는 클라이언트 컴포넌트.
 * 마운트 시 localStorage를 읽어 <html data-theme="dark">를 적용한다.
 */
export default function ThemeApply() {
  useEffect(() => {
    const saved = localStorage.getItem('colorfit_theme')
    if (saved === 'dark') {
      document.documentElement.setAttribute('data-theme', 'dark')
    } else {
      document.documentElement.removeAttribute('data-theme')
    }
  }, [])

  return null
}
