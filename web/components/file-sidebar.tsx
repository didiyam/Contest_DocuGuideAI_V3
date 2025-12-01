"use client"

import { useState, useRef, useEffect } from "react"
import { cn } from "@/lib/utils"

interface FileSidebarProps {
  children: React.ReactNode
  className?: string
}

export function FileSidebar({ children, className }: FileSidebarProps) {
  const [width, setWidth] = useState(380)
  const isResizing = useRef(false)
  const sidebarRef = useRef<HTMLDivElement>(null)

  const startResize = () => {
    isResizing.current = true
    document.body.style.cursor = "ew-resize"
    document.body.style.userSelect = "none"
  }

  const stopResize = () => {
    isResizing.current = false
    document.body.style.cursor = ""
    document.body.style.userSelect = ""
  }

  const handleMouseMove = (e: MouseEvent) => {
    if (!isResizing.current || !sidebarRef.current) return

    const sidebarLeft = sidebarRef.current.getBoundingClientRect().left
    const newWidth = e.clientX - sidebarLeft

    // 최소 / 최대 폭 제한
    const min = 200
    const max = 520

    if (newWidth >= min && newWidth <= max) {
      setWidth(newWidth)
    }
  }

  useEffect(() => {
    window.addEventListener("mousemove", handleMouseMove)
    window.addEventListener("mouseup", stopResize)

    return () => {
      window.removeEventListener("mousemove", handleMouseMove)
      window.removeEventListener("mouseup", stopResize)
    }
  }, [])

  return (
    <div
      ref={sidebarRef}
      className={cn(
        "relative flex flex-col h-full bg-slate-950/50 border-r border-slate-800",
        className
      )}
      style={{ width }}
    >
      {/* 사이드바 내용 */}
      <div className="h-full overflow-y-auto">
        {children}
      </div>

      {/* 드래그 핸들 */}
      <div
        onMouseDown={startResize}
        className="absolute top-0 right-0 h-full w-1 cursor-ew-resize 
                   hover:bg-cyan-500/40 active:bg-cyan-400/70 
                   transition z-20"
      />
    </div>
  )
}
