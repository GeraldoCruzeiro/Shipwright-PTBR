#!/usr/bin/env python3
r"""
Registra a voz escolhida para um personagem a partir do catálogo local.

Exemplo:
    py scripts\ptbr_dubbing\select_voice.py navi 1

O comando lê:
    dublagem_selecao\navi\catalogo.json

e atualiza:
    scripts\ptbr_dubbing\voice_cast.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: Any) -> None:
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Registra a voz escolhida para um personagem."
    )
    parser.add_argument("character", help="Chave do personagem. Ex.: navi")
    parser.add_argument("number", type=int, help="Número da voz escolhida. Ex.: 1")
    parser.add_argument(
        "--allow-duplicate",
        action="store_true",
        help=(
            "Permite reutilizar uma voice_id já atribuída a outro personagem. "
            "Por padrão isso é bloqueado."
        ),
    )
    args = parser.parse_args()

    root = repo_root()
    character = args.character.strip().lower().replace(" ", "_")
    catalog_path = (
        root / "dublagem_selecao" / character / "catalogo.json"
    )
    cast_path = (
        root / "scripts" / "ptbr_dubbing" / "voice_cast.json"
    )

    if not catalog_path.exists():
        print(
            f"ERRO: catálogo não encontrado: {catalog_path}",
            file=sys.stderr,
        )
        return 1

    catalog = load_json(catalog_path)

    selected = None
    for item in catalog:
        if int(item.get("numero", -1)) == args.number:
            selected = item
            break

    if selected is None:
        print(
            f"ERRO: voz número {args.number:03d} não existe no catálogo "
            f"de {character}.",
            file=sys.stderr,
        )
        return 1

    if cast_path.exists():
        cast = load_json(cast_path)
    else:
        cast = {}

    selected_voice_id = str(selected.get("voice_id") or "").strip()
    if not selected_voice_id:
        print(
            "ERRO: a voz escolhida não possui voice_id válido.",
            file=sys.stderr,
        )
        return 1

    if not args.allow_duplicate:
        for other_character, other_voice in cast.items():
            if other_character == character:
                continue

            other_voice_id = str(
                (other_voice or {}).get("voice_id") or ""
            ).strip()

            if other_voice_id == selected_voice_id:
                print(
                    (
                        "ERRO: esta voz já está atribuída a "
                        f"'{other_character}'. Escolha outra voz para "
                        f"'{character}'."
                    ),
                    file=sys.stderr,
                )
                return 2

    cast[character] = {
        "name": selected.get("name"),
        "voice_id": selected.get("voice_id"),
        "public_owner_id": selected.get("public_owner_id"),
        "arquivo_preview": selected.get("arquivo"),
        "gender": selected.get("gender"),
        "age": selected.get("age"),
        "accent": selected.get("accent"),
        "descriptive": selected.get("descriptive"),
        "use_case": selected.get("use_case"),
        "description": selected.get("description"),
        "free_users_allowed": selected.get("free_users_allowed"),
        "rate": selected.get("rate"),
        "verified_languages": selected.get("verified_languages") or [],
    }

    save_json(cast_path, cast)

    print()
    print(f"Personagem: {character}")
    print(f"Escolha: {args.number:03d}")
    print(f"Voz: {selected.get('name')}")
    print(f"Voice ID: {selected.get('voice_id')}")
    print()
    print(f"Elenco atualizado em: {cast_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
