"""The one place this app talks to a language model, and the seam for replacing it.

Everything about the semantic check that is *ours* — which codelists are worth asking
about, the prompt, and reading the answer back — lives in `semantic_matching` and is the
same everywhere. What is not ours is the part every organisation running
OpenStudyBuilder will have differently: which gateway, authenticated how, with what
request body, and where in the reply the text is.

So the seam is exactly one callable, `SemanticProvider`:

    Callable[[str], str]

A prompt goes in, the model's reply comes back as text. Nothing else crosses. That is
narrow on purpose — replacing it is twenty lines, and none of the measured behaviour
(the prompt, the `Nxx`/`Exx` protocol, the parsing) can drift while you do it.

Point `STANDARDS_IMPORT_SEMANTIC_PROVIDER` at your own `module:function` and it is used
instead of the one below. Unset — the default — the check does not run at all, and every
other part of the sponsor impact assessment works exactly as it does now.

The shipped provider speaks the OpenAI chat-completions shape over a bearer token, which
is what most gateways in front of a hosted model accept. If yours wants a different body,
a different header, or the reply somewhere other than
`choices[0].message.content`, write your own rather than bending this one.
"""

import importlib
import logging
from collections.abc import Callable

from common.exceptions import ValidationException
from standards_import.config import settings

log = logging.getLogger(__name__)

SemanticProvider = Callable[[str], str]

SHIPPED_PROVIDER = "standards_import.services.semantic_provider:http_chat_provider"


def http_chat_provider(prompt: str) -> str:
    """One completion from an OpenAI-chat-shaped gateway.

    `temperature` is zero so that re-assessing a release does not quietly produce a
    different set of candidates from the same inputs — a finding that came and went on its
    own would be worse than no finding at all.

    Imported here rather than at module scope: `httpx` is only needed by the one path that
    actually talks to a gateway, and an installation with the check switched off should
    not pay for it.
    """

    import httpx  # pylint: disable=import-outside-toplevel

    ValidationException.raise_if_not(
        settings.semantic_gateway_url and settings.semantic_model,
        msg="The shipped semantic provider needs "
        "STANDARDS_IMPORT_SEMANTIC_GATEWAY_URL and STANDARDS_IMPORT_SEMANTIC_MODEL.",
    )

    headers = {}
    if settings.semantic_api_key:
        headers["Authorization"] = f"Bearer {settings.semantic_api_key}"

    with httpx.Client(
        base_url=settings.semantic_gateway_url,
        headers=headers,
        timeout=settings.semantic_timeout_seconds,
    ) as client:
        response = client.post(
            "v1/chat/completions",
            json={
                "model": settings.semantic_model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": settings.semantic_max_tokens,
                "temperature": 0,
            },
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]


def load_provider() -> SemanticProvider | None:
    """The configured provider, or None where the check is switched off.

    A dotted path rather than a registry, so adapting this to another gateway means adding
    a module of your own and naming it — never editing or forking this file.

    A path that cannot be imported is a configuration mistake and says so, loudly, at the
    point somebody asked for the check. It is not treated as "switched off": silently
    skipping a check the operator asked for is how a release gets a clean bill of health
    nobody earned.
    """

    path = settings.semantic_provider.strip()
    if not path:
        return None

    module_name, separator, attribute = path.partition(":")
    ValidationException.raise_if_not(
        separator and attribute,
        msg=f"STANDARDS_IMPORT_SEMANTIC_PROVIDER is '{path}', which is not a "
        "`package.module:callable` path.",
    )

    try:
        provider = getattr(importlib.import_module(module_name), attribute)
    except (ImportError, AttributeError) as exc:
        raise ValidationException(
            msg=f"The semantic provider '{path}' could not be loaded: {exc}. Fix it or "
            "unset STANDARDS_IMPORT_SEMANTIC_PROVIDER to turn the check off."
        ) from exc

    ValidationException.raise_if_not(
        callable(provider), msg=f"The semantic provider '{path}' is not callable."
    )
    return provider
