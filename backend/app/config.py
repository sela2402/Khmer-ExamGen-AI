from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    llm_api_key: str = ""
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o-mini"
    database_path: str = "examgen.sqlite3"
    max_upload_mb: int = 20
    khmer_font_path: str = ""
    supabase_url: str = ""
    supabase_publishable_key: str = ""
    supabase_jwks_url: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
