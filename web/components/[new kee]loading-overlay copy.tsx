"use client"

import { useState, useEffect } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { ScanSearch, FileText, Bot, BarChart, CheckCircle } from "lucide-react"

interface LoadingOverlayProps {
  fileName?: string
  visible: boolean
  docId: string
}

const steps = [
  {
    icon: ScanSearch,
    label: "OCR",
    text: "Reading document text...",
    textKo: "문서에서 텍스트를 추출하고 있어요...\n이미지라면 조금 더 시간이 걸릴 수 있어요",
  },
  {
    icon: FileText,
    label: "Refine",
    text: "Refining with LLM...",
    textKo: "중요 문장과 핵심 정보를 정리하고 있어요...",
  },
  {
    icon: Bot,
    label: "Analysis",
    text: "Generating To-Do...",
    textKo: "사용자의 할 일 리스트를 생성 중입니다...",
  },
  {
    icon: BarChart,
    label: "Summary",
    text: "Complete!",
    textKo: "분석이 완료되었습니다! 챗봇 생성 완료 후 바로 결과를 보여드릴게요 ",
  },
]

export default function LoadingOverlay({ fileName, visible, docId }: LoadingOverlayProps) {
  const [currentStep, setCurrentStep] = useState(0)
  const [displayedText, setDisplayedText] = useState("")
  const [isTyping, setIsTyping] = useState(true)

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


  // ⭐ 핵심 변경됨: progress polling (백엔드 단계 100% 따라가기)
  useEffect(() => {
    if (!visible || !docId) return;

    console.log("[LOADING] start polling:", docId)

    const interval = setInterval(async () => {
      const res = await fetch(`http://127.0.0.1:8000/progress/${docId}`)
      const data = await res.json()

      console.log("[LOADING] progress:", data)

      // ⭐ 추가됨: 백엔드 단계 매핑
      const stepMap: Record<string, number> = {
        ocr: 0,
        refine: 1,
        analysis: 2,
        summary: 3,
      }

      const next = stepMap[data.step]

      if (typeof next === "number" && next !== currentStep) {
        setCurrentStep(next)
      }

    }, 300) // 0.3초 polling

    return () => clearInterval(interval)
  }, [visible, docId, currentStep])

  // ⭐ 유지됨: 마지막 단계 시 3초 유지 후 종료 가능
  useEffect(() => {
    if (currentStep === 3) {
      const t = setTimeout(() => {
        // 부모가 visible=false로 닫기
      }, 3000)
      return () => clearTimeout(t)
    }
  }, [currentStep])


  /** 타이핑 효과 (변경 없음) */
  useEffect(() => {
    if (!visible) return

    const currentText = steps[currentStep].text
    if (displayedText.length < currentText.length) {
      const timer = setTimeout(() => {
        setDisplayedText(currentText.slice(0, displayedText.length + 1))
      }, 35)
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
            {currentStep < 3 ? (
              <motion.div
                key="document"
                className="relative w-48 h-64 bg-gradient-to-br from-slate-800 to-slate-900 rounded-lg shadow-2xl border border-slate-700"
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{
                  opacity: 1,
                  scale: 1,
                  rotate: currentStep === 1 ? [0, -1, 1, -1, 0] : 0,
                }}
                transition={{
                  rotate: { repeat: currentStep === 1 ? Number.POSITIVE_INFINITY : 0, duration: 0.5 },
                }}
                exit={{ opacity: 0, scale: 0.8 }}
              >
                {/* 문서 텍스트 라인 */}
                <div className="absolute inset-4 flex flex-col gap-2 p-4">
                  <div className="w-full h-3 bg-slate-700 rounded" />
                  <div className="w-3/4 h-3 bg-slate-700 rounded" />
                  <div className="w-full h-3 bg-slate-700 rounded" />
                  <div className="w-5/6 h-3 bg-slate-700 rounded" />
                  <div className="mt-4 w-full h-3 bg-slate-700 rounded" />
                  <div className="w-4/5 h-3 bg-slate-700 rounded" />
                </div>

                {/* OCR 스캔 애니메이션 */}
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

                {/* LLM Glow */}
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

                {/* 분석 파티클 */}
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
              </motion.div>
            ) : (
              <motion.div
                key="complete"
                initial={{ opacity: 0, scale: 0 }}
                animate={{ opacity: 1, scale: 1 }}
                className="w-48 h-64 flex items-center justify-center"
              >
                <motion.div
                  animate={{
                    scale: [1, 1.2, 1],
                    rotate: [0, 360],
                  }}
                  transition={{ duration: 0.6 }}
                >
                  <CheckCircle className="w-32 h-32 text-emerald-400" strokeWidth={1.5} />
                </motion.div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        <div className="flex flex-col items-center mb-16">

          {/* 문서 아이콘 */}
          <AnimatePresence mode="wait">
            ... (기존 document motion 코드 그대로)
          </AnimatePresence>

          {/* 파일명 (큰 아이콘 아래로 이동) */}
          {fileName && (
            <p
              className="
                mt-4 
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


        {/* 하단 스텝 표시 */}
        <div className="relative mt-24">
          <div className="flex items-center justify-between">
            {steps.map((step, index) => {
              const Icon = step.icon
              const isActive = index === currentStep
              const isCompleted = index < currentStep
              const isPending = index > currentStep

              return (
                <div key={index} className="flex-1 relative">
                  <div className="flex flex-col items-center">
                    <motion.div
                      className={`relative z-10 rounded-full p-4 bg-slate-800`}
                      animate={{
                        scale: isActive ? 1.2 : 1,
                        boxShadow: isActive
                          ? [
                            "0 0 20px rgba(255, 255, 255, 0.4)",
                            "0 0 40px rgba(255, 255, 255, 0.6)",
                            "0 0 20px rgba(255, 255, 255, 0.4)",
                          ]
                          : "none",
                      }}
                      transition={{
                        scale: { duration: 0.3 },
                        boxShadow: { repeat: isActive ? Number.POSITIVE_INFINITY : 0, duration: 2 },
                      }}
                    >
                      <Icon
                        className={`w-8 h-8 text-white ${isPending ? "opacity-50" : ""}`}
                      />
                    </motion.div>

                    <p
                      className={`mt-3 text-sm font-medium ${isActive ? "text-white" : isPending ? "text-slate-600" : "text-slate-400"
                        }`}
                    >
                      {step.label}
                    </p>
                  </div>

                  {/* 선 연결 */}
                  {index < steps.length - 1 && (
                    <div className="absolute top-8 left-[calc(50%+3rem)] right-[calc(-50%+3rem)] h-0.5">
                      <motion.div
                        className={`h-full ${index < currentStep ? "bg-white" : "bg-slate-700"
                          }`}
                        initial={{ scaleX: 0 }}
                        animate={{ scaleX: index < currentStep ? 1 : 0 }}
                        transition={{ duration: 0.5 }}
                        style={{ originX: 0 }}
                      />
                    </div>
                  )}
                </div>
              )
            })}
          </div>

          {/* 타이핑 텍스트 */}
          <div className="mt-12 text-center min-h-[2rem]">
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
                className="text-sm text-slate-500 mt-2"
              >
                {steps[currentStep].textKo}
              </motion.p>
            </AnimatePresence>
          </div>
        </div>
      </div>
    </div>
  )
}
