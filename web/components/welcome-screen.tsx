"use client"

import type React from "react"
import { useRef, useState } from "react"
import { Upload, Bot, Sparkles, FileText, Image as ImageIcon, X } from "lucide-react"
import { Button } from "@/components/ui/button"

interface WelcomeScreenProps {
  onStartUpload: (files: File[]) => void
  isUploading: boolean
}

export function WelcomeScreen({ onStartUpload }: WelcomeScreenProps) {
  const [showPicker, setShowPicker] = useState(false)
  const [selectedFiles, setSelectedFiles] = useState<File[]>([])

  const pdfInputRef = useRef<HTMLInputElement>(null)
  const imageInputRef = useRef<HTMLInputElement>(null)

  // 메인 버튼 → 업로드 시작
  const handleMainClick = () => {
    if (selectedFiles.length === 0) {
      setShowPicker((prev) => !prev)
    } else {
      onStartUpload(selectedFiles) // isUploading 체크 제거
    }
  }

  // 파일 처리
  const handleFilePicked =
    (type: "pdf" | "image") => (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = Array.from(e.target.files || [])
      if (files.length === 0) return

      if (type === "pdf") {
        setSelectedFiles([files[0]])
      } else {
        setSelectedFiles((prev) => [...prev, ...files])
      }

      e.target.value = ""
      setShowPicker(false)
    }

  const handleRemoveFile = (index: number) => {
    setSelectedFiles((prev) => prev.filter((_, i) => i !== index))
  }

  const handleClearAll = () => {
    setSelectedFiles([])
  }

  const handlePdfClick = () => pdfInputRef.current?.click()
  const handleImageClick = () => imageInputRef.current?.click()

  // 버튼 색상
  const mainButtonLabel =
    selectedFiles.length === 0 ? "문서 업로드 시작하기" : "시작하기"

  const mainButtonColor =
    selectedFiles.length === 0
      ? "bg-gradient-to-r from-cyan-600 to-blue-600 text-white"
      : "bg-yellow-400 text-slate-900 hover:bg-yellow-300"

  return (
    <div className="h-screen w-full bg-slate-950 flex flex-col items-center justify-center p-6 relative overflow-hidden">
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 
        w-[500px] h-[500px] bg-cyan-500/10 rounded-full blur-[100px]" />

      <div className="relative z-10 flex flex-col items-center text-center max-w-md animate-in fade-in zoom-in duration-500">

        {/* Icon */}
        <div className="relative mb-8 group cursor-pointer">
          <div className="absolute inset-0 bg-cyan-400/20 rounded-full blur-xl animate-pulse" />
          <div className="relative w-32 h-32 bg-slate-900 rounded-full border-2 border-cyan-400/50 
            flex items-center justify-center shadow-[0_0_30px_rgba(34,211,238,0.2)] 
            group-hover:scale-105 transition-transform">
            <Bot className="w-16 h-16 text-cyan-400" />
          </div>
          <Sparkles className="absolute -top-4 -right-4 w-8 h-8 text-yellow-300" />
        </div>

        <h2 className="text-cyan-400 font-medium mb-2 text-sm md:text-base">
          당신의 똑똑한 디지털 문서 매니저
        </h2>
        <h1 className="text-4xl md:text-5xl font-bold text-white mb-6 tracking-tight">
          똑디 Doc!
        </h1>
        <p className="text-slate-400 text-base md:text-lg mb-10">
          복잡한 공공문서는 이제 안녕! <br />문서를 업로드하면 핵심만 쏙 뽑아드려요.
        </p>

        {/* CTA */}
        <div className="relative flex flex-col items-center gap-4 w-full">

          {/* 메인 버튼 */}
          <div className="relative group w-full flex justify-center">
            <div
              className="
            absolute 
            w-full
            max-w-xs 
            sm:max-w-sm 
            md:max-w-md 
            lg:w-[400px]
            h-14 
            rounded-lg 
            bg-gradient-to-r from-cyan-600 to-blue-600 
            blur 
            opacity-25 
            group-hover:opacity-75 
            transition 
            duration-700
            "   
            />


            <Button
              size="lg"
              onClick={handleMainClick}
              className={`
        relative w-full max-w-xs sm:max-w-sm md:max-w-md lg:w-[400px]
        h-14 text-lg rounded-lg transition-all duration-300
        ${mainButtonColor}
      `}
            >
              <>
                {selectedFiles.length === 0 && <Upload className="w-5 h-5" />}
                {mainButtonLabel}
              </>
            </Button>
          </div>

          {/* 파일 선택 메뉴 */}
          {showPicker && selectedFiles.length === 0 && (
            <div className="mt-2 w-full max-w-xs rounded-xl border border-cyan-500/30 
              bg-slate-900/80 px-4 py-3 shadow-lg animate-in slide-in-from-top-2">

              <p className="text-xs text-slate-400 mb-2">
                <span className="font-semibold text-slate-300">업로드할 문서 종류를 선택하세요.</span><br /><br />
                웹에서 여러 장의 이미지를 선택할 경우<br /> <span className="font-semibold">Ctrl</span> 키를 눌러 선택해 주세요.
              </p>

              <div className="flex gap-3">
                <Button
                  type="button"
                  variant="outline"
                  onClick={handlePdfClick}
                  className="
                  flex-1 
                  border-cyan-500/40 
                  bg-slate-900/60 
                  text-slate-100
                  hover:bg-white hover:text-blue-900
                "
                >
                  <FileText className="w-4 h-4 mr-1.5 text-current" /> PDF 업로드
                </Button>


                <Button
                  type="button"
                  variant="outline"
                  onClick={handleImageClick}
                  className="
                  flex-1 
                  border-blue-500/40 
                  bg-slate-900/60 
                  text-slate-100
                  hover:bg-white hover:text-blue-900
                "
                >
                  <ImageIcon className="w-4 h-4 mr-1.5 text-current" /> 이미지 업로드
                </Button>

              </div>
            </div>
          )}

          {/* 선택한 파일 리스트 */}
          {selectedFiles.length > 0 && (
            <div className="w-full max-w-md mt-2 rounded-xl border border-cyan-500/30 
              bg-slate-900/80 px-4 py-3 shadow-lg">
              <div className="flex items-center justify-between mb-2">
                <p className="text-xs text-slate-300">선택한 문서 목록</p>
                <button
                  type="button"
                  onClick={handleClearAll}
                  className="text-[11px] text-slate-400 hover:text-slate-200 underline"
                >
                  다시 선택하기
                </button>
              </div>

              <ul className="space-y-1 max-h-40 overflow-y-auto">
                {selectedFiles.map((file, idx) => (
                  <li
                    key={idx}
                    className="flex items-center justify-between text-xs text-slate-200 
                      border border-slate-700/60 rounded-md px-2 py-1"
                  >
                    <span className="truncate max-w-[220px]">{file.name}</span>
                    <button
                      type="button"
                      onClick={() => handleRemoveFile(idx)}
                      className="text-slate-400 hover:text-red-400"
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </li>
                ))}
              </ul>

              <p className="mt-2 text-[11px] text-slate-500">
                선택된 문서를 확인한 뒤{" "}
                <span className="text-yellow-300 font-semibold">[시작하기]</span> 버튼을 눌러주세요.
              </p>
            </div>
          )}
        </div>

        {/* Hidden Inputs */}
        <input
          type="file"
          ref={pdfInputRef}
          className="hidden"
          accept="application/pdf"
          multiple={false}
          onChange={handleFilePicked("pdf")}
        />
        <input
          type="file"
          ref={imageInputRef}
          className="hidden"
          accept="image/*"
          multiple
          onChange={handleFilePicked("image")}
        />
      </div>

      <div className="absolute bottom-6 text-slate-600 text-xs">
        KEIT 2025 AI Challenge 참가작 &copy; DocuGuide AI 똑디Doc
      </div>
    </div>
  )
}
