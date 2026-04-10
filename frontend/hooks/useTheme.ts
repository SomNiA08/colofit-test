'use client'

import { useState, useEffect } from 'react'

const STORAGE_KEY = 'colorfit_theme'

export function useTheme() {
  const [isDark, setIsDark] = useState(false)

  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY)
    setIsDark(saved === 'dark')
  }, [])

  function toggle() {
    const next = !isDark
    setIsDark(next)
    if (next) {
      document.documentElement.setAttribute('data-theme', 'dark')
      localStorage.setItem(STORAGE_KEY, 'dark')
    } else {
      document.documentElement.removeAttribute('data-theme')
      localStorage.setItem(STORAGE_KEY, 'light')
    }
  }

  return { isDark, toggle }
}
