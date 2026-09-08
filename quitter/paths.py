"""Waar de spullen staan. Eén plek, zodat agents niet gaan raden."""

from __future__ import annotations

from pathlib import Path

WORTEL = Path(__file__).resolve().parent.parent

DOCS = WORTEL / "docs"
SITE = WORTEL / "site"
CONTENT = WORTEL / "content"
DATA = WORTEL / "data"

# Mappen waarin agents mogen schrijven. Alles daarbuiten is verboden terrein:
# een agent mag de website vullen, niet zijn eigen broncode herschrijven.
SCHRIJFBAAR = (CONTENT, SITE, DATA)
LEESBAAR = (CONTENT, SITE, DATA, DOCS)


def _binnen(pad: Path, toegestaan: tuple[Path, ...]) -> bool:
    pad = pad.resolve()
    return any(pad == m or m in pad.parents for m in toegestaan)


def veilig_pad(relatief: str, *, schrijven: bool) -> Path:
    """Zet een relatief pad om naar een absoluut pad, of weiger het."""
    pad = (WORTEL / relatief).resolve()
    toegestaan = SCHRIJFBAAR if schrijven else LEESBAAR
    if not _binnen(pad, toegestaan):
        mappen = ", ".join(m.name for m in toegestaan)
        raise PermissionError(
            f"'{relatief}' ligt buiten de toegestane mappen ({mappen})."
        )
    return pad
