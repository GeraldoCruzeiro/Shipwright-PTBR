#!/usr/bin/env python3
r"""
Audita o mapeamento de falas PT-BR -> personagem.

Exemplos:
    py scripts\ptbr_dubbing\dialogue_map.py --summary
    py scripts\ptbr_dubbing\dialogue_map.py --range 1000 1030
    py scripts\ptbr_dubbing\dialogue_map.py --speaker navi

O arquivo speaker_map.json aceita:
    "1000": "navi"       -> todas as páginas do textId
    "1000:01": "navi"    -> somente a página 01 (sobrescreve o ID)
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

ENTRY_RE = re.compile(
    r'\{\s*(0x[0-9A-Fa-f]+),\s*R"PTBR\((.*?)\)PTBR",\s*0x[0-9A-Fa-f]+\s*\}',
    re.DOTALL,
)
PAGE_BREAK_RE = re.compile(r"<BOX_BREAK(?:_DELAYED:[^>]*)?>")
TAG_RE = re.compile(r"<[^>]+>")
SPACE_RE = re.compile(r"\s+")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_id(value: str) -> int:
    value = value.strip()
    if value.lower().startswith("0x"):
        return int(value, 16)
    return int(value, 16)


def clean_text(tokens: str) -> str:
    text = tokens.replace("<NEWLINE>", " ")
    text = TAG_RE.sub(" ", text)
    return SPACE_RE.sub(" ", text).strip()


def load_messages(root: Path) -> dict[int, list[str]]:
    ptbr = root / "soh" / "soh" / "Enhancements" / "PTBR"
    result: dict[int, list[str]] = {}

    for path in sorted(ptbr.glob("PTBRData_*.cpp")):
        content = path.read_text(encoding="utf-8")
        for match in ENTRY_RE.finditer(content):
            text_id = int(match.group(1), 16)
            raw = match.group(2)
            result[text_id] = [
                clean_text(page)
                for page in PAGE_BREAK_RE.split(raw)
            ]

    return result


def speaker_for(
    mapping: dict[str, str],
    text_id: int,
    page: int,
) -> str | None:
    id_key = f"{text_id:04X}"
    page_key = f"{text_id:04X}:{page:02d}"
    return mapping.get(page_key) or mapping.get(id_key)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audita o mapa de dublagem PT-BR por textId/página."
    )
    parser.add_argument("--summary", action="store_true")
    parser.add_argument(
        "--range",
        nargs=2,
        metavar=("INICIO", "FIM"),
        help="Mostra uma faixa hexadecimal de textIds. Ex.: --range 1000 1030",
    )
    parser.add_argument(
        "--speaker",
        help="Lista páginas atribuídas ao personagem. Ex.: --speaker navi",
    )
    args = parser.parse_args()

    root = repo_root()
    messages = load_messages(root)

    map_path = Path(__file__).with_name("speaker_map.json")
    cast_path = Path(__file__).with_name("voice_cast.json")

    data = load_json(map_path)
    mapping: dict[str, str] = data.get("entries", {})
    cast: dict[str, Any] = load_json(cast_path) if cast_path.exists() else {}

    total_pages = 0
    voiced_pages = 0
    no_dub_pages = 0
    missing_speakers: set[str] = set()

    rows: list[tuple[int, int, str | None, str]] = []
    for text_id in sorted(messages):
        for page, text in enumerate(messages[text_id]):
            total_pages += 1
            speaker = speaker_for(mapping, text_id, page)
            if speaker == "__no_dub__":
                no_dub_pages += 1
            elif speaker:
                voiced_pages += 1
                if speaker not in cast:
                    missing_speakers.add(speaker)
            rows.append((text_id, page, speaker, text))

    if args.range:
        start = parse_id(args.range[0])
        end = parse_id(args.range[1])
        for text_id, page, speaker, text in rows:
            if start <= text_id <= end:
                if speaker == "__no_dub__":
                    who = "NAO_DUBLAR"
                else:
                    who = speaker or "NAO_MAPEADO"
                print(
                    f"{text_id:04X}:{page:02d} | "
                    f"{who:24s} | {text}"
                )
        return 0

    if args.speaker:
        wanted = args.speaker.strip().lower()
        for text_id, page, speaker, text in rows:
            if speaker == wanted:
                print(f"{text_id:04X}:{page:02d} | {text}")
        return 0

    # --summary é também o comportamento padrão.
    print(f"Mensagens PT-BR: {len(messages)}")
    print(f"Páginas de diálogo/texto: {total_pages}")
    classified_pages = voiced_pages + no_dub_pages
    print(f"Páginas com voz/personagem: {voiced_pages}")
    print(f"Páginas marcadas como NÃO DUBLAR: {no_dub_pages}")
    print(f"Páginas classificadas no total: {classified_pages}")
    print(f"Páginas ainda não mapeadas: {total_pages - classified_pages}")
    print(f"Personagens no elenco: {len(cast)}")
    print(f"Entradas no speaker_map: {len(mapping)}")

    if missing_speakers:
        print(
            "ERRO - speakers sem voz no voice_cast.json: "
            + ", ".join(sorted(missing_speakers))
        )
        return 2

    print("Integridade do mapa: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
