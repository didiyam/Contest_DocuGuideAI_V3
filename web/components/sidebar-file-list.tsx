"use client"

import type React from "react"
import { useRef, useState } from "react"
import { FileText, Upload, Search, Trash2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { cn } from "@/lib/utils"

export type FileStatus = "uploading" | "processing" | "ready" | "error"

export interface DocumentFile {
  id: string
  name: string
  size: string
  uploadDate: string
  status: FileStatus
  fileType: "pdf" | "image-bundle"
  files: File[]
  analysis?: AnalysisData
  doc_id: string
}

export interface AnalysisData {
  summary: string
  action: {
    title: string
    text: string
  }[]
}

interface SidebarFileListProps {
  files: DocumentFile[]
  selectedFileId: string | null
  onSelectFile: (id: string) => void
  onDeleteFile: (id: string) => void
  isUploading: boolean
  onUploadClick: () => void
  className?: string
}

export function SidebarFileList({
  files,
  selectedFileId,
  onSelectFile,
  onDeleteFile,
  isUploading,
  onUploadClick,
  className,
}: SidebarFileListProps) {

  // 검색 입력값 & 검색 트리거값
  const [searchText, setSearchText] = useState("");
  const [searchQuery, setSearchQuery] = useState("");

  const handleDeleteClick = (e: React.MouseEvent, fileId: string) => {
    e.stopPropagation()
    if (window.confirm("해당 문서를 삭제하시겠습니까? \n문서에 포함된 정보와 대화기록도 삭제됩니다.")) {
      onDeleteFile(fileId)
    }
  }

  return (
    <div className={cn("flex flex-col h-full bg-slate-950", className)}>
      {/* Header */}
      <div className="p-4 border-b border-cyan-500/30 flex flex-col gap-3 bg-slate-900/30 sticky top-0 z-10 backdrop-blur-sm">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-cyan-400/70 uppercase tracking-wider">
            Files
          </span>

          {/* Upload */}
          <Button
            size="sm"
            className="h-7 text-xs bg-cyan-950/50 hover:bg-cyan-900/50 border border-cyan-500/30 text-cyan-400"
            onClick={onUploadClick}
            disabled={isUploading}
          >
            {isUploading ? (
              <span className="animate-spin mr-1">⏳</span>
            ) : (
              <Upload className="h-3 w-3 mr-1" />
            )}
            Upload
          </Button>
        </div>

        {/* Search Input */}
        <div className="relative">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-cyan-400/50" />
          <Input
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                setSearchQuery(searchText)
              }
            }}
            placeholder="Search files..."
            className="pl-9 h-9 text-sm bg-slate-900/50 border-cyan-500/20 text-slate-200 placeholder:text-slate-500 focus-visible:ring-cyan-500/50"
          />
        </div>
      </div>

      {/* List */}
      <div className="p-3 flex-1 ScrollArea custom-scrollbar">
        <div className="space-y-2">

          {files
            .filter((file) =>
              file.name.toLowerCase().includes(searchQuery.toLowerCase())
            )
            .map((file) => (
              <div
                key={file.id}
                onClick={() => onSelectFile(file.id)}
                className={cn(
                  "group flex items-center gap-3 p-3 rounded-xl border transition-all cursor-pointer relative pr-10",
                  selectedFileId === file.id
                    ? "bg-cyan-950/50 border-cyan-400 shadow-[0_0_15px_rgba(34,211,238,0.3)]"
                    : "bg-slate-900/30 border-transparent hover:bg-slate-800/50 hover:border-cyan-500/30",
                )}
              >
                <div
                  className={cn(
                    "h-10 w-10 rounded-lg flex items-center justify-center transition-colors shrink-0",
                    selectedFileId === file.id
                      ? "bg-cyan-500/20 text-cyan-400"
                      : "bg-slate-800/50 text-slate-400 group-hover:text-cyan-400",
                  )}
                >
                  <FileText className="h-5 w-5" />
                </div>

                <div className="flex-1 min-w-0">
                  <h4
                    className={cn(
                      "text-sm font-medium truncate",
                      selectedFileId === file.id ? "text-cyan-100" : "text-slate-300",
                    )}
                  >
                    {file.name}
                  </h4>
                  <div className="flex items-center gap-2 text-xs text-slate-500 mt-0.5">
                    <span>{file.size}</span>
                    <span>•</span>
                    <span>{file.uploadDate}</span>
                  </div>
                </div>

                {/* Delete */}
                <button
                  onClick={(e) => handleDeleteClick(e, file.id)}
                  className={cn(
                    "absolute right-2 p-1.5 rounded-md text-slate-500 hover:text-red-400 hover:bg-red-950/30 transition-all opacity-0 group-hover:opacity-100",
                    selectedFileId === file.id && "opacity-100",
                  )}
                >
                  <Trash2 className="h-4 w-4" />
                </button>

                {selectedFileId === file.id && (
                  <div className="absolute right-0 top-0 bottom-0 w-1 bg-cyan-400 rounded-r-xl shadow-[0_0_10px_rgba(34,211,238,0.5)]" />
                )}
              </div>
            ))}
        </div>
      </div>
    </div>
  )
}
