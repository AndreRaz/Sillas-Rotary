from __future__ import annotations

import re
import unicodedata
from typing import Optional


def normalize_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    compact = re.sub(r"\s+", " ", str(value).strip())
    if not compact:
        return None
    upper = compact.upper()
    nfd = unicodedata.normalize("NFD", upper)
    no_diacritics = "".join(ch for ch in nfd if unicodedata.category(ch) != "Mn")
    return no_diacritics
