# 게임 기획서 → Testcase 자동 생성기

게임 기획서(DOCX, PDF)를 업로드하면 AI가 자동으로 testcase를 생성하고, 대/중/소분류로 구분한 뒤 품질을 검증하여 점수와 등급을 매겨 엑셀 파일로 출력하는 웹 서비스입니다.

## 주요 기능

- **문서 업로드 및 파싱**: DOCX, PDF 형식 지원
- **문장 단위 분석**: 문장 단위로 분할 후 테스트케이스 생성에 필요한 문장만 필터링
- **문서 구조 자동 인식**: AI가 문서 내 구조를 분석하여 대/중/소분류 자동 지정
- **Testcase 자동 생성**: 지정된 엑셀 템플릿 형식으로 testcase 생성
- **AI 모델 선택**: Google Gemini 또는 OpenAI GPT-4 Turbo 선택 가능
- **Testcase 품질 검증**: 정확성, 명확성, 중복성, 완전성 기준으로 검증 후 점수화
- **결과 엑셀 파일 출력**: 점수와 등급이 포함된 testcase 엑셀 파일 다운로드 제공

## 설치 방법

```bash
# 저장소 복제
git clone https://github.com/yourusername/test_tc_generator.git
cd test_tc_generator

# 가상환경 생성 및 활성화 (선택사항)
python -m venv venv
source venv/bin/activate  # Windows의 경우: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

## 사용 방법

```bash
# Streamlit 앱 실행
streamlit run src/app.py
```

웹 브라우저에서 `http://localhost:8501`로 접속하여 다음 단계를 따릅니다:

1. 사이드바에서 사용할 AI 모델 선택 (Google Gemini 또는 OpenAI GPT-4 Turbo)
2. 선택한 모델에 해당하는 API 키 입력
3. 게임 기획서 파일(DOCX 또는 PDF) 업로드
4. 자동으로 testcase 생성 프로세스 시작
5. 생성된 testcase 미리보기 확인
6. "Testcase 엑셀 파일 다운로드" 버튼으로 결과 다운로드

## 테스트케이스 채점 기준

- **정확성 (40점)**: 테스트 내용의 정확성, 테스트 조건과 기대 결과의 매칭도
- **명확성 (20점)**: 테스트케이스의 이해 용이성
- **중복성 (20점)**: 다른 테스트케이스와의 중복 여부
- **완전성 (20점)**: 필요한 정보의 완전성

## 등급 기준

- 🟢 **매우 우수** (90~100점)
- 🟡 **보통** (70~89점)
- 🟠 **주의** (50~69점)
- 🔴 **부적합** (50점 미만, 재생성 필요)

## Streamlit Cloud 배포

이 앱은 [Streamlit Cloud](https://streamlit.io/cloud)를 통해 무료로 배포할 수 있습니다:

1. GitHub에 코드 푸시
2. Streamlit Cloud에 로그인
3. "New app" 클릭 후 저장소, 브랜치, 메인 Python 파일(src/app.py) 지정
4. 배포 완료!

## 기술 스택

- **문서처리 및 AI**: LangChain, GPT-4 Turbo, Google Gemini
- **데이터 처리 및 출력**: Pandas, openpyxl
- **웹서비스 UI 및 배포**: Streamlit