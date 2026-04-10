'use client'

import { useEffect } from 'react'

/**
 * locked가 true인 동안 document.body의 스크롤을 잠근다.
 * 바텀시트, 모달 등이 열릴 때 배경 스크롤을 막기 위해 사용.
 */
export function useBodyScrollLock(locked: boolean) {
  useEffect(() => {
    if (locked) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = ''
    }
    return () => {
      document.body.style.overflow = ''
    }
  }, [locked])
}
