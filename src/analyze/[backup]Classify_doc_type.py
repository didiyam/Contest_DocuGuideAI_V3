from __future__ import annotations

from typing import Any, Dict, List
import json
from openai import OpenAI


def Classify_doc_type(state: Dict[str, Any]) -> Dict[str, Any]:
        
    """
    state["refined_text"]를 기반으로 공공문서 유형과 의무 여부를 판단해
    state["doc_type"]에 저장하는 노드.

    출력 형식:
        state["doc_type"] = {
            "문서유형": "법규문서" | "지시문서" | "공고문서" | "비치문서" | "일반문서",
            "행동지시": True | False
        }
    """

    refined_list: List[str] = state.get("refined_txt", [])
    if not refined_list:
        # refined_text가 비어 있으면 기본값 세팅 후 리턴
        state["doc_type"] = {"문서유형": "빈문서", "행동지시": False}
        return state

    # 여러 조각을 하나의 텍스트로 합침
    doc_text = "\n".join(refined_list)

    # 너무 긴 문서는 앞부분만 사용 (길이는 필요에 따라 조정)
    max_chars = 15000
    if len(doc_text) > max_chars:
        doc_text = doc_text[:max_chars] + "\n\n[이후 내용 생략]"

    system_prompt = """
당신은 대한민국 공공문서 분류 전문가입니다.

당신의 임무는 주어진 공공문서 텍스트를 읽고 다음 두 가지를 판단하는 것입니다.

1. 문서유형 (다음 다섯 가지 중 정확히 하나만 선택)
- 법규문서: 헌법, 법률, 조례, 규칙 등 법규를 제정하거나 개정하는 문서입니다. 조문 형식으로 작성됩니다.
- 지시문서: 상급 기관이 하급 기관이나 소속 공무원에게 업무를 지시하기 위해 작성하는 문서로, 훈령, 지시, 예규 등이 있습니다.
- 공고문서: 행정기관이 일반 대중에게 특정 사항을 알리기 위해 작성하는 문서입니다. 고시와 공고가 해당하며, 고시는 효력이 지속되는 경우가 많고, 공고는 단기적·일시적인 효력을 가집니다.
- 비치문서: 일정한 사항을 기록하여 비치하고 업무에 활용하는 문서입니다. 비치대장이나 비치카드가 이에 해당합니다.
- 일반문서: 내부 업무 연락, 홍보, 보고 등을 위해 작성하는 문서입니다. 회보, 보고서 등이 일반문서에 속합니다.

2. 행동지시 여부(orderTF)
- 문서가 수취인(국민, 기업, 다른 기관 등)에게 구체적인 행위를 요구하면 true
  (예: 세금 납부, 신고서 제출, 신청서 제출, 법원 출석, 보고서 제출, 시정 조치 이행 등)
- 단순한 안내, 홍보, 설명, 결과 통보만 하는 경우에는 false

반드시 아래 JSON 형식 '하나만' 출력하세요.

{
  "문서유형": "법규문서 또는 지시문서 또는 공고문서 또는 비치문서 또는 일반문서",
  "행동지시": true 또는 false
}

중요:
- JSON 이외의 텍스트(설명, 문장, 주석 등)를 절대 출력하지 마세요.
- 코드 블록(````json` 등)도 사용하지 마세요.
""".strip()

    client = OpenAI()

    response = client.responses.create(
        model="gpt-4o-mini",
        input=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": (
                    "다음은 한 개의 공공문서 전체 내용입니다. "
                    "위 규칙에 따라 문서유형과 의무 여부를 판단해 주세요.\n\n"
                    f"{doc_text}"
                ),
            },
        ],
        # response_format 인자는 제거 (현재 환경에서 지원 X)
        max_output_tokens=210,#임시
    )

    # 다양한 버전에 대응해서 출력 텍스트를 뽑는 방어 코드
    raw_output = None
    try:
        # 최신 responses API 구조
        raw_output = response.output[0].content[0].text
    except Exception:
        try:
            # 혹시 텍스트 전체가 한 필드에 있는 경우
            raw_output = getattr(response, "text", None)
        except Exception:
            pass

    if raw_output is None:
        # 그래도 못 뽑았으면 그냥 문자열로 캐스팅
        raw_output = str(response)

    # JSON 파싱
    try:
        result = json.loads(raw_output)
    except Exception:
        result = {}

    allowed_types = {"법규문서", "지시문서", "공고문서", "비치문서", "일반문서"}
    doc_type = result.get("문서유형", "일반문서")
    if doc_type not in allowed_types:
        doc_type = "일반문서"

    orderTF = bool(result.get("행동지시", False))

    state["doc_type"] = {
        "문서유형": doc_type,
        "행동지시": orderTF,
    }

    return state
