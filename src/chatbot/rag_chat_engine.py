"""
RAG 기반 안전 챗봇 엔진
- 사용자의 질문을 받아 벡터DB 검색 수행
- 검색된 근거 기반으로 LLM 답변 생성
- 답변 기록(state) 관리 (최대 3개 슬롯)
- 초과 시 자동 요약 저장
"""
from src.chatbot.rag_builder import search_rag, embed_text # 이진아 추가 (벡터DB 검색 모듈)
from openai import OpenAI
from src.utils.config import load_api_keys


# "gpt-5.1-chat-latest" 써서 제출하기
# -------------------------------
# call_llm_chat 구현 (문서 기반 챗봇)
# -------------------------------
def call_llm_chat(prompt: str) -> str:
    """
    문서 기반 챗봇 응답 생성용 LLM 호출 함수
    - JSON 출력 강제 없음
    - 자연어 답변 + bullet 가능
    """
    API_KEY = load_api_keys()
    client = OpenAI(api_key=API_KEY)   

    resp = client.chat.completions.create(
        model="gpt-5.1-chat-latest" ,
        messages=[
            {
                "role": "system",
                "content": (
                    "너는 공공문서 기반 질문에 정확하고 친절하게 답변하는 AI 챗봇이야. "
                    "절대 JSON으로 답변하지 말고, 자연어 문장 또는 bullet 형식으로만 말해."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        # temperature=0.2
    )

    return resp.choices[0].message.content.strip()
# ------------------------------
# 1) state 구조 정의
# ------------------------------
state = {
    "history": [],       # [{"question": str, "answer": str}]
    "summary": "",        # 오래된 기록 요약 저장
    "present_answer": ""    # 진아님 요청사항(2025-11-27)
}


# ------------------------------
# 2) 오래된 기록 요약하는 함수
# ------------------------------
def summarize_history(history_list, existing_summary=""):
    """
    질문·답변 기록(history)을 요약하는 함수
    LLM을 이용해 기존 summary + 삭제되는 기록 요약
    """

    text_to_summarize = existing_summary + "\n".join(
        [f"Q: {item['question']}\nA: {item['answer']}" for item in history_list]
    )

    prompt = f"""
    다음 대화기록을 짧고 핵심만 남도록 요약하세요.
    사용자 질문과 챗봇 답변의 흐름이 유지되도록 정리해주세요.

    대화 기록:
    {text_to_summarize}
    """

    return call_llm_chat(prompt).strip()
# -----------------------------------------------------------------------------------
import re
import numpy as np

# 문장 분리
def split_sentences(text: str):
    sentences = re.split(r'(?<=[.!?…\n])\s+', text)
    return [s.strip() for s in sentences if len(s.strip()) > 5]


# 코사인 유사도
def cosine_sim(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


# 질문 vs 문서 문장 유사도 기반 최적 문장 찾기
def find_best_sentence(query: str, chunk_text: str):
    sentences = split_sentences(chunk_text)
    if not sentences:
        return None

    q_vec = embed_text(query)  # 기존 RAG embedding 함수 그대로 사용
    best_sent = None
    best_score = -1

    for sent in sentences:
        s_vec = embed_text(sent)
        sim = cosine_sim(q_vec, s_vec)
        if sim > best_score:
            best_score = sim
            best_sent = sent

    return best_sent

# ------------------------------
# 3) RAG 기반 답변 생성 함수 (문장 기반 근거추출 완전통합 버전)
# ------------------------------
def generate_response(doc_id: str, user_query: str) -> dict:
    """
    문서 단위(doc_id) 기반 RAG 검색 → 답변 생성 → state 업데이트
    """

    # 1) RAG 검색 실행
    retrieved_items = search_rag(doc_id=doc_id, query=user_query)

    # 검색 결과 없으면
    if not retrieved_items:
        answer = "문서에 해당 내용이 없습니다.\n더 많은 정보는 문서 출처에 문의해주세요."

        state["present_answer"] = answer
        state["history"].append({"question": user_query, "answer": answer})

        return {
            "answer": answer,
            "source": None,
            "state": state
        }

    # 🔥 1-1) 출처용 후보 = page 텍스트만 필터링 (action 제외)
    page_items = [item for item in retrieved_items if item.get("type") == "page"]

    # 만약 page가 검색 안 됐다면 fallback (현실적으로 거의 없음)
    if not page_items:
        page_items = retrieved_items


    # 2) db_find: LLM에게 보여줄 전체 텍스트 (그대로 유지)
    db_find = "\n".join([
        f"- ({item.get('type','unknown')}) {item.get('text','')}"
        for item in retrieved_items
    ])

    # 3) 이전 대화 history 반영
    history_text = "\n".join([
        f"Q: {h['question']}\nA: {h['answer']}"
        for h in state["history"]
    ])

    # 4) LLM Prompt 구성
    prompt = f"""
    당신은 문서 기반 정확한 답변만 제공하는 안전 챗봇입니다.
    반드시 아래 문서 내용과 이전 대화 흐름을 함께 고려하여 답변하세요.
    부드럽고 다정한 말투로 답변하세요.

    [문서 ID]
    {doc_id}

    [이전 대화 요약]
    {state["summary"]}

    [최근 대화 기록]
    {history_text}

    [문서에서 찾은 근거 내용]
    {db_find}

    [사용자 질문]
    {user_query}

    응답 규칙:
    - 문서에 기반하지 않은 내용은 말하지 말 것
    - 허위 정보 금지
    - 첫문장과 마지막 문장을 제외한 정보를 제공하는 문장들은 bullet 또는 단계형으로만 답변 작성
    - 첫문장은 질문에 맞게 자연스럽게 시작할 것
    - 마지막문장은 "더 궁금하신 사항이 있으신가요?"로 끝낼것 
    - 각 항목은 줄바꿈(\n)으로 구분할 것
    - 한 줄에 하나의 bullet만 포함할 것
    - 문장은 절대로 붙여쓰지 말 것
    """

    # 5) LLM 호출
    answer = call_llm_chat(prompt).strip()


    # =====================================================
    # 6) 🔥 문서 출처 문장 기반 추출 (action 제외)
    # =====================================================
    best_sentences = []

    for item in page_items:     # 🔥 refined_txt에서만 뽑는다
        page_text = item.get("text", "")
        best_sentence = find_best_sentence(user_query, page_text)

        if best_sentence:
            best_sentences.append(f"- {best_sentence}")

    # fallback: 검색된 page 중 첫 번째
    if not best_sentences:
        fallback = page_items[0].get("text", "")
        best_sentences.append(f"- {fallback}")

    real_source = "\n".join(best_sentences)


    # =====================================================
    # 7) state 업데이트
    # =====================================================
    state["present_answer"] = answer
    state["history"].append({"question": user_query, "answer": answer})

    # 8) state history 크기 제한
    if len(state["history"]) > 3:
        old_data = state["history"][:-3]
        state["history"] = state["history"][-3:]
        state["summary"] = summarize_history(old_data, state["summary"])

    return {
        "answer": answer,
        "source": real_source,
        "state": state
    }
# # ------------------------------
# # 3) RAG 기반 답변 생성 함수 (이진아 수정 : doc_id 기반)
# # ------------------------------
# def generate_response(doc_id: str, user_query: str) -> dict:
#     """
#     문서 단위(doc_id) 기반 RAG 검색 → 답변 생성 → state 업데이트
#     """

#     # 1) 벡터 검색 (doc_id 기준 필터 적용)
#     retrieved_items = search_rag(doc_id=doc_id, query=user_query)

#     # 검색 결과가 없을 때
#     if not retrieved_items:
#         answer = "문서에 해당 내용이 없습니다.\n더 많은 정보는 문서 출처에 문의해주세요."

#         state["present_answer"] = answer
#         state["history"].append({"question": user_query, "answer": answer})
#         return {
#             "answer": answer,
#             "source": None,
#             "state": state
#         }

#     # 2) db_find: 전체 검색 결과 조합 (LLM용, 그대로 유지)
#     db_find = "\n".join([
#         f"- ({item.get('type','unknown')}) {item.get('text','')}"
#         for item in retrieved_items
#     ])


#     # 3) 기존 history 반영
#     history_text = "\n".join([
#         f"Q: {h['question']}\nA: {h['answer']}"
#         for h in state["history"]
#     ])

#     # 4) 프롬프트 생성
#     prompt = f"""
#     당신은 문서 기반 정확한 답변만 제공하는 안전 챗봇입니다.
#     반드시 아래 문서 내용과 이전 대화 흐름을 함께 고려하여 답변하세요.
#     부드럽고 다정한 말투로 답변하세요.

#     [문서 ID]
#     {doc_id}

#     [이전 대화 요약]
#     {state["summary"]}

#     [최근 대화 기록]
#     {history_text}

#     [문서에서 찾은 근거 내용]
#     {db_find}

#     [사용자 질문]
#     {user_query}

#     응답 규칙:
#     - 문서에 기반하지 않은 내용은 말하지 말 것
#     - 허위 정보 금지
#     - 첫문장과 마지막 문장을 제외한 정보를 제공하는 문장들은 bullet 또는 단계형으로만 답변 작성
#     - 첫문장은 질문에 맞게 자연스럽게 시작할 것
#     - 마지막문장은 "더 궁금하신 사항이 있으신가요?"로 끝낼것 
#     - 각 항목은 줄바꿈(\n)으로 구분할 것
#     - 한 줄에 하나의 bullet만 포함할 것
#     - 문장은 절대로 붙여쓰지 말 것
#     - 아래 예시 형식을 반드시 따를 것:

#     예시 형식:
#     첫 번째 항목
#     - 두 번째 항목
#     - 세 번째 항목
#     더 궁금하신 사항이 있으신가요?
#     """

#     # 5) LLM 호출
#     answer = call_llm_chat(prompt).strip()
    
#     # 실제 사용된 문장만 근거로 추출
#     # --------------------------
#     used_sources = []

#     for item in retrieved_items:
#         text = item.get("text", "")
#         # 문장을 40~80 글자 단위로 나눠서 매칭 정확도 UP
#         key = text[:60]

#         if key in answer:   # 답변 본문에 포함되는 경우만 근거로 인정
#             used_sources.append(
#                 f"- ({item.get('type','unknown')}) {text}"
#             )

#     # 아무 매칭 안되면 가장 상위 1개만 fallback
#     if not used_sources:
#         top = retrieved_items[0]
#         used_sources.append(
#             f"- ({top.get('type','unknown')}) {top.get('text','')}"
#         )

#     real_source = "\n".join(used_sources)

#     # 6) state 업데이트
#     state["present_answer"] = answer
#     state["history"].append({"question": user_query, "answer": answer})

#     # 7) state 크기 관리
#     if len(state["history"]) > 3:
#         old_data = state["history"][:-3]
#         state["history"] = state["history"][-3:]
#         state["summary"] = summarize_history(old_data, state["summary"])

#     return {
#         "answer": answer,
#         "source":real_source,
#         "state": state
#     }



# 테스트 실행
# if __name__ == "__main__":
#     print("RAG 챗봇 테스트 시작\n")

#     # 테스트용 doc_id (원하는 걸로 바꿔도 됨)
#     TEST_DOC_ID = "test-doc-1234"

#     while True:
#         user_q = input("\n사용자 질문: ")

#         if user_q.lower() in ["exit", "quit", "종료"]:
#             print("\n종료합니다.")
#             break

#         # generate_response(doc_id, user_query)
#         result = generate_response(TEST_DOC_ID, user_q)

#         print("\n챗봇 답변:")
#         print(result["answer"])

#         print("\n근거(REAL SOURCE):")
#         print(result["source"])   # real_source 들어있음

#         print("\n-------------------------------------")



