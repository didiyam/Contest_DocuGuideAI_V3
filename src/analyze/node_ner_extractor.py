
# --------------------------------------------------------------
# 행정정보 NER 추출 노드 (gpt-4o-mini, 동적 key)
# + 공공문서 유형 및 의무 판단
#
# - 입력:
#     state["refined_txt"] :  List[str]
#       (전처리/정규화가 끝난 문서 텍스트)
# - 출력:
#     state["ner_result"]      : Dict (LLM이 설계한 동적 key 엔티티)
#     state["ner_result_raw"]  : str  (LLM 원문 출력)
#     state["ner_error"]       : str  (에러 메시지, 선택)
#
# 문서 형식 분류 (gpt-4o-mini, 동적 key)
# - 입력 : 
#     state["refined_txt"] :  List[str]
#       (전처리/정규화가 끝난 문서 텍스트)
# - 출력:
#     state["doc_type"]      : Dict (문서 형식, 행동지시여부 포함)
#
# --------------------------------------------------------------

from __future__ import annotations

from typing import Any, Dict, List, Union
import json
from openai import OpenAI
from src.utils.config import load_api_keys

def node_ner_extractor(state: Dict[str, Any]) -> Dict[str, Any]:

    print("[Node] Ner extractor start")

    state = Classify_doc_type(state)     #문서분류 함수 실행
    print("[Node] Ner extractor _ classify doc type finish")

    state = Ner_extractor(state)         #행정정보 ner 추출 함수 실행

    if "ner_error" in state:             #ner추출과정에서 에러 발생했을 시 출력
        print(state["ner_error"])

    print("[Node] Ner extractor end")

    return state
    
def Classify_doc_type(state: Dict[str, Any]) -> Dict[str, Any]:
        
    """
    state["refined_txt"]를 기반으로 공공문서 유형과 의무 여부를 판단해
    state["doc_type"]에 저장하는 노드.

    출력 형식:
        state["doc_type"] = {
            "문서유형": "법규문서" | "지시문서" | "공고문서" | "비치문서" | "일반문서",
            "행동지시": True | False
        }
    """

    refined_list: List[str] = state.get("refined_txt", [])
    if not refined_list:
        # refined_txt 비어 있으면 기본값 세팅 후 리턴
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

    
    API_KEY = load_api_keys()
    client = OpenAI(api_key=API_KEY)

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

