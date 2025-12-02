"use client";

import { useState, useEffect } from "react";
import { Sparkles, ArrowLeft, MoreVertical, MessageSquare } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent } from "@/components/ui/sheet";
import {
  SidebarFileList,
  type DocumentFile,
  type AnalysisData,
} from "./sidebar-file-list";
import { AnalysisPanel } from "./analysis-panel";
import { ChatInterface, type ChatMessage } from "./chat-interface";
import { WelcomeScreen } from "./welcome-screen";
import { AppBrandingHeader } from "./app-branding-header";
import { FileSidebar } from "./file-sidebar";
import UploadModal from "./upload-modal";
import LoadingOverlay from "@/components/loading-overlay";

const INITIAL_FILES: DocumentFile[] = [];

const SplashScreen = ({ onComplete }: { onComplete: () => void }) => {
  useEffect(() => {
    const timer = setTimeout(onComplete, 2000);
    return () => clearTimeout(timer);
  }, [onComplete]);

  return (
    <div className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-slate-950 text-slate-200">
      <div className="w-24 h-24 mb-6 flex items-center justify-center rounded-2xl bg-cyan-950/30 shadow-lg">
        <Sparkles className="w-12 h-12 text-cyan-400 animate-pulse" />
      </div>
      <h1 className="text-2xl font-bold text-cyan-100">똑디 Doc!</h1>
      <p className="text-cyan-400/70 mt-2">당신의 똑똑한 디지털 문서 매니저</p>
    </div>
  );
};

