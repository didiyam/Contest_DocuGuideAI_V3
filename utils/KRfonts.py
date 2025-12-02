from matplotlib import rcParams
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt

# 1) 폰트 경로 직접 지정 (예시 경로)
font_path = r"C:\Windows\Fonts\NotoSansKR-Regular.ttf"  # 실제 설치된 경로 확인 필요
font_prop = fm.FontProperties(fname=font_path)

# 2) 전역 설정
rcParams['font.family'] = font_prop.get_name()  # 예: 'Noto Sans KR'
rcParams['axes.unicode_minus'] = False  # 마이너스 깨짐 방지



# plt.plot([1, 2, 3])
# plt.title("테스트")
# plt.show() 
# print("완료") 