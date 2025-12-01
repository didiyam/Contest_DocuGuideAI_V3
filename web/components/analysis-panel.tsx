"use client"
import { FileText, Sparkles, ClipboardList } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import type { DocumentFile } from "./sidebar-file-list"
import { AnimatedCheck } from "@/components/animatedCheck"


interface AnalysisPanelProps {
  file: DocumentFile
}

export function AnalysisPanel({ file }: AnalysisPanelProps) {
  if (!file.analysis) return null

  return (
    <div className="h-full flex flex-col animate-in fade-in duration-300 bg-slate-950">
      {/* Scrollable Content */}
      <div className="flex-1 ScrollArea custom-scrollbar">

        {/* File Header */}
        <div className="px-6 py-2 border-b border-cyan-500/10 bg-slate-900/30">
          <div className="flex items-center gap-2">
            <div className="h-5 w-5 rounded bg-cyan-950/30 border border-cyan-500/20 flex items-center justify-center text-cyan-400/70">
              <FileText className="h-3 w-3" />
            </div>
            <h2 className="text-xs font-medium text-slate-500 truncate">
              {file.name}
            </h2>
          </div>
        </div>

        <div className="p-6 space-y-6 max-w-3xl mx-auto pb-20">

          {/* Executive Summary */}
          <section>
            <h3 className="text-sm font-medium text-cyan-400 mb-3 uppercase tracking-wider flex items-center gap-2">
              <Sparkles className="w-4 h-4" /> Doc Summary
            </h3>

            <Card className="border border-cyan-500/30 bg-slate-900/60 rounded-lg shadow-none">
              <CardContent className="px-4 py-3 leading-relaxed text-sm md:text-sm text-slate-400 space-y-1.5">


                {file.analysis.summary
                  .split(/[\n]/)  // ← '-', '•' 제거 추천
                  .map((para, i) =>
                    para.trim() && (
                      <p
                        key={i}
                        className="pl-1"
                        style={{ whiteSpace: "pre-line", wordBreak: "break-word" }}
                      >
                        {para.trim()}
                      </p>
                    )
                  )
                }


              </CardContent>
            </Card>


          </section>

          {/* Recommended Actions */}
          <section>
            <h3 className="text-sm font-medium text-cyan-400 mb-3 uppercase tracking-wider flex items-center gap-2">
              <ClipboardList className="w-4 h-4" />
              To do List
            </h3>


            <div className="space-y-5">

              {file.analysis.action.map((item, i) => (
                <div
                  key={i}
                  className="flex gap-4 items-start p-4 rounded-xl 
                 bg-slate-900/70 border border-cyan-500/10
                 sm:flex-row flex-col sm:items-start items-center"
                >

                  {/* 체크 아이콘 */}
                  <div className="flex items-center justify-center 
                      h-8 w-8 rounded-full border border-cyan-400/50 
                      bg-slate-950 shadow-[0_0_12px_rgba(34,211,238,0.35)]
                      hover:shadow-[0_0_20px_rgba(34,211,238,0.6)]
                      hover:scale-110 transition-all duration-300">
                    <AnimatedCheck />
                  </div>

                  {/* 텍스트 */}
                  <div className="flex-1 sm:text-left text-center">
                    <div className="text-base font-bold text-cyan-200 mb-1">
                      {item.title}
                    </div>

                    <p className="text-sm md:text-sm text-slate-200 whitespace-pre-line leading-relaxed">
                      {item.text}
                    </p>

                  </div>

                </div>
              ))}

            </div>

          </section>


        </div>
      </div>
    </div>
  )
}
