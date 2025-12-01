# 수정안된 state입니다. 수정이 필요합니다(251120)
# 
# 
# # State 정의 및 초기화
from typing import TypedDict, List, Dict, Any



# 가입요건 등을 기반으로 사용자에게 질문 응답받기(유환)관련 클래스 정의 필요함.
class ReviewQuestion(TypedDict, total=False):
    question: str
    options: List[str]
    answer: int

class State(TypedDict, total=False):
    
    #[진아 파트]
    #node_ingestion_pipeline
    input_paths : List[str] #업로드한 실제 파일 주소들 list(이미지는 주소 여러개/pdf는 한개)
    pdf_path: str              #변환된 pdf 파일 경로(이미지 업로드시 생성)
    output_dir: str         # 결과물 위치 폴더 주소(파일명은 포함 안 함)

    # 결과물
    raw_txt: List[str] # ocr 직후 또는 pdf에서 추출된 raw 텍스트
    refined_txt : List[str] # clean & llm & pll 보정된 텍스트(☑️vector DB에 저장)

    #[유환 파트]
    #node_ner_extractor
    doc_type : Dict             #문서 형식, 행동지시 여부 
    ner_result : Dict           #행정정보json
    ner_result_raw : str        #LLM 원문
    ner_error : str             #ner 추출시 발생한 에러

    #[서영 파트]
    #node_action_extractor
    needs_action: Any           #행동지시 여부 확인
    action_info: Dict           #지시받은 행동 정보
    # node_result_packager
    summary : str               #문서의 내용 및 지시 정보 정리
    #node_result
    act_title_text : List[Dict]

    # 최종 패키징 산출물 
    # ☑️vector DB에 저장 : summary, needs_action, action_info
    db_package : Dict  #node_result_packager
    
    # 🖥️web 출력용 : title, text (부드러운 llm 설명)
    web_package :  List[Dict] #node_result

    # chat/rag_chat_engine
    generate_response : Dict   #최종 RAG 챗봇 응답(answer, source, state)
    present_answer : str      #answer
    history : List[Dict]      #질문 답변 기록 [{"question": str, "answer": str}]




class Backup(TypedDict, total=False):

    # 생성 산출물
    page_content: List[str]
    script: List[str]

    # 미디어 산출물
    audio: List[str]
    video_path: List[str]
    video_with_subtitle: List[str]

    #음성 산출물
    voice: str 
    TTS_MODEL: str 
    tts_clarity: bool 
    tts_ssml: bool  

    is_done: bool 
    final_video_path: str 
    summary: str 
    review_questions: List[ReviewQuestion] 