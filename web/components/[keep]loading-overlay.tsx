"use client"

import { useEffect, useState } from "react"
import { Sparkles } from "lucide-react"

interface LoadingOverlayProps {
    fileName?: string
    visible: boolean
}

export default function LoadingOverlay({ fileName, visible }: LoadingOverlayProps) {
    const phrases = [
        "문서에서 텍스트를 추출하는 중입니다...",
        "내용을 분석하고 요약을 생성하고 있어요...",
        "챗봇에게 문서를 전달해 대화 준비 중입니다...",
    ]

    const [phraseIndex, setPhraseIndex] = useState(0)
    const [displayText, setDisplayText] = useState("")

    // 🔵 문구 자동 전환
    useEffect(() => {
        if (!visible) return

        const timer = setInterval(() => {
            setPhraseIndex((prev) => (prev + 1) % phrases.length)
        }, 3000)

        return () => clearInterval(timer)
    }, [visible])

    // 🔵 타이핑 애니메이션 (ONLY ONE!!)
    useEffect(() => {
        if (!visible) return

        const fullText = phrases[phraseIndex]
        let i = 0
        let active = true

        setDisplayText("")

        const start = () => {
            const type = () => {
                if (!active) return
                if (i < fullText.length) {
                    setDisplayText((prev) => prev + fullText[i])
                    i++
                    setTimeout(type, 60)
                }
            }
            type()
        }

        const delay = setTimeout(start, 50)

        return () => {
            active = false
            clearTimeout(delay)
        }
    }, [phraseIndex, visible])

    if (!visible) return null

    return (
        <div className="fixed inset-0 z-[99999] bg-slate-950/95 backdrop-blur-xl flex flex-col items-center justify-center text-center p-6">
            {/* Icon */}
            <div className="flex items-center justify-center w-28 h-28 rounded-3xl 
        bg-slate-900 border border-cyan-500/30 shadow-[0_0_40px_rgba(34,211,238,0.4)] mb-8">
                <Sparkles className="w-12 h-12 text-cyan-300 animate-pulse" />
            </div>

            {/* Title */}
            <h1 className="text-3xl font-bold text-cyan-300 mb-3 leading-relaxed">
                정확하고 빠르게 분석해드릴게요!
                <br />잠시만 기다려주세요 🥹
            </h1>

            {/* File name */}
            {fileName && (
                <p className="text-slate-400 text-sm mb-4">
                    업로드하신 <span className="text-cyan-400 font-semibold">{fileName}</span>을 읽고 있어요...
                </p>
            )}

            {/* Typing text */}
            <p className="text-cyan-300 text-lg h-7">
                {displayText}
                <span className="text-cyan-400 animate-pulse">|</span>
            </p>

            {/* Dots */}
            <div className="mt-6 flex gap-2">
                <div className="w-3 h-3 rounded-full bg-cyan-400 animate-bounce"></div>
                <div className="w-3 h-3 rounded-full bg-cyan-400 animate-bounce delay-150"></div>
                <div className="w-3 h-3 rounded-full bg-cyan-400 animate-bounce delay-300"></div>
            </div>
        </div>
    )
}
