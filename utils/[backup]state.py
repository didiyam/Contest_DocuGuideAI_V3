# 수정안된 state입니다. 수정이 필요합니다(251120)
# 
# 
# # State 정의 및 초기화
from typing import TypedDict, List, Dict



# 가입요건 등을 기반으로 사용자에게 질문 응답받기(유환)관련 클래스 정의 필요함.
class ReviewQuestion(TypedDict, total=False):
    question: str
    options: List[str]
    answer: int

class state(TypedDict, total=False):
    # 입력/기본
    # pptx -> pdf 로 변경
    pdf_path: str
    pdf_doc : any
    work_dir: List[str]
    media_dir: List[str]
    prompt: Dict
    slide_index: int
    slide_type: str

    #문서 분해
    refined_text : str

    # 추출 산출물
    texts: List[List[str]]
    tables: List[List[List[List[str]]]]
    images: List[List[str]]
    slide_image: List[str]

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