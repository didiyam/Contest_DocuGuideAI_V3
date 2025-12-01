import re
import unicodedata

def normalize_text(text: str) -> str:
    """
    공공문서용 기본 텍스트 정규화 함수.

    - Unicode 정규화 (전각/반각, 특수문자 정리)
    - 줄바꿈 통일 (\r\n, \r → \n)
    - 따옴표/대시 기호 통일
    - 제로폭 공백 제거
    - 줄 단위로 공백 정리 (여러 공백 → 하나, 앞뒤 공백 제거)
    - 빈 줄이 여러 개 있으면 1줄만 남김
    """

    if text is None:
        return ""

    # 1) 문자열화 + 유니코드 정규화 (전각/반각 통합 등)
    text = str(text)
    text = unicodedata.normalize("NFKC", text)

    # 2) 줄바꿈 통일
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # 3) 따옴표/대시 통일
    replace_map = {
        "“": '"', "”": '"', "‟": '"', "＂": '"',
        "‘": "'", "’": "'", "‛": "'", "＇": "'",
        "–": "-", "—": "-", "−": "-",
    }
    for src, tgt in replace_map.items():
        text = text.replace(src, tgt)

    # 4) 제로폭 공백/제어용 특수 문자 제거
    text = re.sub(r"[\u200B-\u200D\uFEFF]", "", text)

    # 5) 줄 단위로 공백 정리 (여러 공백 → 하나, 양 끝 공백 제거)
    lines = []
    for line in text.split("\n"):
        # \s+ 를 공백 하나로
        line = re.sub(r"\s+", " ", line)
        line = line.strip()
        lines.append(line)

    # 6) 빈 줄 여러 개 → 1줄만 남기기
    normalized_lines = []
    prev_blank = False
    for line in lines:
        if line == "":
            if not prev_blank:
                normalized_lines.append("")
            prev_blank = True
        else:
            normalized_lines.append(line)
            prev_blank = False

    # 전체 앞뒤 공백 제거
    return "\n".join(normalized_lines).strip()
