from openai import OpenAI
import base64
from src.utils.logger import log
from src.utils.config import LLM_MODEL
from src.utils.config import load_api_keys
import os
# os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE" # 위치변경 절대 금지
import fitz
# from src.utils.api_client import client
def pdf_to_images(pdf_path: str, dpi: int = 350) -> list[str]:
    doc = fitz.open(pdf_path)
    image_paths = []
    base = os.path.dirname(pdf_path)

    try:
        for i, page in enumerate(doc):
            pix = page.get_pixmap(dpi=dpi)
            img_path = os.path.join(base, f"page_{i+1}.png")
            pix.save(img_path)
            image_paths.append(img_path)
    finally:
        doc.close()

    return image_paths
# 텍스트 llm 정제
API_KEY = load_api_keys()
client = OpenAI(api_key=API_KEY)

PROMPT ="""
너는 공공문서 전문 정제 및 개인정보 보호 전문가다.

이미지를 기반으로 텍스트를 추출할 때 반드시 아래 규칙을 지켜라.

[공공문서 정제 규칙]

1) 맞춤법, 띄어쓰기, 문장 구조는 공문서 스타일로 자연스럽게 복원한다.
2) 문서의 의미와 내용은 절대 변경하지 않는다.
3) 표, 불릿, 항목 번호, 문단 구조는 최대한 원본에 가깝게 유지한다.
4) 문서에 없는 내용을 임의로 추가하지 않는다.
5) 설명, 해설, 부가 코멘트는 절대 작성하지 않는다.
   (출력은 정제된 텍스트만 반환할 것)

[개인정보(PII) 마스킹 규칙]
개인의 정보만 정확히 식별하여 아래 규칙에 따라 마스킹한다.

1. 마스킹해야 하는 정보(개인 정보)
- 개인 이메일 주소 (예: naver.com, gmail.com 등)
- 개인 휴대폰 번호 및 개인 유선전화 번호
- 개인의 집주소, 상세 주소
- 주민등록번호, 여권번호 등 개인 식별번호

2. 마스킹하지 말아야 하는 정보(기관 정보)
- 정부·지자체·공공기관·학교·법인 도메인 이메일  
  (예: ***@korea.kr, ***@go.kr, ***@seoul.go.kr, ***@company.co.kr)
- 기관/회사 대표번호, 고객센터 전화번호  
  (예: 02-120, 1588-0000, 1577-0000 등)
- 관공서/기관/학교/회사 등 공적인 주소
- 부서 연락처나 업무용 공식 이메일

3. 마스킹 규칙
- 개인 이메일 → [이메일비공개]
- 개인 전화번호 → [전화번호비공개]
- 개인 집주소 → [주소비공개]
- 개인 식별번호(주민등록번호·여권번호 등) → [식별번호비공개]

출력 형식:
→ OCR로 읽은 공문 스타일 텍스트 + 개인정보만 마스킹된 결과
→ 어떠한 설명이나 부가 정보도 포함하지 않는다.
"""

def llm_clean_pii(text: str) -> str:
    """
    LLM을 사용해 '개인' 정보만 정확히 마스킹하고
    문서를 자연스럽게 복원하는 함수.
    """
    if not text or not text.strip():
        return text

    prompt = PROMPT + "\n\n[원문]\n" + text

    resp = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system",
             "content": "너는 한국어 공공문서의 개인정보를 선별적으로 마스킹하고 문서 형태를 정제하는 전문 AI다."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.0,
    )

    return resp.choices[0].message.content.strip()



# 아래는 llm으로 이미지에서 바로 텍스트 추출시 사용
# 이미지 → base64 변환
def encode_image(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


# GPT Vision 1페이지 처리 함수
def extract_page_text(image_path: str) -> str:
    """
    GPT-Vision 기반 OCR + PII 마스킹을
    llm_clean_pii 수준으로 실행하는 고성능 버전
    """

    image_b64 = encode_image(image_path)

    vision_prompt = PROMPT

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": "너는 한국어 공공문서의 이미지에서 텍스트를 추출과 정제를 하고, 개인정보를 선별적으로 마스킹하는 전문 AI다."
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": vision_prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{image_b64}"}
                    }
                ]
            }
        ],
        max_tokens=4096,
        temperature=0.0,
    )

    return response.choices[0].message.content.strip()


# 전체 페이지 Vision 처리
def llm_text_from_images(image_paths: list[str]) -> list[str]:
    """
    이미지를 GPT-4o Vision에 넣고 페이지별 텍스트를 정제하여 반환하는 함수
    """
    final_pages = []
    log(f"[Vision] 총 {len(image_paths)} 페이지 인식 시작")

    for idx, img in enumerate(image_paths):
        log(f"[Vision] 페이지 {idx+1}/{len(image_paths)} 처리 중: {img}")

        try:
            refined = extract_page_text(img)
        except Exception as e:
            log(f"[Vision ERROR] {idx+1}페이지 오류: {e}", level="error")
            refined = ""

        final_pages.append(refined)

    log(f"[Vision] 전체 {len(final_pages)} 페이지 Vision OCR 완료")
    return final_pages
