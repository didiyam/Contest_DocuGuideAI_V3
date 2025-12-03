"use client"

import { useState, useEffect } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { ScanSearch, FileText, BrainCircuit, Bot } from "lucide-react"

interface LoadingOverlayProps {
  fileName?: string
  visible: boolean
  docId: string
}

const steps = [
  {
    label: "Reading",
    text: "Reading text...",
    textKo:
      "똑디 DOC이 약 1분 동안 복잡한 공공문서를 분석하고 있어요. \n 텍스트로 된 pdf는 결과가 더 빨리나와요.",
  },
  {
    label: "Understanding",
    text: "Organizing info...",
    textKo:
      "문서 속 '해야 할 행동'을 찾아드려요. \n 이제 문서를 읽고 고민할 필요가 없어요. 바로 행동하세요!",
  },
  {
    label: "Preparing Bot",
    text: "Building chatbot...",
    textKo:
      "똑디 DOC은 '똑'똑한 '디'지털 'DOC'(문서) 매니저라는 뜻이에요! \n 문서에 대한 모든 정보를 물어볼 수 있어요.",
  },
  {
    label: "Getting Ready",
    text: "Finalizing...",
    textKo:
      "모든 문서 데이터는 SQLite 기반 RAG로 정교하게 연결돼요. \n 더 정확한 답변을 위해 맥락까지 기억합니다.",
  },
]


