# --------------------------------------------------------------
# text_utils.py (강화 버전)
# OCR / PDF 파서 / HWP / Word 등의 텍스트를 공격적으로 전처리하는 모듈.
# --------------------------------------------------------------
import re
from typing import List, Union
from src.utils.config import load_api_keys
from src.utils.config import LLM_MODEL
# ============================================
# 🔹 1) 기본 클린 함수
# ============================================
def clean_text(text: str) -> str:
    if not text:
        return ""

    text = text.replace("\ufeff", "")  # BOM 제거

    # 특수문자 제거
    text = re.sub(r"[■□◆◇●○★☆◼︎◻︎]", " ", text)
    text = re.sub(r"[’‘“”´`•·]", " ", text)

    # OCR 찌꺼기 기호
    text = re.sub(r"[~^_+=▣▤▥▦▧▨▩]", " ", text)

    # OCR 한글깨짐 (자모 반복)
    text = re.sub(r"[ㄱ-ㅎ]{2,}", "", text)

    # 의미 없는 영어 단독 토큰
    text = re.sub(r"\b[A-Za-z]{2,}\b", "", text)

    # 공백 정리
    text = re.sub(r"\s+", " ", text)

    return text.strip()


# ============================================
# 🔹 2) OCR 특성 보정 규칙
# ============================================
def ocr_fix(text: str) -> str:
    if not text:
        return ""

    text = re.sub(r"(\d+)\.(\S)", r"\1. \2", text)
    text = re.sub(r"(\.)([가-힣])", r"\1 \2", text)
    text = re.sub(r"(\d)([가-힣])", r"\1 \2", text)
    text = re.sub(r"([가-힣])(\d)", r"\1 \2", text)

    # 쉼표 뒤 공백
    text = re.sub(r",(\S)", r", \1", text)

    # 대괄호 블록 붙은 경우 개행
    text = re.sub(r"(\])(\S)", r"\1\n\2", text)

    return text


# ============================================
# 🔹 3) 문장부호 기반 개행 삽입
# ============================================
def restore_linebreak(text: str) -> str:
    if not text:
        return ""

    text = re.sub(r"([\.!?])\s+", r"\1\n", text)
    text = re.sub(r"(:)\s+", r"\1\n", text)

    # 불릿 문자
    bullet = r"[•○●\-\u2460-\u2473]"
    text = re.sub(fr"({bullet})\s*", r"\n\1 ", text)

    return text.strip()


# ============================================
# 🔹 4) 짧은 토큰 제거
# ============================================
def remove_noise_tokens(text: str) -> str:
    tokens = text.split()
    cleaned = [t for t in tokens if len(t) > 1]
    return " ".join(cleaned)


# ============================================
# 🔹 5) 개별 텍스트 전처리 pipeline (문자열 용)
# ============================================
def preprocess_single(text: str) -> str:
    if not text:
        return ""

    text = clean_text(text)
    text = ocr_fix(text)
    text = restore_linebreak(text)
    text = remove_noise_tokens(text)

    return text.strip()


# ============================================
# 🔹 6) 리스트 입력을 자동 인식하는 전처리
# ============================================
def preprocess_text(text: Union[str, List[str]]) -> Union[str, List[str]]:
    """
    문자열 입력 → 문자열 반환  
    리스트 입력 → 리스트 각각 처리 후 리스트 반환
    """
    if isinstance(text, list):
        return [preprocess_single(t) for t in text]

    return preprocess_single(text)


# ============================================
# 🔹 7) 페이지 리스트 전용 함수 (alias)
# ============================================
def preprocess_pages(text_list: List[str]) -> List[str]:
    return [preprocess_single(t) for t in text_list]
