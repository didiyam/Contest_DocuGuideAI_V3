# ---------------------------------------------------------
# main.py : FastAPI 서버 파일(백엔드 파일) 
# 파일을 업로드 받고, 우리의 파이프라인을 최종적으로 돌리고
# 프론트(Next.js)로 분석결과를 JSON으로 보내주는 역할
# ---------------------------------------------------------
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import uuid
import os
from openai import OpenAI

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
from src.chatbot.rag_builder import insert_info   # 문서 행동 정보 → 벡터DB 저장
from src.chatbot.rag_chat_engine import generate_response  # RAG 기반 답변 엔진


# 진행상황 저장용 (간단 메모리 버전)
progress_store = {}   # {doc_id: "ocr"|"refine"|"analysis"|"summary"}

def set_progress(doc_id: str, step: str):
    print(f"[PROGRESS SET] doc_id={doc_id}, step={step}")
    progress_store[doc_id] = step

def get_progress(doc_id: str):
    return progress_store.get(doc_id, "pending")


# -------------------------
# 설정
API_KEY = load_api_keys()
client = OpenAI(api_key=API_KEY)

UPLOAD_DIR = "storage/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI()

#프론트에서 백엔드 API한테 요청할 수 있게 허용해 주는 보안 문구
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],    # 개발 단계라 전체 허용
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
    - 행동 정보(action_info)를 RAG 벡터DB에 저장 (insert_actions)
    - 결과 반환
    """

    # # 문서 고유 ID 생성
    # doc_id = uuid.uuid4().hex

# 1) 파일 저장
    saved_paths = []
    for f in files:
        file_id = uuid.uuid4().hex
        save_path = os.path.join(UPLOAD_DIR, f"{file_id}_{f.filename}")
        with open(save_path, "wb") as buffer:
            buffer.write(await f.read())
        saved_paths.append(save_path)


# 2) ingestion 실행 (정제 텍스트 생성)
# ingestion은 "여러 파일 → 하나의 문서" 처리가 이미 구현되어 있으므로
# saved 전체를 리스트로 그대로 넘긴다.
    state = {"input_paths": saved_paths}
    # ingestion 끝난 직후
    state = node_ingestion_pipeline(state)
    set_progress(doc_id, "analysis")  # 3단계 신호



    # list[str] 형태(db저장)
    refined_txt = state["refined_txt"]             # RAG db 저장용

    state["refined_text"] = state["refined_txt"]    # 추후 삭제예정⚠️(유환님)    


# 3) NER 실행 (엔티티, 문서유형/행동지시 정보)
    state = node_ner_extractor(state)


# 4) result packager 실행
    # result 끝난 직후
    state = node_result(state)
    set_progress(doc_id, "summary")  # 마지막 단계

    action_info = state["action_info"]      # RAG db 저장용
    web_package = state["web_package"]      # [{"title": "...", "text": "..."},...]
    summary = state["summary"]              # 프론트 반환용 요약문


# 5) RAG 벡터DB 저장
    insert_info( doc_id=doc_id, action_info=action_info, refined_txt=refined_txt)
    print(f"RAG 저장 완료 (doc_id={doc_id})")



# 6) 프론트 반환값
    return {
        "doc_id": doc_id,  # 프론트에서 챗봇 요청 시 사용
        "summary" : summary,
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
    """
    문서별(doc_id)로 RAG 검색 → generate_response 실행
    """

    # generate_response를 doc_id 기반으로 확장한 버전 사용해야 함
    result = generate_response(
        doc_id = req.doc_id,
        user_query=req.question
    )


    return ChatResponse(
        answer = result["answer"],
        source = result["source"]
    )

# =============================================================
#  3. /progress/{doc_id}  (진행상황 조회)
# =============================================================
@app.get("/progress/{doc_id}")
async def progress(doc_id: str):
    print(">>> PROGRESS GET:", doc_id, "stored:", progress_store.get(doc_id))
    return {"step": get_progress(doc_id)}
