# 유용한 함수들
"""
* 다음은 프로젝트를 수행하는데 유용한 함수들입니다.
* 이 함수들의 내용을 확인하고 필요시 활용합니다.(꼭 활용해야 하는 것은 아닙니다.)
"""

import os, re,  subprocess, base64, mimetypes
from typing import List
from pathlib import Path
from datetime import datetime
import uuid

from src.utils.config import WORK_DIR



"""* 공백 제거 함수"""
def clean_text(s):
    return re.sub(r"\s+", " ", s).strip()

"""* 긴 문자열을 문장 단위로 나누는 문장 분리기"""
def split_sents(t: str) -> List[str]:
    parts = re.split(r'([\.?!])', t)
    merged = []
    for i in range(0, len(parts)-1, 2):
        sent = (parts[i] + parts[i+1]).strip()
        if sent: merged.append(sent)
    if len(parts) % 2 == 1 and parts[-1].strip():
        merged.append(parts[-1].strip())
    return [s for s in merged if s] 

def create_output_folder():
    """
    실행 날짜 + 시간(년-월-일_시-분_초) 기반 고유 폴더 생성
    """
    # 현재 timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M_%S")

    # 폴더명
    folder_name = f"{timestamp}"

    # 절대경로로 오브젝트 만들기
    output_path = os.path.join(WORK_DIR, folder_name)

    # 충돌 대비
    if os.path.exists(output_path):
        folder_name = f"{folder_name}_{uuid.uuid4().hex[:6]}"
        output_path = os.path.join(WORK_DIR, folder_name)

    # 실제 디렉터리 생성
    os.makedirs(output_path, exist_ok=True)

    return output_path

""" state['texts'] (list[str])를 txt 파일로 저장하는 함수"""
def save_texts_to_file(text_list, output_folder, filename="extracted_texts.txt"):
   
    save_path = os.path.join(output_folder, filename)

    with open(save_path, "w", encoding="utf-8") as f:
        for page_idx, text in enumerate(text_list):
            f.write(f"=== [PAGE {page_idx + 1}] ===: 페이지 구분줄은 실제로 저장되지 않습니다.\n")
            f.write(text + "\n\n")

    return save_path

"""* 이미지를 base64로 변환"""

def img_to_data_url(path: str) -> str:
    mime = mimetypes.guess_type(path)[0] or "image/png"
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    return f"data:{mime};base64,{b64}"
