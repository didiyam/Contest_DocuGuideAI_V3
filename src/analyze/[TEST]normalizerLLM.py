

from typing import List, Optional
from openai import OpenAI

client = OpenAI()  # 환경에 맞게 생성 (API 키는 환경변수나 config에서 설정)


LLM_NORMALIZE_SYSTEM_PROMPT = """
당신은 공공문서 전처리 어시스턴트입니다.

당신의 임무는 '내용 손실 없이' 텍스트를 정규화(cleaning/normalizing) 하는 것입니다.
다음 규칙을 지키세요.

1) 절대 요약하지 마세요.
2) 문장의 의미를 바꾸지 마세요. (의역, 재구성, 삭제, 추가 금지)
3) 할 일:
   - 잘못된 띄어쓰기, 기본적인 맞춤법만 자연스럽게 수정
   - 이상한 특수기호, 중복 공백을 정리
   - 따옴표, 대시 기호를 일반적인 형태로 통일 (예: “ ” → ", ‘ ’ → ')
4) 줄바꿈은 가능한 한 보존하되, 의미 없는 연속 빈 줄은 1줄로 줄입니다.
5) 표/번호 목록 등은 가능한 한 형태를 유지하세요.

출력은 정규화된 텍스트만 그대로 출력하세요.
여는 말, 설명, 주석 등을 붙이지 마세요.
"""


def normalize_text_with_llm(
    text: Optional[str],
    model: str = "gpt-4.1-mini",
) -> str:
    """
    LLM을 사용하여 '내용 손실 없이' 텍스트를 정규화하는 함수 (단일 문자열 버전).

    - 맞춤법/띄어쓰기/기호 통일 등만 수행
    - 요약/삭제/의역은 하지 않도록 프롬프트로 강하게 제한
    """
    if not text:
        return ""

    resp = client.responses.create(
        model=model,
        input=[
            {
                "role": "system",
                "content": LLM_NORMALIZE_SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": f"<TEXT>\n{text}\n</TEXT>",
            },
        ],
        max_output_tokens= len(text) * 2,  # 대략 원문 길이 기준 여유 있게
    )

    # responses API 기준 파싱 (환경에 따라 구조는 조정 가능)
    output = resp.output[0].content[0].text
    return output.strip()


def normalize_texts_with_llm(
    texts: List[Optional[str]],
    model: str = "gpt-4.1-mini",
) -> List[str]:
    """
    여러 텍스트를 한꺼번에 LLM 정규화하는 리스트 버전.

    사용 예:
        from utils.text_utils import normalize_texts_with_llm

        cleaned_list = normalize_texts_with_llm(raw_list)
    """
    results: List[str] = []
    for t in texts:
        cleaned = normalize_text_with_llm(t, model=model)
        results.append(cleaned)
    return results
