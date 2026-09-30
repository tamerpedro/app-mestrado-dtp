import json
import re
from pathlib import Path

from src.i18n import LANGUAGES, normalize_language, t

LOCALES = Path(__file__).resolve().parent.parent / "locales"
PLACEHOLDER = re.compile(r"{(\w+)}")


def _catalog(lang: str) -> dict[str, str]:
    return json.loads((LOCALES / f"{lang}.json").read_text(encoding="utf-8"))


def test_catalogs_have_the_same_keys():
    keys = {lang: set(_catalog(lang)) for lang in LANGUAGES}
    assert keys["pt"] == keys["en"], keys["pt"] ^ keys["en"]


def test_catalogs_have_no_empty_values_and_matching_placeholders():
    pt, en = _catalog("pt"), _catalog("en")
    for key in pt:
        assert pt[key].strip() and en[key].strip(), key
        assert set(PLACEHOLDER.findall(pt[key])) == set(PLACEHOLDER.findall(en[key])), key


def test_every_key_used_in_code_exists():
    source = "\n".join(path.read_text(encoding="utf-8") for path in [Path("app.py"), *Path("src").glob("*.py")])
    used = set(re.findall(r"\btr?\(\s*\"([a-z_]+\.[a-z0-9_.]+)\"", source))
    missing = used - set(_catalog("pt"))
    assert used and not missing, missing


def test_t_formats_and_falls_back():
    assert t("manual.added", "en", id="MAN001") == "Risk MAN001 added for review."
    assert t("manual.added", "xx", id="MAN001") == "Risco MAN001 adicionado para revisão."
    assert t("chave.inexistente", "en") == "chave.inexistente"
    assert normalize_language("EN") == "en"
    assert normalize_language("es") == "pt"
