# src/app/pipeline.py

from __future__ import annotations

from typing import Any, Dict

from src.utils.config import load_api_keys
from src.utils.state import State

# 1단계: 인입(ingestion)
from src.ingestion.node_ingestion_pipeline import node_ingestion_pipeline

# 2단계: 텍스트 전처리(cleaning/normalizing)
from src.analyze.node_preprocess import node_preprocess

# 3단계: 문서 유형 / 행동지시 여부 판단
from src.analyze.node_analyzer import Classify_doc_type

# 4단계: 행정정보 NER 추출
from src.analyze.node_ner_extractor import node_ner_extractor

# 5단계: 행동 정보 추출 + 요약/패키징
#from src.result.Test_node_action_extractor import node_action_extractor 
#from src.result.Test_node_result_packager import node_result_packager



def run_full_pipeline(input_path: str) -> State:
    """
    실제 서비스용 노드만 순서대로 호출하는 전체 파이프라인.

    순서:
        1) node_ingestion_pipeline  : 파일 타입 판별, PDF 변환, OCR, PII 마스킹, 기본 클렌징
        2) node_preprocess          : state["raw_texts"] → state["refined_text"] (cleaning/normalizing)
        3) Classify_doc_type        : 문서유형/행동지시 여부 → state["doc_type"]
        4) node_ner_extractor       : 행정정보 NER → state["ner_result"]
        5) node_result_packager     : 요약 + 행동지시 정리 → 최종 패키징

    입력:
        input_path : 업로드된 원본 파일 경로 (PDF, 이미지, HWP, PPTX 등)

    출력:
        State(TypedDict) 전체. 주요 필드 예:
            - raw_data / txt_pages / refined_txt
            - refined_text
            - doc_type
            - ner_result
            - result_summary / action_info 등
    """
    # 0) API 키 로드
    load_api_keys()

    # 1) 초기 state 구성
    state: State = State(
        input_path=input_path
    )

    # 2) 인입 파이프라인 (파일 타입 판별 + OCR + PII 마스킹 등)
    state = node_ingestion_pipeline(state)

    # 3) 텍스트 전처리 (cleaning/normalizing 전용)
    state = node_preprocess(state)

    # 4) 문서 유형 / 행동지시 여부 판단
    state = Classify_doc_type(state)

    # 5) 행정정보 NER 추출
    state = node_ner_extractor(state)

    # 6) 결과 패키징 (요약 + 행동지시 등)
    #state = node_action_extractor(state)
    #state = node_result_packager(state)

    print(state)
    return state

run_full_pipeline(State)

