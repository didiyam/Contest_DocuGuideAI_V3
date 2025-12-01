"use client"

import type React from "react"

import { useState, useRef, useEffect } from "react"
import { Bot, Sparkles, X, Paperclip, Send } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { cn } from "@/lib/utils"
import type { DocumentFile } from "./sidebar-file-list"

export interface ChatMessage {
  id: string
  role: "user" | "assistant"
  content: string
  timestamp: Date
  source?: string
}

/** **텍스트** 부분을 <strong>으로 바꿔서 렌더하는 헬퍼 */
function renderMessageContent(content: string) {
  // **굵게** 부분을 기준으로 잘라서 JSX로 변환
  const segments = content.split(/(\*\*[^*]+\*\*)/g)

  return segments.map((seg, i) => {
    const boldMatch = seg.match(/^\*\*(.*)\*\*$/)
    if (boldMatch) {
      // **안쪽 텍스트만 굵게
      return (
        <strong key={i} className="font-semibold">
          {boldMatch[1]}
        </strong>
      )
    }
    return <span key={i}>{seg}</span>
  })
}

interface ChatInterfaceProps {
  file: DocumentFile | null
  messages: ChatMessage[]
  onSendMessage: (message: string) => void
  isTyping: boolean
  isMobile?: boolean
  onCloseMobile?: () => void
}

export function ChatInterface({
  file,
  messages,
  onSendMessage,
  isTyping,
  isMobile = false,
  onCloseMobile,
}: ChatInterfaceProps) {
  const [inputMessage, setInputMessage] = useState("")
  const chatScrollRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const [openSourceId, setOpenSourceId] = useState<string | null>(null)


  // Auto-scroll to bottom when messages change
  useEffect(() => {
    if (chatScrollRef.current) {
      chatScrollRef.current.scrollTop = chatScrollRef.current.scrollHeight
    }
  }, [messages, isTyping, file?.id])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!inputMessage.trim() || !file) return

    onSendMessage(inputMessage)
    setInputMessage("")
  }

  if (!file) {
    return (
      <div className="h-full flex flex-col items-center justify-center text-center p-8 text-slate-500 bg-slate-950">
        <Bot className="h-12 w-12 mb-4 opacity-20" />
        <p>Select a file to start chatting</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full bg-slate-950 border-l border-cyan-500/30">
      {/* Chat Header */}
      <div className="p-3 border-b border-cyan-500/30 flex items-center justify-between bg-slate-900/80 backdrop-blur-md sticky top-0 z-10">
        <div className="flex items-center gap-2">
          <Bot className="h-4 w-4 text-cyan-400" />
          <span className="font-medium text-slate-200 text-sm">똑디봇</span>
        </div>
        {isMobile && onCloseMobile && (
          <Button variant="ghost" size="icon" onClick={onCloseMobile} className="text-slate-400 hover:text-slate-200">
            <X className="h-4 w-4" />
          </Button>
        )}
      </div>

      {/* Messages Area */}
      <div
        className="flex-1 overflow-y-auto ScrollArea p-4 space-y-4"
        ref={chatScrollRef}
      >
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center space-y-4 opacity-50">
            <div className="h-12 w-12 rounded-full bg-cyan-950/50 border border-cyan-500/30 flex items-center justify-center">
              <Sparkles className="h-6 w-6 text-cyan-400" />
            </div>
            <div className="max-w-[200px] text-slate-400">
              <p className="text-sm font-medium">Ask me anything about</p>
              <p className="text-xs text-cyan-400 mt-1">"{file.name}"</p>
            </div>
          </div>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              className={cn("flex gap-3 max-w-[85%]", msg.role === "user" ? "ml-auto flex-row-reverse" : "")}
            >
              <Avatar className="h-8 w-8 shrink-0 ring-1 ring-cyan-500/30">
                {msg.role === "assistant" ? (
                  <>
                    <AvatarImage src="/bot-avatar.png" />
                    <AvatarFallback className="bg-slate-900 text-cyan-400">
                      <Bot className="h-4 w-4" />
                    </AvatarFallback>
                  </>
                ) : (
                  <>
                    <AvatarImage src="/user-avatar.png" />
                    <AvatarFallback className="bg-cyan-900 text-cyan-100">
                      <span className="text-xs">ME</span>
                    </AvatarFallback>
                  </>
                )}
              </Avatar>
              <div
                className={cn(
                  "p-3 rounded-2xl text-sm",
                  msg.role === "user"
                    ? "bg-cyan-700 text-white rounded-tr-none shadow-[0_0_10px_rgba(34,211,238,0.2)]"
                    : "bg-slate-800 text-gray-200 border border-slate-700 rounded-tl-none",
                )}
                style={{ whiteSpace: "pre-line", wordBreak: "break-word" }}
              >
                {/* 본문 텍스트 */}
                {renderMessageContent(msg.content)}

                {/* ⭐ 문서출처 버튼 + 토글영역 */}
                {msg.role === "assistant" && msg.source && (
                  <div className="mt-2 text-xs text-cyan-300">
                    <button
                      type="button"
                      className="underline decoration-dotted hover:text-cyan-200"
                      onClick={() =>
                        setOpenSourceId((prev) => (prev === msg.id ? null : msg.id))
                      }
                    >
                      [문서출처]
                    </button>

                    {openSourceId === msg.id && (
                      <div className="mt-1 whitespace-pre-line text-slate-400 border border-cyan-500/20 rounded-lg p-2 bg-slate-900/60">
                        {msg.source}
                      </div>
                    )}
                  </div>
                )}
              </div>

            </div>
          ))
        )}

        {/* Typing Indicator */}
        {isTyping && (
          <div className="flex gap-3 max-w-[85%]">
            <Avatar className="h-8 w-8 shrink-0 ring-1 ring-cyan-500/30">
              <AvatarFallback className="bg-slate-900 text-cyan-400">
                <Bot className="h-4 w-4" />
              </AvatarFallback>
            </Avatar>
            <div className="p-3 rounded-2xl rounded-tl-none bg-slate-800 text-gray-200 border border-slate-700 flex items-center gap-2">
              <span className="animate-pulse">...</span>
              <span className="text-xs text-cyan-400/70">{file.name} 문서 기준 답변 생성 중</span>
            </div>
          </div>
        )}
      </div>

      {/* Input Area */}
      {/* Input Area */}
      <div className="p-4 border-t border-cyan-500/30 bg-slate-900/80 backdrop-blur-md sticky bottom-0">
        <form onSubmit={handleSubmit} className="relative flex items-center gap-2">
          <Input
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            placeholder="Ask a question..."
            className="flex-1 pr-10 bg-slate-900/50 border-cyan-500/20 text-slate-200 placeholder:text-slate-500 focus-visible:ring-cyan-500/50"
          />
          <Button
            type="submit"
            size="icon"
            disabled={!inputMessage.trim() || isTyping}
            className={cn(
              "absolute right-1 h-8 w-8 transition-all bg-gradient-to-r from-cyan-600 to-blue-600 hover:shadow-lg hover:shadow-cyan-500/50 border-none",
              inputMessage.trim() ? "opacity-100 scale-100" : "opacity-0 scale-90",
            )}
          >
            <Send className="h-4 w-4 text-white" />
          </Button>
        </form>
      </div>
    </div>
  )
}
