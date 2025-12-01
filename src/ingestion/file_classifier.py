# --------------------------------------------------------------
# file_classifier.py
# 업로드된 파일 형식을 판별하는 모듈.
# 지원 파일: PDF / HWP / Word / 이미지 / PPT / TXT
# 지원 불가: Excel(xlsx/xls), CSV, JSON, XML, HTML, GIF 등은
# 공공문서 분석 목적상 처리 대상에서 제외한다.
# --------------------------------------------------------------

import os
import mimetypes

SUPPORTED_TYPES = {
    "pdf",
    "hwp",
    "doc", "docx",
    "ppt", "pptx",
    "txt",
    "jpg", "jpeg", "png"
}


def classify_file(file_path: str) -> str:
    """
    파일 확장자 기반으로 문서 형식을 판별한다.
    Args:
            file_path (str): 저장된 파일의 경로    
    Returns:
        str: 분류된 파일 타입
             pdf / hwp / word / ppt / image / txt / excel / unsupported
    """

    ext = os.path.splitext(file_path)[1].lower().replace(".", "")

    # ------------------------
    # 1) 우선 확장자로 판단
    # ------------------------
    if ext == "pdf":
        return "pdf"

    if ext == "hwp":
        return "hwp"

    if ext in {"doc", "docx"}:
        return "word"

    if ext in {"ppt", "pptx"}:
        return "ppt"

    if ext in {"jpg", "jpeg", "png"}:
        return "image"

    if ext == "txt":
        return "txt"

    # ------------------------
    # 2) 확장자가 없으면 MIME 검사
    # ------------------------
    # jpg/hwp/doc/docx/ppt/pptx는 MIME으로 분류하면 위험하기 때문에 제외한 것.
    mime, _ = mimetypes.guess_type(file_path)

    if mime:
        if "pdf" in mime:
            return "pdf"
        if "image" in mime:
            return "image"
        if "text" in mime:
            return "txt"

    # ------------------------
    # 3) 마지막 fallback
    # ------------------------
    return "unsupported"