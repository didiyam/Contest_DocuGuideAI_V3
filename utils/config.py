import os
from dotenv import load_dotenv

# ================================
# config.py
# api, 설정값(경로 등) 저장
# ================================

# 프로젝트 기본 폴더 기준 (src 기준)
WORK_DIR = "./output/"
# # MEDIA_DIR = "./output/"
# BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# WORK_DIR = os.path.join(BASE_DIR, "output")

load_dotenv()

def load_api_keys():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY가 .env 파일에 없습니다.")
    return api_key


# ================================
# 🤖 AI Model Settings
# ================================

# # LLM 모델 이름
LLM_MODEL = "gpt-4o-mini"

# ================================
# 💬 User Prompt Default
# ================================

# DEFAULT_USER_PROMPT = {
#     "voice": DEFAULT_VOICE,
#     "tone": "친절하고 명료한 강의 톤",
#     "style": "예시와 핵심 요점 중심",
#     "lang": "한국어",
#     "target": "대학생",
# }

# ================================
# 🎬 Video / Audio Settings
# ================================

# VIDEO_WIDTH = 1920
# VIDEO_HEIGHT = 1080
# AUDIO_BITRATE = "192k"

# ================================
# ⚙ App Settings
# ================================

RECURSION_LIMIT = 200