"""Traducao da interface: ``t("chave", lang, **params)``.

Os textos ficam em ``locales/<idioma>.json``. Chave ausente no idioma pedido
cai para o portugues; ausente nos dois, devolve a propria chave (visivel na
tela e pego pelo teste de completude dos catalogos).
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

LANGUAGES = {"pt": "Português", "en": "English"}
DEFAULT_LANGUAGE = "pt"
LOCALES_DIR = Path(__file__).resolve().parent.parent / "locales"


def normalize_language(lang: str | None) -> str:
    code = (lang or "").strip().lower()[:2]
    return code if code in LANGUAGES else DEFAULT_LANGUAGE


@lru_cache(maxsize=None)
def load_catalog(lang: str) -> dict[str, str]:
    path = LOCALES_DIR / f"{lang}.json"
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def t(key: str, lang: str | None = DEFAULT_LANGUAGE, **params: object) -> str:
    text = load_catalog(normalize_language(lang)).get(key)
    if text is None:
        text = load_catalog(DEFAULT_LANGUAGE).get(key, key)
    return text.format(**params) if params else text
