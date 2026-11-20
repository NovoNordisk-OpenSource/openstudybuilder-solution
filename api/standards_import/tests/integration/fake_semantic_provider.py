"""A semantic provider that answers without a gateway.

Loaded the way a real one is — by dotted path, through
`STANDARDS_IMPORT_SEMANTIC_PROVIDER` — so the tests using it exercise the whole seam,
resolver included, rather than reaching past it. Writing one of these is the entire job of
adapting the check to another LLM backend, which is worth knowing is this small.
"""

import json

# Every prompt this was asked, so a test can assert what was *not* sent as easily as what
# came back. Reset it in any test that reads it; nothing else does.
PROMPTS: list[str] = []

REPLY = json.dumps(
    {
        "pairs": [
            {
                "new": "N00",
                "existing": "E00",
                "confidence": "high",
                "why": "N00 and E00 both name the ANGPTL3/8 complex.",
            }
        ]
    }
)


def pairs_the_first_two(prompt: str) -> str:
    """Always pairs the first added term with the first sponsor one.

    Wrapped in the prose a real model puts around its JSON, because that is the shape
    `extract_pairs` exists to survive.
    """

    PROMPTS.append(prompt)
    return (
        "N00 | angiopoietin-like 3/8 complex | none\n\n"
        f"{REPLY}\n\n"
        "Note: no other pairs were found."
    )


def finds_nothing(prompt: str) -> str:
    PROMPTS.append(prompt)
    return '{"pairs": []}'


def fails(prompt: str) -> str:
    PROMPTS.append(prompt)
    raise RuntimeError("the gateway is having a bad day")


# Whether `flaky` is currently in its bad afternoon. Reset between tests.
FAILING = False


def flaky(prompt: str) -> str:
    """Fails or answers depending on `FAILING`, under one unchanging dotted path.

    Which matters more than it looks: the provider path is part of the cache key, so a
    test that swapped `fails` for `pairs_the_first_two` between two runs would see the
    second run ask again whatever the caching did — and prove nothing about it.
    """

    if FAILING:
        return fails(prompt)
    return pairs_the_first_two(prompt)
