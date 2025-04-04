FROM python:3.10-slim

# 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
    build-essential \
    ffmpeg \
    libmagic-dev \
    cargo \
    && apt-get clean

# 작업 디렉토리
WORKDIR /app

# 프로젝트 전체 복사
COPY . .

# pip 최신화 + 패키지 설치
RUN pip install --upgrade pip \
 && pip install -r requirements.txt

# Streamlit 실행
CMD ["streamlit", "run", "src/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
