from __future__ import annotations

import json
from typing import Dict, Any

from openai import OpenAI

# 전역 클라이언트 (OPENAI_API_KEY는 환경변수에서 읽음)


# -------------------------------
# 1) call_llm 구현 (신버전 OpenAI)
# -------------------------------
def call_llm(prompt: str) -> str:
    client = OpenAI()       
    """
    OpenAI responses API를 이용해 prompt를 처리하고 결과 반환.
    - prompt: JSON만 출력하도록 안내된 한글 프롬프트 문자열
    - 반환: LLM이 생성한 문자열 (JSON 문자열 기대)
    """

    resp = client.responses.create(
        model="gpt-4o-mini",
        input=[
            {
                "role": "system",
                "content": "당신은 한국어 공공문서에서 행동 정보를 JSON 형식으로 추출하는 어시스턴트입니다. "
                           "항상 유효한 JSON만 출력해야 하며, 다른 설명 문장은 절대 포함하지 마세요.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0,
    )

    # responses API 구조에 맞게 텍스트 추출
    # (output[0].content[0].text 가 일반적인 위치)
    return resp.output[0].content[0].text.strip()


# -------------------------------
# 2) node_action_extractor 정의
# -------------------------------
def node_action_extractor(state: Dict[str, Any]) -> Dict[str, Any]:
    print("\n[Node] node_action_extractor 실행")

    # 문서 유형에서 행동지시 여부 확인
    is_obligation = state.get("doc_type", {}).get("행동지시", False)
    text = state.get("refined_txt", "")
    ner_result = state.get("ner_result")

    # 행동지시가 없는 문서인 경우
    if not is_obligation:
        print("행동지시 없음 → 사용자 행동 정보 추출 생략")
        state["needs_action"] = False
        state["action_info"] = None
        return state

    # LLM 프롬프트 구성
    prompt = f"""
다음 문서 내용을 기반으로 사용자가 실제로 수행해야 할 행동 정보를 추출하라.
문서에는 일부 정보가 명시되어 있지 않을 수 있으므로, 가능한 경우 문서의 내용과 엔티티를 참고하여 "action", "who", "when", "how", "where"를 최대한 추론하라.
금액, 날짜, 기관명, 환급 항목, 행동 방법 등은 표 안에 있더라도 참고해서 필요한 필드를 채워라.
최대한 구체적으로 필드를 채워라.
행동이 여러 개라면 배열 형태로 모두 반환하라.
**은행계좌(bank_account)의 경우 은행 명도 같이 표기할 것**
JSON만 출력하세요. 자연어 설명 절대 금지. 출력은 반드시 JSON object 하나만 포함해야 합니다.

문서 내용:
{text}

문서에서 발견되는 엔티티:
{ner_result}

반드시 아래 JSON 형식 준수:

{{
  "needs_action": true,
  "action_info": [
    {{
      "action": "무엇을 해야 하는가 (동사 중심)",
      "who": "누가 행동해야 하는가(문서의 주체, 수신자, 일반적으로 '국민' 혹은 '신청자')",
      "when": "언제까지 또는 시점 (문서에서 언급된 날짜, 또는 '즉시' 등 시간 정보)",
      "how": "어떤 방법으로 행동해서 해결해야하는가(행동 방법, 신청 방법, 온라인, 방문, 우편, FAX 등)",
      "where": "어디에서 문서를 보냈나(문서의 출처, 문서의 발신지 등)"
    }}
  ]
}}

모든 필드(action, who, when, how, where)를 가능한 한 채워라.
how는 어디서 어떻게 행동해야하는지 상세하게, 자세하게 추출하라.
추가 설명 문장 없이 JSON만 반환하라.
"""

    raw_response = call_llm(prompt)

    try:
        parsed = json.loads(raw_response)
    except Exception:
        print("[⚠ 경고] JSON 파싱 실패 → fallback 처리")
        parsed = {"needs_action": True, "action_info": []}

    # 기존 state 유지 + 필드만 추가/갱신
    state["needs_action"] = parsed.get("needs_action", True)
    state["action_info"] = parsed.get("action_info", [])

    return state