export default function LoadingOverlay({ fileName, visible, docId }: LoadingOverlayProps) {
  const [currentStep, setCurrentStep] = useState(0)
  const [displayedText, setDisplayedText] = useState("")
  const [isTyping, setIsTyping] = useState(true)

  // 단계 순환 (0→1→2→3→0...)
  useEffect(() => {
    if (!visible) return;

    const interval = setInterval(() => {
      setCurrentStep((prev) => (prev + 1) % steps.length);
    }, 6000);

    return () => clearInterval(interval);
  }, [visible]);


  //단계 바뀔 때마다 타이핑 리셋
  useEffect(() => {
    setDisplayedText("")
    setIsTyping(true)
  }, [currentStep])

  // visible false → 초기화
  useEffect(() => {
    if (!visible) {
      setCurrentStep(0)
      setDisplayedText("")
    }
  }, [visible])


  /** 타이핑 효과 */
  useEffect(() => {
    if (!visible) return

    const currentText = steps[currentStep].text
    if (displayedText.length < currentText.length) {
      const timer = setTimeout(() => {
        setDisplayedText(currentText.slice(0, displayedText.length + 1))
      }, 50)
      return () => clearTimeout(timer)
    } else {
      setIsTyping(false)
    }
  }, [displayedText, currentStep, visible])

  if (!visible) return null

  return (
    <div className="fixed inset-0 z-[99999] bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 flex items-center justify-center p-8">
      <div className="w-full max-w-4xl">
        {/* 중앙 문서 시각화 */}
        <div className="flex justify-center mb-16">
          <AnimatePresence mode="wait">
            <motion.div
              key={`doc-${currentStep}`}
              className="relative w-48 h-64 bg-gradient-to-br from-slate-800 to-slate-900 rounded-lg shadow-2xl border border-slate-700"
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.8 }}
            >
              {/* 문서 라인 */}
              <div className="absolute inset-4 flex flex-col gap-2 p-4">
                <div className="w-full h-3 bg-slate-700 rounded" />
                <div className="w-3/4 h-3 bg-slate-700 rounded" />
                <div className="w-full h-3 bg-slate-700 rounded" />
                <div className="w-5/6 h-3 bg-slate-700 rounded" />
                <div className="mt-4 w-full h-3 bg-slate-700 rounded" />
                <div className="w-4/5 h-3 bg-slate-700 rounded" />
              </div>

              {/* 0단계 - OCR 스캔 */}
              {currentStep === 0 && (
                <>
                  <motion.div
                    className="absolute inset-0 border-2 border-blue-500 rounded-lg"
                    animate={{
                      boxShadow: [
                        "0 0 20px rgba(59, 130, 246, 0.5)",
                        "0 0 40px rgba(59, 130, 246, 0.8)",
                        "0 0 20px rgba(59, 130, 246, 0.5)",
                      ],
                    }}
                    transition={{ repeat: Number.POSITIVE_INFINITY, duration: 2 }}
                  />
                  <motion.div
                    className="absolute left-0 right-0 h-1 bg-gradient-to-r from-transparent via-blue-400 to-transparent"
                    animate={{ top: ["0%", "100%"] }}
                    transition={{ repeat: Number.POSITIVE_INFINITY, duration: 2, ease: "linear" }}
                  />
                </>
              )}

              {/* 1단계 - Glow */}
              {currentStep === 1 && (
                <motion.div
                  className="absolute inset-0 rounded-lg"
                  animate={{
                    boxShadow: [
                      "0 0 30px rgba(168, 85, 247, 0.4)",
                      "0 0 60px rgba(168, 85, 247, 0.6)",
                      "0 0 30px rgba(168, 85, 247, 0.4)",
                    ],
                  }}
                  transition={{ repeat: Number.POSITIVE_INFINITY, duration: 1.5 }}
                />
              )}

              {/* 2단계 - 퍼지는 파티클 */}
              {currentStep === 2 && (
                <>
                  {[...Array(8)].map((_, i) => (
                    <motion.div
                      key={i}
                      className="absolute w-2 h-2 bg-violet-400 rounded-full"
                      style={{
                        left: "50%",
                        top: "50%",
                      }}
                      animate={{
                        x: [0, Math.cos((i * 45 * Math.PI) / 180) * 80],
                        y: [0, Math.sin((i * 45 * Math.PI) / 180) * 80],
                        opacity: [1, 0],
                      }}
                      transition={{
                        repeat: Number.POSITIVE_INFINITY,
                        duration: 2,
                        delay: i * 0.1,
                      }}
                    />
                  ))}
                </>
              )}

              {/* 3단계 - 초록 반짝임 */}
              {currentStep === 3 && (
                <motion.div
                  className="absolute inset-0 rounded-lg"
                  animate={{
                    boxShadow: [
                      "0 0 30px rgba(34, 197, 94, 0.3)",
                      "0 0 60px rgba(34, 197, 94, 0.6)",
                      "0 0 30px rgba(34, 197, 94, 0.3)",
                    ],
                  }}
                  transition={{ repeat: Number.POSITIVE_INFINITY, duration: 2 }}
                />
              )}
            </motion.div>
          </AnimatePresence>
        </div>
        <div className="flex flex-col items-center mb-10">

          {/* 문서 아이콘 */}
          <AnimatePresence mode="wait">
            ... (기존 document motion 코드 그대로)
          </AnimatePresence>

          {/* 파일명 (큰 아이콘 아래로 이동) */}
          {fileName && (
            <p
              className="
                mt-2 
                max-w-[280px]
                text-center
                text-slate-300 
                text-sm 
                font-medium 
                opacity-80
                whitespace-nowrap 
                overflow-hidden 
                text-ellipsis
            "
            >
              {fileName}
            </p>
          )}
        </div>
          {/* 타이핑 텍스트 */}
          <div className="mt-6 text-center min-h-[2rem]">
            <AnimatePresence mode="wait">
              <motion.p
                key={currentStep}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="text-xl text-slate-300 font-medium"
              >
                {displayedText}
                {isTyping && (
                  <motion.span
                    animate={{ opacity: [1, 0, 1] }}
                    transition={{ repeat: Number.POSITIVE_INFINITY, duration: 0.8 }}
                    className="text-violet-400"
                  >
                    |
                  </motion.span>
                )}
              </motion.p>
            </AnimatePresence>

            <AnimatePresence mode="wait">
              <motion.p
                key={`ko-${currentStep}`}
                initial={{ opacity: 0 }}
                animate={{ opacity: 0.7 }}
                exit={{ opacity: 0 }}
              className="text-sm text-slate-500 mt-2 whitespace-pre-line"
              >
                {steps[currentStep].textKo}
              </motion.p>
            </AnimatePresence>
          </div>
        </div>
      </div>
  )
}
