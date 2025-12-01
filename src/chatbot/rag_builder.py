"""
Windows용 안전 챗봇 RAG (SQLite 영구 저장)
SentenceTransformer 제거 버전
OpenAI Embedding(text-embedding-3-small) 사용
"""
 
import os
import uuid
import json
import pickle
import sqlite3
import numpy as np
from typing import List, Dict, Any
 
from openai import OpenAI
from src.utils.config import load_api_keys
API_KEY = load_api_keys()
client = OpenAI(api_key=API_KEY)   
 
# 0) 경로 설정 및 DB 초기화
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STORAGE_DIR = os.path.join(BASE_DIR, "storage")
os.makedirs(STORAGE_DIR, exist_ok=True)
 
DB_PATH = os.path.join(STORAGE_DIR, "rag_db.sqlite")
 
 
def get_conn():
    """SQLite Connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
 
 
def init_db():
    """embeddings 테이블 생성"""
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS embeddings (
                id TEXT PRIMARY KEY,
                doc_id TEXT NOT NULL,
                type TEXT,
                page_num INTEGER,
                text TEXT,
                embedding BLOB NOT NULL,
                metadata TEXT
            )
            """
        )
        conn.commit()
 
 
# 모듈 로드 시 실행
init_db()
 
# 1) OpenAI Embedding 함수
def embed_text(text: str) -> np.ndarray:
    """
    OpenAI text-embedding-3-small 사용
    SentenceTransformer 대체
    """
    if not text:
        text = ""
    try:
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return np.array(response.data[0].embedding, dtype=np.float32)
    except Exception as e:
        print(" Embedding Error:", e)
        # fallback: zero vector
        return np.zeros(1536, dtype=np.float32)
 
 
# 2) dict → 문장 변환
def dict_to_sentence(item: dict) -> str:
    parts = []
    if item.get("who"):
        parts.append(f"주체: {item['who']}")
    if item.get("action"):
        parts.append(f"행동: {item['action']}")
    if item.get("when"):
        parts.append(f"기한: {item['when']}")
    if item.get("how"):
        parts.append(f"방법: {item['how']}")
    if item.get("where"):
        parts.append(f"장소: {item['where']}")
    return " / ".join(parts)
 
 
# 3) (레거시) 메모리 vector DB — 유지
vector_db: List[Dict[str, Any]] = []
 
 
def insert_actions(action_list):
    """테스트용 in-memory 저장 — RAG와는 무관"""
    for item in action_list:
        sentence = dict_to_sentence(item)
        embedding_vec = embed_text(sentence).tolist()
 
        vector_db.append(
            {
                "id": str(uuid.uuid4()),
                "embedding": embedding_vec,
                "text": sentence,
                "metadata": item,
            }
        )
    print(f"[레거시] 메모리 DB에 {len(action_list)}개 저장 완료")
 
 
# 4) 본 기능: doc_id 단위로 SQLite에 저장
def insert_info(doc_id: str, action_info: list, refined_txt: List[str]):
    """
    RAG 저장 함수: 행동(action) + 페이지 텍스트(refined_txt)
    """
    with get_conn() as conn:
        cur = conn.cursor()
        inserted = 0
 
        # 1) 행동(action_info)
        if action_info:
            for item in action_info:
                sentence = dict_to_sentence(item)
                if not sentence.strip():
                    continue
 
                embedding_vec = embed_text(sentence)
                emb_blob = pickle.dumps(embedding_vec)
 
                cur.execute(
                    """
                    INSERT INTO embeddings (id, doc_id, type, page_num, text, embedding, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        uuid.uuid4().hex,
                        doc_id,
                        "action",
                        None,
                        sentence,
                        emb_blob,
                        json.dumps(item, ensure_ascii=False),
                    ),
                )
                inserted += 1
 
        # 2) refined_txt (페이지 텍스트)
        if refined_txt:
            for idx, page_text in enumerate(refined_txt):
                clean_text = (page_text or "").strip()
                if not clean_text:
                    continue
 
                embedding_vec = embed_text(clean_text)
                emb_blob = pickle.dumps(embedding_vec)
 
                cur.execute(
                    """
                    INSERT INTO embeddings (id, doc_id, type, page_num, text, embedding, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        uuid.uuid4().hex,
                        doc_id,
                        "page",
                        idx + 1,
                        clean_text,
                        emb_blob,
                        json.dumps({"page": idx + 1}, ensure_ascii=False),
                    ),
                )
                inserted += 1
 
        conn.commit()
 
    print(f" [SQLite] doc_id={doc_id} → {inserted}개 항목 저장 완료")
 
 
# 5) (레거시) in-memory 검색
def search_actions(query: str, top_k: int = 3):
    """테스트용 in-memory vector DB 검색"""
    if not vector_db:
        return []
 
    query_vec = embed_text(query)
 
    def cosine(a, b):
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))
 
    scores = [(cosine(query_vec, np.array(item["embedding"])), item) for item in vector_db]
    scores.sort(key=lambda x: x[0], reverse=True)
 
    return [item for score, item in scores[:top_k]]
 
 
# 6) SQLite 기반 RAG 검색
def search_rag(doc_id: str, query: str, top_k: int = 5):
    """
    문서 단위 RAG 검색
    action_info + refined_txt 전체 검색
    """
    query_vec = embed_text(query)
 
    # DB에서 doc_id 해당하는 embedding 모두 가져오기
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, doc_id, type, page_num, text, embedding, metadata
            FROM embeddings
            WHERE doc_id = ?
            """,
            (doc_id,),
        )
        rows = cur.fetchall()
 
    if not rows:
        print(f"!! doc_id={doc_id} 데이터 없음")
        return []
 
    def cosine(a, b):
        return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))
 
    scored_items = []
    for row in rows:
        emb_vec = pickle.loads(row["embedding"])  # np.array(float32)
        score = cosine(query_vec, emb_vec)
 
        item = {
            "id": row["id"],
            "doc_id": row["doc_id"],
            "type": row["type"],
            "page_num": row["page_num"],
            "text": row["text"],
            "embedding": emb_vec.tolist(),
            "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
            "score": score,
        }
        scored_items.append((score, item))
 
    scored_items.sort(key=lambda x: x[0], reverse=True)
 
    return [item for score, item in scored_items[:top_k]]
 
 
# 7) 간단 답변 생성 예시
def generate_answer(user_query: str):
    """레거시 in-memory 검색 예시"""
    items = search_actions(user_query)
    if not items:
        return "관련 내용을 찾지 못했습니다."
 
    msg = "관련된 안내입니다:\n"
    for it in items:
        msg += f"- {it['text']}\n"
    return msg