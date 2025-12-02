# test_node_result_packager_gpt2.py
from __future__ import annotations

import copy
from typing import Dict, Any
from src.utils.config import load_api_keys
from openai import OpenAI
from src.result.node_action_extractor import node_action_extractor

# 요약용 LLM
def call_llm(prompt: str) -> str:
    API_KEY = load_api_keys()
    client = OpenAI(api_key=API_KEY)  
    """
    OpenAI API(Responses)를 이용해 prompt를 처리하고 결과 반환.
    - prompt: 한국어 지시가 포함된 문자열
    - 반환: 모델이 생성한 문자열
    """
    resp = client.responses.create(
        model="gpt-4o-mini",
        input=[
            {
                "role": "system",
                "content": (
                    "당신은 한국어 공공문서 요약 및 안내문 재작성 어시스턴트입니다. "
                    "사용자의 지시를 따라 요약 또는 자연어 설명을 생성하되, "
                    "불필요한 설명은 붙이지 마세요."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.2,
    )

    # 1) output_text 사용
    if hasattr(resp, "output_text") and resp.output_text:
        return resp.output_text.strip()

    # 2) output(list) 처리
    if hasattr(resp, "output") and resp.output:
        texts = []
        for item in resp.output:
            if getattr(item, "type", "") == "output_text":
                if getattr(item, "text", None):
                    texts.append(item.text)

            if getattr(item, "content", None):
                for c in item.content:
                    if getattr(c, "text", None):
                        texts.append(c.text)

        if texts:
            return "\n".join(texts).strip()

    # 3) fallback
    return str(resp).strip()
    


# 요약 함수
def _summarizer(text: str) -> str:
    prompt = f"""
아래 문서의 핵심 내용을 5~8문장이내로 요약하라. 
문단이 아닌 리스트 형태로 문장 앞에 무조건 '-'을 이용하면서 요약하라.
제일 첫문장은 '-'을 이용하지 않고 "이 문서는 OO에 대한 문서입니다"와 같은 문장으로 문서의 주제를 먼저 말하고 요약하라.
핵심 정보(금액, 날짜, 기관명, 중요한 사유 등)를 포함하고 불필요한 배경설명이나 감상 없이 간결하게 요약하라.
문서에 나오지 않는 주관이 들어간 불필요한 표현들은 쓰지 말 것
**은행계좌(bank_account)의 경우 은행 명도 같이 표기할 것**
단, 은행계좌가 3개 이상인 경우, 대표로 2개만 노출하고 "나머지는 챗봇을 통해 문의해주세요"와 같이 쓸 것
중복되는 내용은 다 쓸 필요없이 한 번만 써라.

문서:
{text}

반드시 한국어 문장형 요약만 출력하고 JSON을 포함하지 말 것.
"""
    return call_llm(prompt)

# 행동 추출 및 요약 패키저
def node_result_packager(state: Dict[str, Any]) -> Dict[str, Any]:
    print("\n[Node] node_result_packager 실행")
    state = copy.deepcopy(state)

    is_obligation = state.get("doc_type", {}).get("행동지시", False)

    if is_obligation:
        print("행동지시 있음 -> node_action_extractor 실행")
        action_state = node_action_extractor(state)
        state["needs_action"] = action_state.get("needs_action")
        state["action_info"] = action_state.get("action_info")
    else:
        print("행동지시 없음 -> 행동 추출 스킵")
        state["needs_action"] = False
        state["action_info"] = None

    summary = _summarizer(state.get("refined_txt", ""))
    state["summary"] = summary

    db_packaged = {
        "summary": state["summary"],
        "needs_action": state["needs_action"],
        "action_info": state["action_info"],
    }
    state['db_package'] = db_packaged

    print("\n[Node] summary 완료")
    return state



# 행동지시 자연어 안내 변환
def format_action_instructions(action_list):
    """
    행동지시(action_info)를 부드러운 자연어로 재작성하고
    각 행동을 리스트 형태로 저장하도록 변환한다.
    """

    results = []

    for item in action_list or []:
        title = item.get("action", "")
        who = item.get("who", "")
        when = item.get("when", "")
        how = item.get("how", "")
        where = item.get("where", "")

        prompt = f"""
아래 정보를 기반으로 자연스럽고 가독성 좋게 여러 문장으로 행동 설명 문장을 만들어줘.
- title은 단 한 번만 출력할 것.
- "제목:" 같은 라벨은 절대 생성하지 말 것.
- 설명 문장 안에 title을 반복해서 쓰지 말 것.
- title은 반드시 **명사구로만** 작성해야 함.
- title은 절대 "~하다", "~하기", "~하는 것" 등 동사/동명사로 끝나면 안 됨.
- title은 반드시 **구체적**이고 명확해야 함.
  예: “세금 납부”처럼 추상적 표현 금지.  
      “주민세 납부”, “재산세 납부”처럼 실제 항목에 맞게 구체적으로 작성할 것.
- title이 여러 개일 경우 **서로 완전히 동일하거나 동일 의미를 갖는 표현을 금지함.**
  즉, 각 title은 개별 항목을 정확히 구분할 수 있도록 차별화된 명사구여야 함.

- 말투는 부드럽게
- 명령조가 아닌 지시하고 안내하는 방식으로 쓸 것. 예를 들어, "~OO하세요"와 같은 화법으로 쓸것
- 문장이 너무 길면 2~3문장으로 나눠줘
- 불필요한 형식적 문구는 빼줘
- 결과는 문장만 반환 (•, -, 리스트 문법 없이)
- 담당 기관이 뒷부분과 동일하면 앞부분에서 한 번만 안내할 것
- 행위를 위해 가야하는 곳이 아니라면 where은 생략할 것.
- **은행계좌(bank_account)의 경우 은행 명도 같이 표기할 것**  
- 단, 은행계좌가 3개 이상인 경우, 대표로 2개만 노출하고 "더 많은 계좌번호는 챗봇을 통해 문의해주세요"와 같이 쓸 것


[행동명(title)] : "text"에서는 절대 반복 금지.
"{title}"

[요소 정보]
- 대상: {who}
- 시점/기한: {when}
- 수행 방법: {how}
- 기관/장소: {where}
"""

        natural_text = call_llm(prompt).strip()
        # natural_text가 여러 줄일 수 있으므로 줄 단위로 split
        lines = natural_text.split("\n")

        # 첫 번째 줄이 title과 완전히 동일하거나 공백 포함 동일하면 제거
        if lines and lines[0].strip() == title.strip():
            lines = lines[1:]  # 첫 줄 제거

        # 다시 문장으로 합침
        natural_text = "\n".join(lines).lstrip()

        results.append({
            "title": title,
            "text": natural_text,
        })

    return results