export function DashboardApp() {
  const [uploadModalOpen, setUploadModalOpen] = useState(false);
  const [showSplash, setShowSplash] = useState(true);

  const [files, setFiles] = useState<DocumentFile[]>(INITIAL_FILES);
  const [selectedFileId, setSelectedFileId] = useState<string | null>(null);
  const [mobileView, setMobileView] = useState<"list" | "detail">("list");
  const [isMobileChatOpen, setIsMobileChatOpen] = useState(false);

  const [chatMessages, setChatMessages] = useState<
    Record<string, ChatMessage[]>
  >({});
  const [isUploading, setIsUploading] = useState(false);
  const [isTyping, setIsTyping] = useState(false);

  const [showLoading, setShowLoading] = useState(false);
  const [loadingFileName, setLoadingFileName] = useState("");

  const selectedFile = files.find((f) => f.id === selectedFileId) || null;

  const [docId, setDocId] = useState("");

  const startLoading = (fileName: string) => {
    setLoadingFileName(fileName);
    setShowLoading(true);
  };

  const handleFileSelect = (fileId: string) => {
    setSelectedFileId(fileId);
    setMobileView("detail");

    const file = files.find((f) => f.id === fileId);
    if (!file) return;
  };

  const handleBackToList = () => {
    setSelectedFileId(null);
    setMobileView("list");
  };

  const handleDeleteFile = (fileId: string) => {
    setFiles((prev) => prev.filter((f) => f.id !== fileId));
    setChatMessages((prev) => {
      const copy = { ...prev };
      delete copy[fileId];
      return copy;
    });

    if (selectedFileId === fileId) {
      setSelectedFileId(null);
      setMobileView("list");
    }
  };

  //   FastAPI /chat 호출 함수
  async function sendChatToBackend(docId: string, message: string) {
    const API_BASE = process.env.NEXT_PUBLIC_API_BASE;

    const res = await fetch(`${API_BASE}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        doc_id: docId,
        question: message,
      }),
    });


    const data = await res.json();
    return data;
  }

  //   채팅 메세지 전송
  const handleSendMessage = async (messageContent: string) => {
    if (!selectedFileId) return;

    const currentFile = files.find((f) => f.id === selectedFileId);
    if (!currentFile) return;

    const newMessage: ChatMessage = {
      id: Date.now().toString(),
      role: "user",
      content: messageContent,
      timestamp: new Date(),
    };

    setChatMessages((prev) => ({
      ...prev,
      [selectedFileId]: [...(prev[selectedFileId] || []), newMessage],
    }));

    setIsTyping(true);

    console.log("📨 챗봇 호출 doc_id:", currentFile.doc_id);
    const { answer, source } = await sendChatToBackend(
      currentFile.doc_id,
      messageContent
    );

    const aiResponse: ChatMessage = {
      id: (Date.now() + 1).toString(),
      role: "assistant",
      content: answer, // 문자열만 content에!
      source: source ?? null,
      timestamp: new Date(),
    };

    setChatMessages((prev) => ({
      ...prev,
      [selectedFileId]: [...(prev[selectedFileId] || []), aiResponse],
    }));

    setIsTyping(false);
  };

  //   파일 업로드 처리
  const uploadFiles = async (incomingFiles: File[]) => {
    if (incomingFiles.length === 0) return;

    console.log("uploadFiles 호출됨, files:", incomingFiles);

    setIsUploading(true);

    const displayName =
      incomingFiles.length === 1
        ? incomingFiles[0].name
        : `${incomingFiles[0].name} 외 ${incomingFiles.length - 1}개`;

    startLoading(displayName);

    const clientDocId = crypto.randomUUID(); // 브라우저 내장 UUID
    setDocId(clientDocId); // 로딩오버레이에 바로 전달할 값

    const formData = new FormData();
    formData.append("doc_id", clientDocId); // FastAPI로 같이 보냄
    incomingFiles.forEach((f) => formData.append("files", f));

    let backendSummary = "";
    let backendAction: { title: string; text: string }[] = [];
    let backendDocId = "";

    const API_BASE = process.env.NEXT_PUBLIC_API_BASE;

    try {
      const res = await fetch(`${API_BASE}/process-document`, {
        method: "POST",
        body: formData,
      });


      if (!res.ok) {
        const text = await res.text().catch(() => "");
        console.error("API status error:", res.status, text);
        backendSummary = `⚠️ API 오류: ${res.status}`;
        backendAction = [];
      } else {
        const data = await res.json();
        console.log("백엔드 응답:", data);

        backendDocId = data.doc_id;
        console.log("업로드 응답으로 받은 doc_id:", backendDocId);

        backendSummary = data.summary ?? "";
        const rawAction = data.action ?? [];
        backendAction = Array.isArray(rawAction) ? rawAction : [rawAction];
      }
    } catch (e) {
      console.error("ingestion API error:", e);
      backendSummary = "[오류]ingestion 오류 발생";
      backendAction = [];
    } finally {
      const totalSize = incomingFiles.reduce((acc, f) => acc + f.size, 0);

      const newFile: DocumentFile = {
        id: backendDocId, //프론트 파일 ID = 백엔드 doc_id
        doc_id: backendDocId,
        name: displayName,
        size: `${(totalSize / 1024 / 1024).toFixed(1)} MB`,
        uploadDate: "",
        status: "ready",
        fileType:
          incomingFiles.length === 1 &&
          incomingFiles[0].type === "application/pdf"
            ? "pdf"
            : "image-bundle",
        files: incomingFiles,
        analysis: {
          summary: backendSummary,
          action: backendAction,
        },
      };

      setFiles((prev) => [newFile, ...prev]);
      setIsUploading(false);
      setShowLoading(true);
      handleFileSelect(newFile.id);

      setChatMessages((prev) => ({
        ...prev,
        [newFile.id]: [
          {
            id: crypto.randomUUID(),
            role: "assistant",
            content: `안녕하세요! 똑디봇입니다🤖\n"${newFile.name}" 문서에 대해 무엇이든 물어보세요.`,
            timestamp: new Date(),
          },
        ],
      }));
    }
  };

  // ============================
  //   웰컴스크린 시작 처리
  // ============================

  const handleWelcomeStart = (filesToUpload: File[]) => {
    if (filesToUpload.length === 0) return;
    console.log("handleWelcomeStart 호출됨, files:", filesToUpload);
    uploadFiles(filesToUpload);
  };

  if (showSplash) {
    return <SplashScreen onComplete={() => setShowSplash(false)} />;
  }

  return (
    <>
      <LoadingOverlay
        visible={isUploading}
        fileName={loadingFileName} // ← 수정됨
        docId={docId}
      />

      {files.length === 0 ? (
        <WelcomeScreen
          onStartUpload={handleWelcomeStart}
          isUploading={isUploading}
        />
      ) : (
          <div className="h-screen w-full bg-slate-950 text-slate-200 flex flex-col">
          <UploadModal
            isOpen={uploadModalOpen}
            onClose={() => setUploadModalOpen(false)}
            onStartUpload={handleWelcomeStart}
            isUploading={isUploading}
          />

          {/* Mobile */}
          <div className="lg:hidden flex-1 flex flex-col relative overflow-y-auto touch-pan-y">
            {mobileView === "list" ? (
              <SidebarFileList
                files={files}
                selectedFileId={selectedFileId}
                onSelectFile={handleFileSelect}
                onDeleteFile={handleDeleteFile}
                isUploading={isUploading}
                onUploadClick={() => setUploadModalOpen(true)}
              />
            ) : (
              <div className="flex-1 flex flex-col">
                    <div className="h-14 border-b border-cyan-500/30 flex items-center px-4 bg-slate-900/80 backdrop-blur-lg sticky top-0 z-50">
                  <Button variant="ghost" size="icon" onClick={handleBackToList}>
                      <ArrowLeft className="h-5 w-5 text-cyan-400" />
                    </Button>

                    <span className="flex-1 font-semibold truncate">
                      {selectedFile?.name}
                    </span>

                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => setIsMobileChatOpen(true)}
                    >
                      <MessageSquare className="h-5 w-5 text-cyan-400" />
                    </Button>
                  </div>

                <div className="flex-1 overflow-y-auto">
                  {selectedFile && <AnalysisPanel file={selectedFile} />}
                </div>

                  <div className="fixed bottom-6 right-6 z-50">
                    <Button
                      size="lg"
                      className="h-14 w-14 rounded-full bg-gradient-to-r from-cyan-600 to-blue-600 shadow-xl"
                      onClick={() => setIsMobileChatOpen(true)}
                    >
                      <MessageSquare className="text-white" />
                    </Button>
                  </div>

                <Sheet
                  open={isMobileChatOpen}
                  onOpenChange={setIsMobileChatOpen}
                >
                    <SheetContent
                      side="bottom"
                      className="h-screen p-0 rounded-t-2xl overflow-y-auto"
                    >

                    <ChatInterface
                      file={selectedFile}
                      messages={
                        selectedFile ? chatMessages[selectedFile.id] || [] : []
                      }
                      onSendMessage={handleSendMessage}
                      isTyping={isTyping}
                      isMobile
                      onCloseMobile={() => setIsMobileChatOpen(false)}
                    />
                  </SheetContent>
                </Sheet>
              </div>
            )}
          </div>

          {/* Desktop */}
          <div className="hidden lg:flex h-full w-full">
            <FileSidebar className="">
              <SidebarFileList
                files={files}
                selectedFileId={selectedFileId}
                onSelectFile={handleFileSelect}
                onDeleteFile={handleDeleteFile}
                isUploading={isUploading}
                onUploadClick={() => setUploadModalOpen(true)}
              />
            </FileSidebar>

            <div className="flex-1 flex flex-col h-full overflow-hidden">
              <AppBrandingHeader />

              <div className="flex flex-1 overflow-hidden">
                <div className="flex-1 overflow-y-auto border-r border-cyan-500/30">
                  {selectedFile ? (
                    <AnalysisPanel file={selectedFile} />
                  ) : (
                    <div className="flex h-full justify-center items-center text-slate-500">
                      <div className="w-16 h-16 rounded-2xl bg-slate-900/50 border border-cyan-500/20 flex items-center justify-center mr-3">
                        <Sparkles className="w-8 h-8 text-cyan-500/50" />
                      </div>
                      <p>문서를 선택하여 분석 결과를 확인하세요</p>
                    </div>
                  )}
                </div>

                <div className="w-[450px] bg-slate-950/80 backdrop-blur-lg overflow-y-auto">
                  <ChatInterface
                    file={selectedFile}
                    messages={
                      selectedFile ? chatMessages[selectedFile.id] || [] : []
                    }
                    onSendMessage={handleSendMessage}
                    isTyping={isTyping}
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

export default DashboardApp;
