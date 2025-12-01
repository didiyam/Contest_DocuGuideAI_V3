from typing import Dict, Any
from src.result.C_node_action_extractor import node_action_extractor
from src.result.C_node_action_extractor import call_llm   # LLM 호출 모듈
import copy


def _summarizer(text: str) -> str:
    """
    문서 전체 핵심 요약 생성 (5~8문장)
    외부에서 import되지 않고 이 파일 내부에서만 사용되는 기능.
    """
    prompt = f"""
아래 문서의 핵심 내용을 5~8문장으로 요약하라.
문단이 아닌 리스트 형태로 문장앞에 무조건 -을 이용하면서 요약하라.
핵심 정보(금액, 날짜, 기관명, 중요한 사유 등)를 포함하고 불필요한 배경설명이나 감상 없이 간결하게 요약하라.
중복되는 내용은 다 쓸 필요없이 한번만 써라.

문서:
{text}

반드시 한국어 문장형 요약만 출력하고 리스트나 JSON을 포함하지 말 것.
"""
    response = call_llm(prompt)
    return response.strip()


def node_result_packager(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    문서 핵심 요약 + 행동 정보 패키징 노드
    행동지시 여부에 따라 action_extractor 실행 여부만 다르고
    summarizer는 항상 실행됨.
    """

    print("\n[Node] node_result_packager 실행")

    # state 수정 전에 deep copy
    state = copy.deepcopy(state)

    # 행동 지시 여부 확인
    is_obligation = state.get("doc_type", {}).get("행동지시", False)

    # 행동지시가 있는 경우에만 action_extractor 호출
    if is_obligation:
        print("행동지시 있음 → node_action_extractor 실행")
        action_state = node_action_extractor(state)
        state["needs_action"] = action_state["needs_action"]
        state["action_info"] = action_state["action_info"]
    else:
        print("행동지시 없음 → 행동 추출 스킵")
        state["needs_action"] = False
        state["action_info"] = None

    # summarizer 항상 실행
    summary = _summarizer(state.get("refined_text", ""))
    state["summary"] = summary

    # 최종 출력 형태
    packaged = {
        "summary": state["summary"],
        "needs_action": state["needs_action"],
        "action_info": state["action_info"]
    }

    print("\n[Node] 1차 결과 패키징 완료")
    return packaged


def format_action_instructions(action_list):
    """
    행동지시(action_info)를 부드러운 자연어로 재작성하고
    각 행동을 리스트 형태로 저장하도록 변환한다.
    """

    results = []

    for item in action_list:
        title = item.get("action", "")
        who = item.get("who", "")
        when = item.get("when", "")
        how = item.get("how", "")
        where = item.get("where", "")

        prompt = f"""
아래 정보를 기반으로 자연스럽고 가독성 좋게 여러 문장으로 행동 설명 문장을 만들어줘.
- 말투는 부드럽게
- 너무 명령조(X) → 제안, 안내 형식(O)
- 문장이 너무 길면 2~3문장으로 나눠줘
- 불필요한 형식적 문구는 빼줘
- 결과는 문장만 반환 (•, -, 리스트 문법 없이)
- 담당 기관이 뒷부분과 동일하면 앞부분에서 한번만 안내할 것

[제목]
{title}

[대상]
{who}

[언제]
{when}

[방법]
{how}

[장소 또는 담당 기관]
{where}
"""

        # GPT 호출 함수 사용
        natural_text = call_llm(prompt).strip()

        # 리스트 형태로 저장
        results.append({
            "title": title,
            "text": natural_text
        })

    return results