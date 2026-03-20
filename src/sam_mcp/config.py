from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    sam_api_key: str = ""
    sam_base_url: str = "https://api.sam.gov"

    @field_validator("sam_api_key")
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        if not v:
            raise ValueError(
                "SAM_API_KEY is not set. "
                "Get a free API key at https://sam.gov/workspace/profile/account-details"
            )
        return v


settings = Settings()
