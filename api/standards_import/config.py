"""Configuration parameters specific to the standards import API.

Kept separate from `common.config.settings` because the staging database only
exists for this app — the other three apps must not carry a dependency on it.
"""

import os

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class StandardsImportSettings(BaseSettings):
    """Settings for the standards import API, loaded from the shared `.env`."""

    app_root_dir: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))

    model_config = SettingsConfigDict(
        env_file=f"{app_root_dir}/.env",
        extra="ignore",
        case_sensitive=False,
    )

    staging_neo4j_dsn: str = Field(
        default="",
        validation_alias=AliasChoices("STANDARDS_IMPORT_STAGING_DSN", "NEO4J_DSN"),
        description="DSN of the CDISC staging database, same format as NEO4J_DSN "
        "(bolt://user:password@host:port/database). Falls back to NEO4J_DSN when "
        "STANDARDS_IMPORT_STAGING_DSN is not set. This database is durable and "
        "owned by this app: analysing a new package needs the state left by previous ones.",
    )
    staging_connection_lifetime: float = 29 * 60
    staging_liveness_check_timeout: float = 5 * 60

    max_package_file_bytes: int = Field(
        default=64 * 1024 * 1024,
        ge=0,
        description="Maximum accepted size of an uploaded CDISC package JSON file. "
        "The largest package in the current CDISC set is around 14 MB.",
    )
    staging_batch_size: int = Field(
        default=1000,
        gt=0,
        description="Number of rows per UNWIND batch when writing to the staging database.",
    )
    semantic_provider: str = Field(
        default="",
        alias="STANDARDS_IMPORT_SEMANTIC_PROVIDER",
        description="Dotted path to the callable that asks a language model whether a "
        "CDISC term duplicates a sponsor one under a different name, as "
        "`package.module:name`. Empty — the default — turns the check off entirely, and "
        "everything else still works. The shipped implementation is "
        "`standards_import.services.semantic_provider:http_chat_provider`, which speaks "
        "the OpenAI chat-completions shape; see the README for writing your own.",
    )
    semantic_gateway_url: str = Field(
        default="",
        alias="STANDARDS_IMPORT_SEMANTIC_GATEWAY_URL",
        description="Base URL of the LLM gateway, for the shipped provider.",
    )
    semantic_api_key: str = Field(
        default="",
        alias="STANDARDS_IMPORT_SEMANTIC_API_KEY",
        description="Bearer token for the gateway, for the shipped provider.",
    )
    semantic_model: str = Field(
        default="",
        alias="STANDARDS_IMPORT_SEMANTIC_MODEL",
        description="Model id to ask. Recorded on every finding the check raises, because "
        "an answer is only meaningful against the model that gave it.",
    )
    semantic_timeout_seconds: float = Field(
        default=900,
        alias="STANDARDS_IMPORT_SEMANTIC_TIMEOUT_SECONDS",
        gt=0,
        description="Per-request timeout. Generous: the prompt asks the model to reason "
        "through every added term before answering, and that is worth ten points of "
        "recall.",
    )
    semantic_max_tokens: int = Field(
        default=16000,
        alias="STANDARDS_IMPORT_SEMANTIC_MAX_TOKENS",
        gt=0,
        description="Completion budget, large enough for that reasoning plus the JSON.",
    )

    cdisc_api_base_url: str = Field(
        default="",
        alias="STANDARDS_IMPORT_CDISC_API_BASE_URL",
        description="Base URL of the CDISC Library API, used to discover which controlled "
        "terminology releases CDISC has published, for example "
        "`https://api.library.cdisc.org/api`. Empty — the default — turns discovery off, "
        "and the endpoint says so rather than guessing; uploading package files by hand "
        "works exactly as before either way.",
    )
    cdisc_api_timeout_seconds: float = Field(
        default=30,
        alias="STANDARDS_IMPORT_CDISC_API_TIMEOUT_SECONDS",
        gt=0,
        description="Per-request timeout for the CDISC Library API. Short, unlike the "
        "semantic one: discovery reads a single small list, and a call that hangs should "
        "fail the request rather than hold it open.",
    )

    job_stale_after_seconds: float = Field(
        default=4 * 60 * 60,
        gt=0,
        description="How old a RUNNING job (import, analysis, sponsor impact "
        "assessment, or discovery) must be before startup treats it as abandoned. "
        "Every kind runs in a background task, so it cannot outlive the process that "
        "started it — but with several workers a restart of one must not fail a job "
        "still running in another, hence the age threshold rather than clearing every "
        "RUNNING job outright. Comfortably longer than a real run of any of them.",
    )


settings = StandardsImportSettings()
