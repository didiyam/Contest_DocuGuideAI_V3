import { Bot, Sparkles } from "lucide-react"

export function AppBrandingHeader() {
  return (
    <div className="h-16 flex items-center px-6 bg-slate-900/50 backdrop-blur-xl border-b border-cyan-500/30 w-full">
      <div className="flex items-center gap-4">
        {/* Cute AI Character Placeholder */}
        <div className="relative flex items-center justify-center w-10 h-10 rounded-full bg-gradient-to-b from-cyan-900 to-slate-900 ring-2 ring-cyan-400/50 shadow-[0_0_20px_rgba(34,211,238,0.4)] animate-pulse-slow">
          <div className="absolute inset-0 rounded-full bg-cyan-400/10 animate-ping-slow" />
          <Bot className="w-6 h-6 text-cyan-300 relative z-10" />
          <Sparkles className="absolute -top-1 -right-1 w-3 h-3 text-yellow-300 animate-bounce" />
        </div>

        <div className="flex flex-col justify-center">
          <h1 className="text-xl font-bold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-cyan-200 to-blue-100 drop-shadow-[0_0_10px_rgba(34,211,238,0.5)]">
            똑디 Doc!
          </h1>
          <p className="text-[10px] font-medium text-cyan-400/80 tracking-wide">당신의 똑똑한 디지털 문서 매니저</p>
        </div>
      </div>
    </div>
  )
}