def Ner_extractor(state: Dict[str, Any]) -> Dict[str, Any]:
    
    API_KEY = load_api_keys()
    client = OpenAI(api_key=API_KEY)
    
    NER_SYSTEM_PROMPT = """
    당신은 한국어 공공·행정 문서를 분석하는 NER(개체명 인식) 전문가입니다.

    당신의 임무는 주어진 문서를 분석하여,
    문서 유형과 다양한 행정정보 엔티티들을 추출하고,
    단일 JSON 객체로만 출력하는 것입니다.

    출력 JSON의 최상위 구조는 다음과 같습니다.

    {
    "doc_type": "...",
    "entities": {
        // 여기에 다양한 엔티티 타입들을 key로 두고,
        // 각 key마다 문자열 리스트를 값으로 둡니다.
    },
    "meta": {
        // 문서 분석에 유용한 메타 정보 (선택적)
    }
    }

    규칙:

    1) doc_type
    - 이 문서가 어떤 행정/공공 문서인지 한 문장으로 요약해서 적습니다.
    - 예: "지방세 환급 안내문", "지방세 고지서", "지원사업 공고문", "행정처분 통지서" 등.

    2) entities
    - key 이름은 당신이 문서를 보고 **직접 설계**합니다.
    - 예시 (참고용, 반드시 그대로 쓸 필요는 없음):
        - organization, department, contact, subject, project_name, tax_item,
        amount, refund_reason, due_date, application_period, legal_basis,
        address, website, bank_account, applicant, target, warnings 등
    - 각 엔티티 유형의 value는 **문자열 리스트**입니다.
    - 한 엔티티 값이 여러 번 등장하면 중복 없이 한 번만 넣으세요.
    - key 이름은 머신에서 쓰기 좋게 **영어 lower_snake_case**로 만드는 것을 권장합니다.
        (예: "refund_reason", "application_procedure", "tax_item")
    - 날짜 관련 표기는 YYYY-MM-DD 로 표기. 년도가 없을경우는 MM-DD
    - **은행계좌(bank_account)의 경우 은행 명도 같이 표기할 것**
    
    3) meta
    - 문서 분석에 참고할 수 있는 정보들을 넣습니다.
    - 예시 (필수는 아님):
        - page_count: 정수
        - has_sensitive_info: true/false (주민등록번호, 계좌번호, 개인 전화번호, 상세 주소 등이 있으면 true)
        - source: "OCR", "PDF_TEXT" 등
        - doc_language: "ko"
        - 기타 필요한 메타 정보 (예: "has_signature": true 등)

    4) 출력 형식
    - 반드시 **하나의 JSON 객체만** 출력하세요.
    - JSON 바깥에 설명, 주석, 자연어 문장, ``` 기호 등은 절대 넣지 마세요.
    - 키 순서는 상관없지만, 최소한 "doc_type", "entities", "meta" 세 개는 포함해야 합니다.

    5) 내용 처리
    - 텍스트를 요약해서 엔티티 값을 만들 수 있지만,
        문서의 핵심 정보를 잃지 않도록 주의하세요.
    - 엔티티 값은 가능한 한 문서에 나온 표현을 기반으로 합니다.
    """


    # ---- 1) 입력 텍스트 가져오기 (str / List[str] 둘 다 지원) ----
    refined =  state.get("refined_txt")

    if isinstance(refined, str):
        document_text = refined
        page_count = 1
    elif isinstance(refined, list):
        non_empty = [t for t in refined if t]
        document_text = "\n\n".join(non_empty)
        page_count = len(refined) if refined else 0
    else:
        document_text = ""
        page_count = 0

    # 결과 기본값 세팅
    state["ner_result"] = {}
    state["ner_result_raw"] = ""
    state.pop("ner_error", None)

    if not document_text.strip():
        state["ner_error"] = "NER: 입력 텍스트가 비어 있습니다."
        return state

    # ---- 2) LLM 호출 (gpt-4o-mini) ----
    user_prompt = f"""
    다음은 한국어 행정/공공 문서의 전체 텍스트입니다.

    - 이 문서는 총 {page_count} 페이지입니다.
    - 텍스트 출처(source)는 "PDF_TEXT" 라고 가정합니다.

    문서를 분석하여, 시스템 메시지에서 정의한 형식에 맞는
    단일 JSON 객체만 출력하세요.

    <문서 시작>
    {document_text}
    <문서 끝>
    """

    try:
        resp = client.responses.create(
            model="gpt-4o-mini",
            input=[
                {"role": "system", "content": NER_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            max_output_tokens=2048,
        )

        raw = resp.output[0].content[0].text.strip()
        state["ner_result_raw"] = raw

    except Exception as e:
        state["ner_error"] = f"NER: LLM 호출 중 예외 발생 - {e!r}"
        return state

    # ---- 3) JSON 파싱 ----
    text = state["ner_result_raw"].strip()

    # ```json ... ``` 형식이 섞여 있으면 제거 시도
    if text.startswith("```"):
        text = text.strip("`")
        lines = text.splitlines()
        if lines and lines[0].strip().lower().startswith("json"):
            lines = lines[1:]
        text = "\n".join(lines).strip()

    try:
        parsed = json.loads(text)
    except Exception:
        state["ner_error"] = "NER: LLM 출력에서 JSON 파싱 실패"
        return state

    if not isinstance(parsed, dict):
        state["ner_error"] = "NER: 파싱된 결과가 JSON 객체가 아닙니다."
        return state

    # meta.page_count 기본값 채워넣기
    meta = parsed.setdefault("meta", {})
    if "page_count" not in meta:
        meta["page_count"] = page_count or 1

    state["ner_result"] = parsed
    return state
