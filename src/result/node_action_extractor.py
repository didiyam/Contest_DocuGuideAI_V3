from __future__ import annotations

import json
import re
from typing import Dict, Any
from openai import OpenAI
from src.utils.config import load_api_keys


# 1) call_llm 강제 JSON-only 버전
def call_llm_json(prompt: str) -> str:
    API_KEY = load_api_keys()
    client = OpenAI(api_key=API_KEY)

    system_prompt = """
    당신은 공공문서에서 행동 정보를 JSON으로 추출하는 전문가입니다. 
    ⚠ 절대 JSON 외의 어떤 텍스트도 출력하지 마십시오.
    ⚠ 코드블록(````), 설명문, 자연어 문장, 머리말, 꼬리말 금지.
    ⚠ 오직 JSON 하나만 출력하세요.
    """

    resp = client.responses.create(
        model="gpt-4o-mini",
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        temperature=0,
    )

    text = resp.output[0].content[0].text.strip()
    return text


# JSON 자동 복구 
def repair_json(text: str) -> str:
    # 코드블록 제거
    text = re.sub(r"```.*?```", "", text, flags=re.S)

    # 앞뒤의 JSON 이외 텍스트 제거
    # JSON 배열 또는 객체 시작 찾기
    match_start = re.search(r"[\[{]", text)
    match_end = re.search(r"[\]}]\s*$", text, re.S)

    if match_start and match_end:
        text = text[match_start.start(): match_end.end()]

    # 잘못된 따옴표 수정
    text = text.replace("'", '"')
    return text.strip()


# 2) node_action_extractor
def node_action_extractor(state: Dict[str, Any]) -> Dict[str, Any]:
    print("\n[Node] node_action_extractor 실행")

    is_obligation = state.get("doc_type", {}).get("행동지시", False)
    text = state.get("refined_txt", "")
    ner_result = state.get("ner_result")

    if not is_obligation:
        print("행동지시 없음 -> 사용자 행동 정보 추출 생략")
        state["needs_action"] = False
        state["action_info"] = []
        return state

    # action_info 추출
    action_prompt = f"""
    다음 문서 내용을 기반으로 사용자가 실제로 수행해야 할 행동 정보를 추출하라.
    문서에는 일부 정보가 명시되어 있지 않을 수 있으므로, 가능한 경우 문서의 내용과 엔티티를 참고하여 
    "action", "who", "when", "how", "where"를 최대한 추론하라.

    금액, 날짜, 기관명, 환급 항목, 행동 방법 등은 표 안에 있더라도 참고해서 필요한 필드를 채워라.
    최대한 구체적으로 필드를 채워라.

    action(행동명)은 반드시 **구체적인 명사구**로 작성한다.
     - "납부", "신청" 같은 단일 동사 금지.
     - 예: "재산세 납부", "지방세 고지서 확인 및 전자납부", "ETAX 시스템 온라인 신청", "관악구 복지정책과 전화 신청"
    action에 문서 내 세금명 / 제도명 / 제출서류명 / 기관명 정보를 가능한 한  반영한다.
    
    action은 서로 완전히 다른 항목이어야 한다.
   - 의미가 같은 것이면 하나로 통합
   - 중복되는 “신청”, “문의”, “납부” 생성 금지.
   
   행동이 여러 개라면 배열 형태로 모두 반환하라.

    **은행계좌(bank_account)**의 경우 은행 명도 같이 표기할 것.

    필드 의미:
    - action: 사용자가 실제로 수행해야 할 행동 (동사 중심)
    - who: 행동 주체 (국민, 근로자, 신청자 등)
    - when: 기한 또는 시점
    - how: 수행 방법(방문/온라인/서류제출/전화 등)
    - where: 기관명, 지사, 콜센터 등

    -----------------------------------------
    ⚠ 아래 규칙을 반드시 지켜라:
    - 오직 JSON 하나만 출력한다.
    - 자연어 설명, 코드블록(````), 머리말/아무 말도 출력하지 않는다.
    - JSON object 하나만 포함해야 하며, 그 외 텍스트 금지.
    -----------------------------------------

    문서 내용:
    {text}

    NER 엔티티:
    {ner_result}

    반환 JSON 형식:

    {{
    "needs_action": true,
    "action_info": [
        {{
        "action": "",
        "who": "",
        "when": "",
        "how": "",
        "where": ""
        }}
    ]
    }}
    """

    raw = call_llm_json(action_prompt)

    # 2) JSON 자동 복구 + 파싱
    try:
        parsed = json.loads(raw)
    except Exception:
        print("[경고] JSON 파싱 실패 -> JSON 복구 시도")

        repaired = repair_json(raw)

        try:
            parsed = json.loads(repaired)
        except Exception:
            print("[문제 발생] JSON 복구 실패 -> fallback 반환")
            parsed = {"needs_action": True, "action_info": []}

    # 3) state 업데이트
    state["needs_action"] = parsed.get("needs_action", True)
    state["action_info"] = parsed.get("action_info", [])

    return state