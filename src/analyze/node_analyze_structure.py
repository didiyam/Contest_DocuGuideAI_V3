# src/analyze/node_analyzer.py
# --------------------------------------------------------------
# 문서 구조 분석(요약 정리) 노드
#
# 역할:
#   - 전처리된 텍스트(문자열/문자열 리스트)만을 입력으로 받아,
#     "표 / 문단 / 섹션" 관점에서 문서 구조를 LLM으로 분석·요약한다.
#
# 전제:
#   - doc_type 은 *다른 노드*에서 state["doc_type"]에 세팅해준다.
#     이 노드는 doc_type 을 "추론하지 않고" 단지 사용만 한다.
#   - tables 는 별도로 받지 않는다.
#     LLM이 텍스트 안의 표/목록/열 구조를 스스로 추론해서 설명하도록 한다.
#
# 입력 state (예시):
#   - texts:
#       * "문자열" 또는 ["문자열", ...] 또는 [["문자열", ...], ...]
#       * 페이지/블록 단위 등은 전처리 노드 설계에 따라 자유
#   - doc_type: str (선택)
#       * 예: "지방세 환급 안내문", "상생페이백 공고문" 등
#
# 출력 state:
#   - structure_summary: str
#       * 문서 개요, 섹션 구조, 표/목록 구조, 구조적 특징 등을 정리한 요약
# --------------------------------------------------------------

from __future__ import annotations

from typing import Any, Dict, List
from src.utils.config import load_api_keys



def node_analyze_structure(state: Dict[str, Any]) -> Dict[str, Any]:
    from openai import OpenAI
    API_KEY = load_api_keys()
    client = OpenAI(api_key=API_KEY)
    """
    문서 구조를 요약/정리하는 단일 노드.

    - 입력: state["texts"], state["doc_type"](선택)
    - 처리: LLM을 사용해 표/문단/섹션 관점에서 문서 구조를 분석
    - 출력: state["structure_summary"] 에 구조 요약 텍스트 저장
    """

    texts = state.get("texts", [])
    doc_type = state.get("doc_type")  # ← 다른 노드에서 미리 세팅 (여기서는 추론 X)

    # --- 1. texts → 사람이 읽을 수 있는 큰 문자열로 병합 ---
    page_texts: List[str] = []

    # texts 형태 허용:
    #   - "문자열"
    #   - ["문자열", ...]
    #   - [["문자열", ...], ...]
    if isinstance(texts, (str, bytes)):
        # 단일 문자열인 경우
        merged_text = str(texts)
    else:
        # 리스트 계열인 경우: 1단계/2단계 리스트를 모두 허용
        for idx, t in enumerate(texts):
            if isinstance(t, list):
                joined = "\n".join(str(x) for x in t if x)
            else:
                joined = str(t) if t is not None else ""

            joined = joined.strip()
            if not joined:
                continue

            # 페이지/블록 구분용 태그 (필요 없으면 나중에 제거해도 됨)
            page_texts.append(f"[블록 {idx + 1}]\n{joined}")

        merged_text = "\n\n".join(page_texts)

    if not merged_text or not merged_text.strip():
        state["structure_summary"] = "문서에서 유의미한 텍스트를 찾지 못했습니다."
        return state

    # --- 2. LLM 프롬프트 구성 ---
    system_msg = """
당신은 공공문서를 분석하는 문서 구조 전문가입니다.

당신의 역할은:
1) 전처리된 텍스트만을 보고, 문서 전체의 구조를 "표, 문단, 섹션" 관점에서 분석하고,
2) 사람이 한눈에 이해할 수 있도록 요약 정리하는 것입니다.

주의사항:
- 텍스트 외에 별도의 표 데이터는 주어지지 않습니다.
- 따라서 텍스트 안에서 표/목록/열 구조로 보이는 부분을 스스로 찾아서,
  그것들이 어떤 정보를 담고 있는지, 문단과 어떻게 연결되는지 설명해야 합니다.
- 문서의 의미나 내용을 임의로 바꾸지 말고, 원문의 항목/번호 체계를 가능한 한 존중하세요
  (예: Ⅰ, Ⅱ, Ⅲ / 1., 2., 3. / (1), (2) 등).
- 너무 장황하게 길게 쓰기보다는, 구조 중심으로 핵심만 정리하세요.
"""

    doc_type_line = f"문서 유형: {doc_type}\n" if doc_type else ""

    user_prompt = f"""
{doc_type_line}
아래는 전처리된 문서 본문 텍스트입니다.

[문서 본문 시작]
{merged_text}
[문서 본문 끝]

위 텍스트만을 바탕으로, 이 문서의 구조를
'표, 문단, 섹션' 관점에서 분석하여 한국어로 정리해 주세요.

반드시 아래 형식을 따라 주세요:

1. 문서 개요
   - (문서의 목적, 대상, 전체적인 흐름)

2. 섹션 구조 요약
   - (섹션 번호/제목/대략적인 범위와 함께, 각 섹션이 어떤 내용을 다루는지 2~3줄로 정리)

3. 표/목록 구조 요약
   - (텍스트 안에 나타나는 표 형식/목록 형식의 부분이 어떤 정보를 다루는지,
      그리고 주변 문단과 어떻게 연결되는지 간단히 설명)

4. 문서 구조적 특징
   - (예: 붙임/부록 구성, 자주 나오는 패턴, 구조적으로 주의 깊게 봐야 할 부분 등)
"""

    # --- 3. LLM 호출 ---
    response = client.responses.create(
        model="gpt-4o-mini",  # 프로젝트에서 사용하는 기본 모델로 교체 가능
        input=[
            {"role": "system", "content": system_msg.strip()},
            {"role": "user", "content": user_prompt.strip()},
        ],
        max_output_tokens=1200,
    )

    try:
        summary_text = response.output[0].content[0].text
    except Exception:
        # 혹시 응답 구조가 바뀌어도 최소한 문자열로 fallback
        summary_text = str(response)

    state["structure_summary"] = summary_text.strip()

    return state
