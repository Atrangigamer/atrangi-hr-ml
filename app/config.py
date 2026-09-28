"""Validated deployment settings; no model downloads occur during requests."""

from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Read ML_ environment variables once when constructing the application."""

    model_config = SettingsConfigDict(env_prefix="ML_", extra="ignore", hide_input_in_errors=True)
    llm_provider: Literal["local", "openai", "gemini", "antigravity"] = "local"
    antigravity_model: str = "gemini-3.7-flash"
    antigravity_token_budget: int = Field(default=8192, ge=2048, le=32768)
    gemini_api_key: SecretStr | None = Field(default=None, repr=False)
    gemini_model: str = "gemini-3.8-flash"
    gemini_max_tokens: int = Field(default=8192, ge=1024, le=32768)
    openai_api_key: SecretStr | None = Field(default=None, repr=False)
    openai_model: str = "gpt-4o-mini"
    openai_timeout: float = Field(default=90, gt=0, le=300)
    llm_model_path: Path = Path("/models/resume.gguf")
    llm_chat_format: str | None = None
    llm_context: int = Field(default=4096, ge=2048, le=32768)
    llm_max_tokens: int = Field(default=1024, ge=256, le=4096)
    llm_attempts: int = Field(default=2, ge=1, le=3)
    embedding_model: str = "/models/embedding"
    # A single llama.cpp context cannot be called concurrently. Keep this at one.
    gpu_concurrency: int = Field(default=1, ge=1, le=1)
    gpu_queue_timeout: float = Field(default=30.0, gt=0, le=600)
    pdf_concurrency: int = Field(default=2, ge=1, le=8)
    max_active_requests: int = Field(default=4, ge=1, le=128)
    max_pdf_bytes: int = Field(default=10 * 1024 * 1024, ge=1024)
    max_pdf_pages: int = Field(default=20, ge=1, le=100)
    max_resume_chars: int = Field(default=24000, ge=100, le=100000)

    @model_validator(mode="after")
    def valid_context(self) -> "Settings":
        """Reserve space for both the extraction schema and model output."""
        if self.llm_provider in ("openai", "gemini", "antigravity"):
            key = self.gemini_api_key if self.llm_provider in ("gemini", "antigravity") else self.openai_api_key
            if key is None or not key.get_secret_value().strip():
                raise ValueError("Selected cloud provider requires a nonblank API key")
        if self.llm_provider == "local" and self.llm_max_tokens + 1024 >= self.llm_context:
            raise ValueError("LLM context must exceed output allowance + 1024 tokens")
        return self
