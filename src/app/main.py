# ---------------------------------------------------------
# main.py : FastAPI 서버 파일(백엔드 파일) 
# ---------------------------------------------------------
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import run_in_threadpool   # ⭐ NEW: heavy 작업을 스레드에서 실행시키기
from pydantic import BaseModel
from typing import List
import uuid
import os

# -------------------------
# Import: 문서 파이프라인 노드
# -------------------------
from src.utils.config import load_api_keys
from src.ingestion.node_ingestion_pipeline import node_ingestion_pipeline
from src.analyze.node_ner_extractor import node_ner_extractor
from src.result.node_result import node_result

# -------------------------
# Import: 챗봇 모듈
# -------------------------
from src.chatbot.rag_builder import insert_info
from src.chatbot.rag_chat_engine import generate_response


# 진행상황 저장용
progress_store = {}   # {doc_id: "ocr"|"refine"|"analysis"|"summary"}

def set_progress(doc_id: str, step: str):
    print(f"[PROGRESS SET] doc_id={doc_id}, step={step}")
    progress_store[doc_id] = step

def get_progress(doc_id: str):
    return progress_store.get(doc_id, "pending")


# -------------------------
# 설정
load_api_keys()

UPLOAD_DIR = "storage/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # 개발 단계라 전체 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================================================
#  1. /process-document  (문서 결과물 처리 파이프라인)
# =============================================================
@app.post("/process-document")
async def process_document(
    files: List[UploadFile] = File(...),
    doc_id: str = Form(...),
):

    """
    - 파일 업로드
    - ingestion → ner → result
    - RAG DB 저장
    - 결과 반환
    """

    # 1) 파일 저장
    saved_paths = []
    for f in files:
        file_id = uuid.uuid4().hex
        save_path = os.path.join(UPLOAD_DIR, f"{file_id}_{f.filename}")
        with open(save_path, "wb") as buffer:
            buffer.write(await f.read())
        saved_paths.append(save_path)

    # 2) ingestion 실행
    set_progress(doc_id, "ocr")    # 단계 1 시작

    state = {"input_paths": saved_paths}

    # ⭐ 수정됨: CPU-heavy 작업을 thread pool에서 실행
    state = await run_in_threadpool(node_ingestion_pipeline, state)

    refined_txt = state["refined_txt"]
    state["refined_text"] = refined_txt  # 유지


    # 3) NER 실행
    set_progress(doc_id, "refine")   # 단계 2 시작

    # ⭐ 수정됨
    state = await run_in_threadpool(node_ner_extractor, state)


    # 4) result packager 실행
    set_progress(doc_id, "analysis")  # 단계 3 시작

    # ⭐ 수정됨
    state = await run_in_threadpool(node_result, state)

    # 결과 unpack
    action_info = state["action_info"]
    web_package = state["web_package"]
    summary = state["summary"]

    # 마지막 단계
    set_progress(doc_id, "summary")   # 단계 4
    
    # 5) RAG 벡터DB 저장
    # ⭐ 수정됨: DB 저장도 thread로 분리 (blocking 방지)
    await run_in_threadpool(insert_info, doc_id, action_info, refined_txt)
    print(f"RAG 저장 완료 (doc_id={doc_id})")

    


    # 6) 프론트 반환
    return {
        "doc_id": doc_id,
        "summary": summary,
        "action": web_package
    }


# =============================================================
#  2. /chat  (문서 기반 챗봇)
# =============================================================
class ChatRequest(BaseModel):
    doc_id: str
    question: str

class ChatResponse(BaseModel):
    answer: str
    source: str | None


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):

    result = generate_response(
        doc_id=req.doc_id,
        user_query=req.question
    )

    return ChatResponse(
        answer=result["answer"],
        source=result["source"]
    )


# =============================================================
#  3. /progress/{doc_id}  (진행상황 조회)
# =============================================================
@app.get("/progress/{doc_id}")
async def progress(doc_id: str):
    print(">>> PROGRESS GET:", doc_id, "stored:", progress_store.get(doc_id))
    return {"step": get_progress(doc_id)}
