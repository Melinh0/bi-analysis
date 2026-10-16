from pydantic_settings import BaseSettings
from pydantic import Field, computed_field
from typing import Any, Mapping, Optional
from pathlib import Path
import re


def get_project_root() -> Path:

    return Path(__file__).parent.parent.parent.parent


class Settings(BaseSettings):
    app_name: str = "BI Analysis"
    app_version: str = "0.2.0"
    debug: bool = True


    database_path: str = Field(default="data/bi_analysis.db", alias="DATABASE_PATH")
    vector_store_path_rel: str = Field(default="data/vector_store", alias="VECTOR_STORE_PATH")

    @computed_field
    @property
    def database_url(self) -> str:

        root = get_project_root()
        db_path = root / self.database_path
        db_path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{db_path}"

    @computed_field
    @property
    def vector_store_path(self) -> str:

        root = get_project_root()
        vs_path = root / self.vector_store_path_rel
        vs_path.mkdir(parents=True, exist_ok=True)
        return str(vs_path)

    ollama_api_key: str = Field(default="", alias="OLLAMA_API_KEY")
    ollama_base_url: str = Field(default="https://api.ollama.com", alias="OLLAMA_BASE_URL")
    ollama_model: str = Field(default="gemma4:cloud", alias="OLLAMA_MODEL")
    ollama_embedding_model: str = Field(default="nomic-embed-text", alias="OLLAMA_EMBEDDING_MODEL")
    ollama_available_models: str = Field(
        default="gemma4:cloud,qwen2.5-coder:1.5b-base",
        alias="OLLAMA_AVAILABLE_MODELS"
    )

    instagram_email: Optional[str] = Field(default=None, alias="INSTAGRAM_EMAIL")
    instagram_password: Optional[str] = Field(default=None, alias="INSTAGRAM_PASSWORD")

    chroma_collection_name: str = "bi_analysis_documents"
    embedding_batch_size: int = 100
    chunk_size: int = 1000
    chunk_overlap: int = 200
    top_k_retrieval: int = 5

    web_host: str = "0.0.0.0"
    web_port: int = 8000

    log_level: str = "INFO"

    class Config:
        env_file = get_project_root() / ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


settings = Settings()


def get_settings() -> Settings:
    return settings


def get_env_file() -> Path:

    return get_project_root() / ".env"


def _env_key_for(field_name: str) -> str:

    field = Settings.model_fields.get(field_name)
    if field is not None and field.alias:
        return str(field.alias)
    return field_name.upper()


def _format_env_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return ""
    text = str(value)
    if re.fullmatch(r"-?\d+(\.\d+)?", text):
        return text
    escaped = text.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def persist_settings(updates: Mapping[str, Any]) -> Path:

    env_path = get_env_file()
    wanted = {
        _env_key_for(name).upper(): _format_env_value(value)
        for name, value in updates.items()
    }

    lines = env_path.read_text(encoding="utf-8").splitlines() if env_path.exists() else []
    new_lines = []
    written = set()
    for line in lines:
        match = re.match(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=", line)
        key = match.group(1).upper() if match else None
        if key in wanted:
            if key in written:
                continue
            written.add(key)
            new_lines.append(f"{match.group(1)}={wanted[key]}")
        else:
            new_lines.append(line)
    for key, value in wanted.items():
        if key not in written:
            new_lines.append(f"{key}={value}")

    env_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = env_path.with_name(env_path.name + ".tmp")
    tmp_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    tmp_path.replace(env_path)
    return env_path


def apply_settings(updates: Mapping[str, Any]) -> dict[str, Any]:
    





    unknown = sorted(set(updates) - set(Settings.model_fields))
    if unknown:
        raise ValueError(f"Configurações desconhecidas: {', '.join(unknown)}")

    candidate = Settings(**dict(updates))
    applied = {name: getattr(candidate, name) for name in updates}
    for name, value in applied.items():
        setattr(settings, name, value)
    persist_settings(applied)
    return applied