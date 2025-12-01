# src/utils/state.py

from __future__ import annotations

from typing import TypedDict, List, Dict, Any


class State(TypedDict, total=False):
    """
    공공문서 파이프라인 공용 State 스키마.

    - ingestion/node_ingestion_pipeline
    - ingestion/pdf_test
    - analyze/node_preprocess
    - analyze/node_analyzer
    - analyze/node_analyze_structure
    - analyze/node_ner_extractor
    - result/node_action_extractor
    - result/node_result_packager

    에서 사용하는 키들을 모두 모아둔 superset.
    필요한 노드는 이 중 일부 key만 읽고/쓰도록 설계.
    """

    # ------------------------------------------------------------------
    # 1. 입력/기본 정보 (파일 & 작업 디렉터리)
    # ------------------------------------------------------------------
    input_path: str           # 업로드/선택한 원본 파일 경로
    file_type: str            # file_classifier 결과 (예: "pdf", "image", "word"...)

    output_dir: str           # node_ingestion_pipeline에서 만든 출력/작업 폴더
    work_dir: str             # (선택) 과거 코드 호환용 alias, 필요하면 output_dir와 동일하게 사용

    # ------------------------------------------------------------------
    # 2. PDF / 이미지 관련 정보
    # ------------------------------------------------------------------
    pdf_path: str             # 실제 분석 대상이 되는 PDF 경로 (원본이 이미지/word여도 여기로 수렴)
    slide_image: List[str]    # pdf_image_extractor가 생성한 각 페이지 PNG 경로 리스트
    slide_index: int          # 현재 처리 중인 페이지 index (0-based)

    # (옵션) 테스트/최적화용 핸들 — 대부분의 노드에서는 사용하지 않음
    pdf_doc: Any              # fitz.Document 등 PDF 핸들 (재사용용)

    # ------------------------------------------------------------------
    # 3. 텍스트 추출 결과 (페이지 단위 / 정제 단계별)
    # ------------------------------------------------------------------
    # ingestion 단계에서 추출/클렌징한 텍스트
    raw_txt: List[str]        # OCR/텍스트 레이어 등에서 바로 뽑은 원본 페이지 텍스트
    refined_txt: List[str]    # preprocess_text + llm_clean_pii 적용 후의 페이지 텍스트

    # pdf_test + node_preprocess에서 사용하는 이름
    raw_texts: List[str]      # 테스트용 pdf_text_test가 채우는 페이지 텍스트
    refined_text: Any         # node_preprocess 이후 텍스트 (보통 List[str] 또는 str)

    # 구조 분석용 통합 텍스트
    #   - 문자열 / 문자열 리스트 / 페이지-블록 2D 리스트 등
    texts: Any                # node_analyze_structure가 읽는 입력 텍스트 컨테이너

    # (참고용/실험용)
    raw_data: List[str]       # app/main_dev.py 등에서 사용하는 별칭 (raw_txt와 매핑해서 써도 됨)

    # ------------------------------------------------------------------
    # 4. 문서 유형/구조 정보
    # ------------------------------------------------------------------
    doc_type: Dict[str, Any]  # {"문서유형": "...", "행동지시": bool} 형태의 분류 결과
    structure_summary: str    # 문서 구조(섹션/표/목록) 요약 텍스트

    # ------------------------------------------------------------------
    # 5. 행정정보 NER / 엔티티 추출 결과
    # ------------------------------------------------------------------
    ner_result: Dict[str, Any]    # 동적 key 기반 엔티티 결과 ({"doc_type": ..., "entities": {...}, "meta": {...}})
    ner_result_raw: str           # LLM이 출력한 원본 JSON 문자열
    ner_error: str                # NER 수행/파싱 중 에러 메시지

    # ------------------------------------------------------------------
    # 6. 사용자 행동 정보 & 최종 결과
    # ------------------------------------------------------------------
    needs_action: bool            # 사용자가 실제로 해야 할 행동이 있는지 여부
    action_info: List[Dict[str, Any]] | None
                                  # 행동 리스트: 각 원소에 "action", "who", "when", "how", "where" 등이 들어감

    summary: str                  # 문서 전체 핵심 요약 (node_result_packager에서 생성)

    # ------------------------------------------------------------------
    # 7. (옵션) 표/이미지 텍스트 – 아직 주석/실험 단계
    # ------------------------------------------------------------------
    tables: Any                   # 표 텍스트 (List[List[List[str]]]) 형태로 사용할 예정
    images: Any                   # 이미지 경로/메타데이터 등
