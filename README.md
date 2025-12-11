## [🤖📄 공공문서 요약 및 행동 안내 AI]
# 똑띠DOC
**똑**똑한 **디**지털 **DOC** AI매니저

<img width="3836" height="1802" alt="image" src="https://github.com/user-attachments/assets/a460bc94-1969-4b9c-975a-f3ef9b00ffd2" /><img width="3410" height="2015" alt="image" src="https://github.com/user-attachments/assets/fe8b99e9-83c9-4918-898f-c3d75f3e1433" />


복잡한 공공문서를 업로드하면 AI가 쉽게 설명해주고, 행동지침와 Q&A까지 지원하는 맞춤형 AI Agent 프로젝트입니다.

공공문서를 자동 분석해 핵심 요약과 필요한 행동 정보를 제공하고,  
OCR → 전처리 → 정제(PII 마스킹) → 임베딩 → RAG 검색까지 이어지는  
완전한 공공문서 안내 경험을 제공하는 서비스입니다.

---

## Tech Stack

### Frontend
- Next.js (App Router, TypeScript)
- Tailwind CSS
- Framer Motion
- Lucide Icons

### Backend
- FastAPI (Python)
- SQLite 기반 벡터DB (문서 단위 메타데이터 저장)
- OpenAI GPT API  
  - **Vision OCR:** gpt-4o-mini  
  - **텍스트 정제 & 개인정보 마스킹:** gpt-4.1-mini  
  - **임베딩:** text-embedding-3-small
- PyMuPDF(fitz) 기반 PDF → 이미지 변환
- clean-text / 정규식 기반 전처리
- NER 기반 행동 정보 추출

---

## 프로젝트 구조

## 📁 프로젝트 구조

```
DocuGuideAI/
├─ src/
│  ├─ analyze/           # 행동 정보 추출(NER), 요약 등 분석 로직
│  ├─ app/               # FastAPI 엔드포인트(router) 및 서버 실행부
│  ├─ chatbot/           # RAG 기반 질의응답 엔진
│  ├─ ingestion/         # OCR → 전처리(clean-text) → LLM 정제 → PII 마스킹
│  ├─ result/            # 최종 요약, 행동 안내(To-Do) 결과 생성
│  ├─ utils/             # 공통 유틸(로거, 설정, 공통 함수 등)
│  └─ __init__.py
│
├─ utils/                # (중복 유틸 폴더 – 공용 스크립트/실행툴이 위치하는 경우)
│
├─ web/                  # 프론트엔드(Next.js)
│  ├─ app/               # Next.js App Router 페이지
│  ├─ components/        # UI 컴포넌트
│  ├─ hooks/             # 커스텀 훅
│  ├─ lib/               # API 호출 및 클라이언트 유틸
│  └─ public/            # 정적 assets
│
├─ storage/
│  └─ rag_db.sqlite      # SQLite 벡터DB (문서 단위 임베딩 저장)
│
├─ .env                  # 환경 변수
├─ README.md
├─ requirements.txt
└─ 기타 설정 파일 (.vscode, .gitignore 등)
```


---

## 실행 방법

### Backend 실행

```
pip install -r requirements.txt
uvicorn src.app.main:app --reload --host 127.0.0.1 --port 8000
```

API Docs → http://localhost:8000/docs

### Frontend 실행

```
cd web
npm install
npm run dev
```

Frontend → http://localhost:3000

### 환경 변수 설정

```
NEXT_PUBLIC_API_BASE=http://localhost:8000
```

---

## 문서 처리 전체 흐름

### 1) PDF → 이미지(OCR 입력용)
- PyMuPDF(fitz)를 사용해 PDF 페이지를 PNG(base64)로 변환
- 해상도(DPI)를 조정해 OCR 품질을 최적화

### 2) Vision OCR (gpt-4o-mini)
- 각 페이지를 GPT Vision 모델로 OCR
- 의미를 변경하지 않으며 문단, 항목, 형식 구조를 최대한 복원
- 해설/요약 없이 “텍스트만” 출력

### 3) clean-text + 정규식 기반 전처리
- OCR 특유의 잡음 노이즈 제거  
  (여백, 개행 오류, 불필요한 특수문자)
- 텍스트 의미를 바꾸지 않는 최소한의 정규화 수행  
  → LLM 정제가 더 안정적으로 동작하도록 사전 정돈 단계

### 4) LLM 정제(gpt-4.1-mini) + 개인정보(PII) 마스킹
- 공공문서 스타일로 자연스럽게 문서를 재구성
- 개인 정보만 선별적으로 마스킹
  - 개인 전화번호 → `[전화번호비공개]`
  - 개인 이메일 → `[이메일비공개]`
  - 개인 주소 → `[주소비공개]`
  - 주민번호/식별번호 → `[식별번호비공개]`
- 공공기관 주소/전화/이메일은 마스킹하지 않음

### 5) NER 기반 행동 정보 추출
문서에서 다음 요소 자동 구조화:
- 주체(who)
- 행동(action)
- 기한(when)
- 장소(where)
- 방법(how)

출력된 요소는 다시 사람이 보기에 쉬운 To-Do 리스트로 재구성됨.

### 6) 벡터 임베딩 & SQLite 저장
- 행동 정보와 페이지 텍스트를 각각 임베딩(text-embedding-3-small)
- SQLite에 다음 구조로 저장:

```
id, doc_id, type(action/page), page_num, text, embedding(BLOB), metadata(JSON)
```

- 문서 단위 검색 공간 분리  
  → “이 문서 안에서만” 정확한 근거 기반 검색 가능

### 7) RAG 기반 질의응답
- cosine similarity로 가장 유사한 문장 검색
- GPT가 “근거 기반 + bullet 구조”로 답변 생성  
- hallucination을 최소화하는 필터링 프롬프트 적용

---

## OCR 핵심 코드 요약

### PDF → base64 변환

```
pix = page.get_pixmap(matrix=mat)
img_bytes = pix.tobytes("png")
img_b64 = base64.b64encode(img_bytes).decode("utf-8")
```

### Vision OCR

```
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[ ... OCR 규칙 + 이미지 ... ]
)
```

### PII 마스킹 정제

```
resp = client.chat.completions.create(
    model="gpt-4.1-mini",
    messages=[ ... PII 규칙 ... ]
)
```

---

## RAG 구조 요약

- **임베딩 모델:** text-embedding-3-small  
- **저장소:** SQLite + BLOB(embedding) + metadata(JSON)  
- **검색 방식:** cosine similarity  
- **답변 원칙:** 근거 기반, bullet 중심, 불확실한 정보 차단  

---

## 한계 및 개선 예정

- HWP 문서 파싱 안정성 개선 필요  
- Vision OCR 비용 최적화  
- 다양한 문서 포맷 조건에 대한 규칙 개선  
- 전자고지(PASS) 자동 연동 기능 추가 예정  

---

## 프로젝트 목적

공공문서를 이해하기 어려운 사용자도  
핵심 내용과 필요한 행동을 즉시 파악하고  
실수 없이 처리할 수 있도록 돕는  
**사용자 중심 공공문서 안내 AI**를 구축하는 것이 목표입니다.
