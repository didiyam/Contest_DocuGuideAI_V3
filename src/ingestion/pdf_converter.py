# pdf_converter.py
# 비PDF 문서를 PDF로 변환하는 표준 모듈


from PIL import Image
from docx2pdf import convert
import olefile
import win32com.client as win32
import os
import win32gui

def images_to_pdf(image_paths: list[str], output_path: str) -> str:
    """여러 장의 이미지를 하나의 PDF로 묶어서 생성"""
    first = Image.open(image_paths[0]).convert("RGB")
    pages = []

    for img_path in image_paths[1:]:
        pages.append(Image.open(img_path).convert("RGB"))

    first.save(output_path, "PDF",
               save_all=True,
               append_images=pages,
               resolution=200)

    return output_path

# hwp to pdf : 잠정보류
# LibreOffice : 웹 변환 오류 빈번하게 발생 -> 재도전 필요
# hwp5txt : 리눅스 환경 권장(윈도우 오류남)
# win32 : 웹 배포 시 서버에 한글파일 깔아야 함으로 불가.
# def hwp_to_pdf(input_path:str, output_path: str) -> str:
#     #한글파일 열기 위한 함수저장
    # hwp = win32.Dispatch('HWPFrame.HwpObject')
    # hwnd = win32gui.FindWindow(None,'빈 문서 1 - 한글')
    # win32gui.ShowWindow(hwnd,0)
    # hwp.RegisterModule('FilePathCheckDLL','FilePathCheckerModule')
    # hwp.Open(os.path.join(input_path))
    # hwp.Haction.GetDefault('FileSaveAsPdf',hwp.HParameterSet.HFileOpenSave.HSet)
    # hwp.HParameterSet.HFileOpenSave.filename - os.path.join(input_path.replace('.hwp','pdf'))
    # hwp.HAction.Execute("FileSaveAsPdf",hwp.HParameterSet.HFileOpenSave.HSet)



# doc/docx -> pdf 
def doc_to_pdf(input_path: str, output_path: str) -> str:
    return convert(input_path, output_path)


 
