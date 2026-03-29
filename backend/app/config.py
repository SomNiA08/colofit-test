from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    app_name: str = "ColorFit API"
    app_version: str = "0.1.0"
    debug: bool = False

    # Database
    database_url: str = ""

    # Gemini
    gemini_api_key: str = ""

    # Naver Shopping
    naver_client_id: str = ""
    naver_client_secret: str = ""

    # CORS — Railway 환경변수에서 JSON 배열로 추가 가능
    # 예: ALLOWED_ORIGINS=["https://your-app.vercel.app","http://localhost:3000"]
    allowed_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
