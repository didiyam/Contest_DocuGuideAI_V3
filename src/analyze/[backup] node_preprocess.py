
from __future__ import annotations
from typing import Dict, Any, List, Optional

from openai import OpenAI

from ..utils.text_utils import clean_text

def normalize_text(text: str) -> str:
    """
    LLM 기반 공공문서 텍스트 정규화 함수.

    - 의미는 최대한 유지하면서
      * 이상한 공백 / 줄바꿈 / 특수 문자 정리
      * 기본적인 맞춤법 / 띄어쓰기 보정
      * 반복되는 잡음/노이즈 문구 최소화
    - 요약하거나 내용을 삭제하는 게 목적이 아니라
      "읽기 좋게, 깨끗하게" 만드는 것이 목적이다.
    """

    if not text:
        return ""

    # 여기서 import / client 생성까지 전부 함수 내부에서 처리
    # (파일 상단 import 안 건드리려고 이렇게 구성)
    from openai import OpenAI

    client = OpenAI()

    system_prompt = """
당신은 공공문서 전처리(클리닝/정규화) 전문가입니다.

[목표]
- 문서의 핵심 내용과 의미는 유지합니다.
- 대신 다음과 같은 "노이즈"를 최대한 제거/정리합니다.

[해야 할 일]
1) 잘못된 띄어쓰기, 기본적인 맞춤법을 자연스럽게 수정합니다.
2) 의미 없는 공백/줄바꿈/탭/중복 공백을 정리합니다.
3) 깨진 문자, 이상한 기호(예: ▒, ░, ■, ◆ 등)가 문맥에 필요 없으면 제거합니다.
4) 따옴표/대시/괄호 등은 일반적인 기호로 통일합니다.
5) 페이지 번호, 머리글/바닥글처럼
   "1 / 12", "- 3 -", "페이지 3 / 10" 등
   문서 내용과 상관없는 표시는 제거해도 좋습니다.
6) 완전히 같은 문구가 여러 번 반복되는 광고성/푸터 문구는 한 번만 남기거나 제거해도 됩니다.

**CRITICAL RULES**
- **문서를 요약하지 마세요.**
- 문장의 의미를 바꾸지 마세요.
- 중요한 문장이나 항목을 임의로 삭제하지 마세요.
- 새로운 정보를 추가하지 마세요.

출력 형식:
- 정리된 텍스트만 그대로 출력하세요.
- 설명, 주석, 따옴표 등은 붙이지 마세요.
"""

    try:
        resp = client.responses.create(
            model="gpt-4o-mini",  # 필요하면 다른 모델명으로 교체 가능
            input=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": f"<TEXT>\n{text}\n</TEXT>",
                    
                },
            ], max_output_tokens=210 #추후 삭제
        )

        # responses API 기준 파싱
        # (output[0].content[0].text 에 결과 문자열이 들어있다고 가정)
        refined = resp.output[0].content[0].text
        return refined.strip()

    except Exception as e:
        # LLM 호출에 실패하면, 원문을 그대로 돌려주거나
        # 최소한의 fallback 처리를 할 수 있다.
        # 여기서는 안전하게 원문 그대로 반환.
        # (원하면 print(e)나 logger로 남겨도 됨)
        return text

def node_preprocess(state: Dict[Any]) -> Dict[Any]:
    import os   
    
    key_tail = os.environ.get("OPENAI_API_KEY", "")[:60]
    print(f"[DEBUG] node_classify OPENAI_API_KEY last4 = {key_tail}")
    """
    state["raw_text"]만 사용해서 전처리 후
    state["refined_text"]에 저장하는 노드.
    """

    raw_text = state.get("raw_txt")
    if raw_text is None : refined = []
    else :     refined = []

    for i in raw_text : 
    # 1차: 공백/개행 정리 등 기본 클리닝
        cleaned = clean_text(i)

    # 2차: normalize_text로 정규화 (유니코드/기호/줄바꿈 등)
        result = normalize_text(cleaned)
        refined.append(result)

    state["refined_txt"] = refined
    return state