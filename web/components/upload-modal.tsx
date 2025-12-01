"use client"

import { X, Image as ImageIcon, FileText } from "lucide-react"
import { useState } from "react"

interface UploadModalProps {
    isOpen: boolean
    onClose: () => void
    onStartUpload: (files: File[]) => void
    isUploading: boolean
}

export default function UploadModal({
    isOpen,
    onClose,
    onStartUpload,
    isUploading
}: UploadModalProps) {
    const [selectedFiles, setSelectedFiles] = useState<File[]>([])

    if (!isOpen) return null

    const handlePDFSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
        const files = Array.from(e.target.files || [])
        setSelectedFiles(files)
    }

    const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
        const files = Array.from(e.target.files || [])
        setSelectedFiles(files)
    }

    // ❗ 시작하기 버튼: 모달 먼저 닫고 DashboardApp에서 로딩 제어
    const handleStart = () => {
        if (selectedFiles.length === 0) return
        onClose()
        onStartUpload(selectedFiles)
        setSelectedFiles([])
    }

    // 개별 삭제
    const handleRemoveSingle = (index: number) => {
        setSelectedFiles(prev => prev.filter((_, i) => i !== index))
    }

    // 전체 삭제
    const handleRemoveAll = () => {
        setSelectedFiles([])
    }

    return (
        <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/60 backdrop-blur-sm">
            <div className="relative w-[90%] max-w-[500px] bg-slate-950 border border-cyan-500/40 rounded-xl p-6 shadow-xl">

                {/* Close Button */}
                <button
                    onClick={onClose}
                    className="absolute top-4 right-4 text-slate-400 hover:text-white"
                >
                    <X className="w-6 h-6" />
                </button>

                {/* Title */}
                <h2 className="text-xl font-bold text-cyan-300 mb-4 text-center">
                    문서 업로드
                </h2>

                {/* 🔵 선택된 파일 없을 때만 업로드 버튼 노출 */}
                {selectedFiles.length === 0 && (
                    <div className="flex gap-3 mb-6">
                        {/* PDF 업로드 */}
                        <label className="flex-1 cursor-pointer flex items-center justify-center gap-2 bg-slate-900 p-3 rounded-lg border border-cyan-500/30 hover:bg-slate-800">
                            <FileText className="text-cyan-400" />
                            PDF 업로드
                            <input
                                type="file"
                                accept="application/pdf"
                                className="hidden"
                                onChange={handlePDFSelect}
                            />
                        </label>

                        {/* 이미지 업로드 */}
                        <label className="flex-1 cursor-pointer flex items-center justify-center gap-2 bg-slate-900 p-3 rounded-lg border border-cyan-500/30 hover:bg-slate-800">
                            <ImageIcon className="text-cyan-400" />
                            이미지 업로드
                            <input
                                type="file"
                                accept="image/*"
                                multiple
                                className="hidden"
                                onChange={handleImageSelect}
                            />
                        </label>
                    </div>
                )}

                {/* 🔵 선택된 파일 목록 */}
                {selectedFiles.length > 0 && (
                    <div className="mb-4 bg-slate-900 p-3 rounded-lg border border-cyan-500/20">

                        {/* 상단: 제목 + 다시 선택하기 */}
                        <div className="flex justify-between items-center mb-2">
                            <p className="text-sm text-cyan-300 font-semibold">선택한 문서</p>

                            <button
                                onClick={handleRemoveAll}
                                className="text-xs text-slate-400 hover:text-blue-300 transition"
                            >
                                다시 선택하기
                            </button>
                        </div>

                        {/* 파일 리스트 */}
                        <ul className="space-y-2">
                            {selectedFiles.map((file, index) => (
                                <li
                                    key={index}
                                    className="flex justify-between items-center bg-slate-800/60 p-2 rounded-md text-sm text-slate-200"
                                >
                                    <span className="truncate">{file.name}</span>

                                    {/* 개별 삭제 */}
                                    <button
                                        onClick={() => handleRemoveSingle(index)}
                                        className="text-red-400 hover:text-red-300 px-2"
                                    >
                                        ✕
                                    </button>
                                </li>
                            ))}
                        </ul>
                    </div>
                )}

                {/* Start Button */}
                <button
                    onClick={handleStart}
                    disabled={selectedFiles.length === 0 || isUploading}
                    className="w-full bg-gradient-to-r from-cyan-600 to-blue-600 hover:opacity-90 text-white py-3 rounded-lg font-semibold mt-4 disabled:opacity-40"
                >
                    {/* isUploading은 더 이상 모달에서 사용하지 않지만 props 형태는 유지 */}
                    {isUploading ? "업로드 중..." : "시작하기"}
                </button>

            </div>
        </div>
    )
}
