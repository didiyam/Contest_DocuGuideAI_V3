# test_node_result_packager_gpt2.py
from __future__ import annotations

import copy
from typing import Dict, Any
from src.utils.config import load_api_keys
from openai import OpenAI
from src.result.node_action_extractor import node_action_extractor
API_KEY = load_api_keys()
client = OpenAI(api_key=API_KEY)

# 요약용 LLM
def call_llm_summary(prompt: str) -> str:
    API_KEY = load_api_keys()
    client = OpenAI(api_key=API_KEY)

    resp = client.responses.create(
        model="gpt-4o-mini",
        input=[
            {"role": "system", "content": "당신은 공공문서를 간결하고 가독성 좋게 요약하는 한국어 요약 전문가입니다."},
            {"role": "user", "content": prompt},
        ],
    )

    # 안전하게 parse
    try:
        output = resp.output
        if not output:
            return "[실패] 요약 생성에 실패했습니다."

        content = output[0].content
        if not content:
            return "[실패] 요약 생성에 실패했습니다."

        if not hasattr(content[0], "text"):
            return "[실패] 요약 생성에 실패했습니다."

        return content[0].text.strip()

    except Exception as e:
        print("[LLM SUMMARY ERROR]", e)
        return "[오류] 요약 생성 중 오류가 발생했습니다."


# 행동 안내용 LLM
def call_llm(prompt: str) -> str:
    API_KEY = load_api_keys()
    client = OpenAI(api_key=API_KEY)
    """
    OpenAI API(Responses)를 이용해 prompt를 처리하고 결과 반환.
    - prompt: 한국어 지시가 포함된 문자열
    - 반환: 모델이 생성한 문자열
    """
    resp = client.responses.create(
        model="gpt-5.1-chat-latest",
        input=[
            {
                "role": "system",
                "content": "당신은 사용자가 해야하는 공공문서의 행동지시를 부드럽고 자연스럽게 안내문으로 재작성하는 어시스턴트입니다."
                ,
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
    )
    # 최신 Responses API의 표준 출력
    if hasattr(resp, "output_text") and resp.output_text:
        return resp.output_text.strip()

    # 일부 모델 : output이 리스트 형태
    if hasattr(resp, "output") and resp.output:
        parts = resp.output
        texts = []
        for p in parts:
            if p.type == "output_text":
                texts.append(p.text)
            elif hasattr(p, "content"):
                for c in p.content:
                    if hasattr(c, "text"):
                        texts.append(c.text)
        return "\n".join(texts).strip()
    return str(resp).strip()





# -------------------------
# _summarizer 
# -------------------------
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
    return call_llm_summary(prompt)


# node_result_packager
# -------------------------
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
# -------------------------
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
        아래 정보를 이용해 사용자가 해야 할 행동을 자연스럽게 설명하는 문장으로 만들어 주세요.
        출력 형식은 자연스러운 한국어 문장만 포함하며, 리스트 기호(•, -, 숫자 등)는 절대 사용하지 않습니다.

        [작성 규칙 — 반드시 모두 지킬 것]

        1) 문체 및 구성
        - 말투는 부드럽고 안내하듯이 작성하세요. (“~하세요” 형태 권장)
        - 문장이 너무 길면 2~3개의 짧은 문장으로 나누세요.
        - 불필요한 형식적 문구, 반복 표현, 장황한 설명은 넣지 않습니다.

        2) 제목(title) 관련 규칙
        - title은 결과 문단에서 **절대 반복해서 쓰지 않습니다.** (한 번도 쓰지 말 것)
        - “제목:”, “[제목]” 같은 라벨도 쓰지 않습니다.
        - title은 동사형(~하다, ~하기)으로 쓰지 않습니다. **반드시 명사구 형태**로만 사용하십시오.
        - 여러 행동이 있을 경우, 각 title은 서로 명확히 구분될 수 있도록 실제 행동명을 구체적으로 표현해야 합니다.  
        (예: “세금 납부” 금지 → “주민세 납부”, “재산세 납부”처럼 구체적 명칭)

        3) 정보 사용 규칙
        - where(장소/기관)이 '방문해야 하는 장소'가 아닌 단순 출처 정보라면 생략하세요.
        - 담당 기관이 문단 내에서 반복될 경우, 앞에서 한 번만 언급하고 이후에는 반복하지 마세요.
        - 은행계좌(bank_account)는 은행명 + 계좌번호 형식으로 표기합니다.
        - 계좌가 3개 이상일 경우, 대표 2개만 표기하고  
        “나머지 계좌는 챗봇을 통해 문의해주세요.”라고 안내하세요.

        4) 출력 형식
        - 출력은 title을 제외한 **행동 설명 문장만** 반환합니다.
        - 리스트, 헤더, 기호, JSON, 메타정보는 절대 사용하지 않습니다.
        - 문장 사이에는 한 줄 공백 없이 바로 이어서 작성합니다.

        [입력 정보]
        제목(title): {title}
        대상(who): {who}
        언제(when): {when}
        방법(how): {how}
        담당 기관 또는 장소(where): {where}

        위 규칙을 모두 지킨 행동 안내문을 자연스럽게 작성해 주세요.
        """

        natural_text = call_llm(prompt).strip()

        results.append({
            "title": title,
            "text": natural_text,
        })

    return results
