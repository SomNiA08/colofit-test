FROM python:3.13-slim

WORKDIR /app

# 시스템 의존성
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스 코드 복사
COPY . .

# 포트 (Railway는 $PORT 환경변수로 동적 포트 사용)
EXPOSE $PORT

# 실행
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
