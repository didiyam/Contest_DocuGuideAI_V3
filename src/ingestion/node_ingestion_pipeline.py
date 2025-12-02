# ocr 라이브러리 쓴다면 (이진아) 검색하기
# 
# node_ingestion_pipeline.py
# 파일 업로드 후 전체 ingestion 파이프라인 오케스트레이션
# - 파일 타입 판별 → PDF 변환 → OCR → 텍스트 추출 → 클렌징/LLM 정제\

# import os
# import tkinter as tk
# from tkinter import filedialog
from typing import List


from src.utils.state import State
from src.ingestion.file_classifier import classify_file
# from src.ingestion.pdf_converter import doc_to_pdf, images_to_pdf
from src.ingestion.doc_parser import extract_pdf_text #, extract_ppt_text
# from src.ingestion.ocr_image_runner import pdf_to_images, run_ocr
from src.utils.text_utils import preprocess_text
from src.utils.file_utils import create_output_folder
from src.utils.logger import log, user_log 
from src.ingestion.llm_clean_data_pll import llm_text_from_images ,pdf_to_images,encode_image


# 실제 텍스트 존재 여부 확인
def has_real_text(pages: list[str]) -> bool:
    for p in pages:
        clean = p.replace("\n", "").replace("\r", "").strip()
        if not clean:
            continue

        # 실제 문자(한글,영문,숫자)가 포함되어 있으면 텍스트가 있다고 판단
        for ch in clean:
            if ch.isalnum() or "\uac00" <= ch <= "\ud7a3":  # 한글 범위 체크
                return True
    return False

# OCR 여부 확인 및 텍스트 추출
def check_do_ocr(pdf_path: str, state: dict):
    """
    PDF 텍스트 레이어 없는 것 확인 후 OCR (클렌징+LLM 하기 전)
    """
    log(f"[OCR PDF] 텍스트 레이어 추출 시도: {pdf_path}")
    parsed_pages = extract_pdf_text(pdf_path)  # list[str]

    # PDF 텍스트 레이어가 있는 경우(list 중 하나라도 text 존재)
    all_text = "\n".join(parsed_pages).strip()
    if len(all_text) >= 10:
        log("[PDF 파서] 텍스트 레이어가 감지되어 OCR 생략")
        state["raw_txt"] = parsed_pages
        return parsed_pages
     
    # OCR 수행
    log("[OCR PDF] 텍스트 없음 → OCR 수행 시작")

    # 1) PDF → 이미지 변환
    images = pdf_to_images(pdf_path)
    log(f"[PDF OCR] PDF → 이미지 변환 완료 (총 {len(images)}페이지)")

    # 2) OCR 실행(GPT Vision 사용)
    
    #(이진아) 주석하기(한 줄)
    ocr_pages = llm_text_from_images(images)

    log("[텍스트 없는 PDF OCR] Vision OCR 완료")
    #(이진아) 주석해제
    # images = pdf_to_images(pdf_path)
    # log(f"[OCR] PDF → 이미지 변환 완료 (총 {len(images)}페이지)")
    # ocr_pages = run_ocr(images)  # list[str]
    # log("[OCR] OCR 완료")
    state["raw_txt"] = ocr_pages
    return ocr_pages



# 메인 Ingestion 파이프라인
def node_ingestion_pipeline(state: dict) -> State:
    """
    문서 파일 확장자 판별 후 확장자별로 텍스트 추출
    → 클렌징 + LLM 정제까지 수행
    결과는 state["raw_txt"] (List[str])에 저장
    """
    # 출력 폴더 생성
    output_dir = create_output_folder()
    state["output_dir"] = output_dir
    log(f"[파이프라인] output 디렉토리 생성: {output_dir}")
 
    # 입력 파일이 여러 개일 경우 → 첫 번째 파일로 타입 판별
    first_file = state["input_paths"][0]
    log(f"[파이프라인] 입력 파일 경로: {first_file}")

    # 이미지 여러 장 처리용 전체 리스트
    input_paths = state["input_paths"] 


    # 1) 파일 타입 판별
    file_type = classify_file(first_file)
    log(f"[파이프라인] 판별된 파일 타입: {file_type}")

    txt_pages: List[str] = []

    # 2) 이미지 : GPT Vision OCR 처리
    if file_type == "image":
        input_paths = [encode_image(p) for p in input_paths]
        #(이진아) 아래 두문장 주석처리
        txt_pages = llm_text_from_images(input_paths)
        state["raw_txt"] = txt_pages
        #(이진아) 주석해제( 여러 장 PDF 통합 후 OCR 진행)
        # pdf_path = images_to_pdf(
        #     input_paths,
        #     os.path.join(output_dir, "images_to_pdf.pdf"),
        # )
        # log(f"[변환] 이미지 -> PDF 변환 완료: {pdf_path}")
        # txt_pages = check_do_ocr(pdf_path,state)
        

    # 3) TXT : 클렌징 후 바로 사용
    # elif file_type == "text":
    #     user_log("텍스트 파일로 판단되어, 내용을 바로 불러옵니다.", step="read_text")
    #     with open(first_file, "r", encoding="utf-8") as f:
    #         raw_txt = f.read()
    #     txt_pages = [raw_txt]
    #     log("[텍스트] TXT 파일에서 텍스트 읽기 완료")

    # 4) PPT : 별도로 텍스트 추출
    # elif file_type == "ppt":
    #     user_log("PPT 문서로 판단되어, 슬라이드 텍스트를 추출합니다.", step="ppt_parse")
    #     full_txt = extract_ppt_text(first_file)
    #     txt_pages = [full_txt]
    #     log("[PPT] PPT 텍스트 추출 완료")

    # 5) Word : PDF 변환 후 처리 (HWP는 현재 보류)
    # elif file_type == "word":
    #     user_log("Word 문서로 판단되어, PDF로 변환 후 처리합니다.", step="word_convert")
    #     pdf_path = doc_to_pdf(
    #         first_file,
    #         os.path.join(output_dir, "doc_to_pdf.pdf"),
    #     )
    #     log(f"[변환] Word → PDF 변환 완료: {pdf_path}")
    #     txt_pages = check_do_ocr(pdf_path,state)

    # 6) PDF : 텍스트 레이어 확인 후 필요 시 OCR
    elif file_type == "pdf":
        user_log("PDF 문서로 판단되어, 텍스트를 추출합니다.", step="pdf_parse")
        txt_pages = check_do_ocr(first_file,state)

    else:
        user_log("지원하지 않는 파일 형식입니다. 다른 문서를 선택해 주세요.", step="error")
        log(f"[에러] 지원하지 않는 파일 타입: {file_type}", level="error")
        state["raw_txt"] = []
        return state

    # 7) 클렌징 + LLM 정제
    user_log("문서 내용을 정리하고 있어요. 잠시만 기다려 주세요 ✨", step="clean_llm")
    log("[클렌징] preprocess_text + llm_cleaner 시작")
    #(이진아) 두줄 주석필요
    clean_txt_pages: List[str] = [
    preprocess_text(t or "") for t in txt_pages]

    # (이진아) 주석해제
    # clean_txt_pages: List[str] = [
    #     llm_clean_pii(preprocess_text(t or "")) for t in txt_pages
    # ]

    log("[클렌징] 모든 페이지 클렌징 + LLM 정제 완료")

    state["refined_txt"] = clean_txt_pages
    user_log("문서 분석 준비가 모두 완료되었습니다", step="done")
    log("[파이프라인] node_ingestion_pipeline 완료")

    return state
