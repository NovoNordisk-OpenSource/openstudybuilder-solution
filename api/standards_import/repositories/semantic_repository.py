"""Answers a language model has already given, so the same question is not paid for twice.

Assessing a release is not a one-off. The import refuses a release analysed more recently
than it was assessed, and analysis is re-run every time a review item is settled — so the
ordinary shape of a release is analyse, assess, settle, re-analyse, re-assess, and each of
those assessments would otherwise re-ask the model everything it asked last time.

**The prompt is the cache key, which is what makes this exact rather than approximate.**
It is a pure function of the codelist's name, the terms this release adds to it with their
settled names, submission values and definitions, and the sponsor terms already in it with
theirs — all in a stable order — and the provider is asked at temperature zero. So an
identical prompt has an identical answer, and a prompt that differs by so much as one
settled name is a different question that has to be put again.

The provider path and model id are part of the key too. Swapping either is asking somebody
else, and their answer is not interchangeable with the one on file.

What is stored is the **raw reply**, not the candidates parsed out of it. Re-parsing is
free and pure, so an improvement to the parser reaches every answer already on file
instead of only the ones asked after it.

Rows accumulate at roughly one per codelist per release — tens per quarter, and only for
codelists the sponsor has extended. There is deliberately no expiry: an entry is dead the
moment its prompt cannot recur, and reclaiming that space has never been worth a job.
"""

import hashlib
import logging
from typing import Any

from standards_import.repositories.staging_db import StagingSession, run_query

log = logging.getLogger(__name__)


def answer_key(provider_path: str, model: str, prompt: str) -> str:
    """Digests everything that decides what the answer would be.

    Hashed rather than readable, unlike the finding uids: a prompt runs to thousands of
    characters and nobody reads this one, they read the reply it points at.
    """

    material = f"{provider_path}\n{model}\n{prompt}"
    return hashlib.sha256(material.encode()).hexdigest()


def get_answers(session: StagingSession, keys: list[str]) -> dict[str, str]:
    """The replies already on file for these keys. Missing keys are simply absent."""

    if not keys:
        return {}

    records = run_query(
        session,
        """
        MATCH (answer:SemanticAnswer)
        WHERE answer.uid IN $keys
        RETURN answer.uid AS uid, answer.reply AS reply
        """,
        parameters={"keys": keys},
    )
    return {record["uid"]: record["reply"] for record in records}


def save_answers(session: StagingSession, answers: list[dict[str, Any]]) -> None:
    """Files what the model said, against the question that produced it.

    `asked_at` is refreshed on every write so that a question being asked again — after a
    `refresh`, say — is visible as recent rather than looking like the original answer.
    The codelist is recorded for readability only; it is not part of the key, because the
    prompt already names it.
    """

    if not answers:
        return

    run_query(
        session,
        """
        UNWIND $answers AS row
        MERGE (answer:SemanticAnswer:CDISCStaging {uid: row.uid})
        SET answer.reply = row.reply,
            answer.model = row.model,
            answer.provider = row.provider,
            answer.codelist_id = row.codelist_id,
            answer.asked_at = datetime()
        """,
        parameters={"answers": answers},
    )
