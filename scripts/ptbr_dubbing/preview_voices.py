#!/usr/bin/env python3
"""
Gera amostras das vozes PT-BR disponíveis no Edge TTS para escolher o elenco da dublagem.

Uso:
    py scripts\ptbr_dubbing\preview_voices.py

Saída:
    dublagem_vozes_teste\*.mp3
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

VOICES = [
    ("feminina", "pt-BR-ThalitaMultilingualNeural"),
    ("masculina", "pt-BR-MacerioMultilingualNeural"),
    ("feminina", "pt-BR-FranciscaNeural"),
    ("masculina", "pt-BR-AntonioNeural"),
    ("feminina", "pt-BR-BrendaNeural"),
    ("masculina", "pt-BR-DonatoNeural"),
    ("feminina", "pt-BR-ElzaNeural"),
    ("masculina", "pt-BR-FabioNeural"),
    ("feminina", "pt-BR-GiovannaNeural"),
    ("masculina", "pt-BR-HumbertoNeural"),
    ("masculina", "pt-BR-JulioNeural"),
    ("feminina", "pt-BR-LeilaNeural"),
    ("crianca", "pt-BR-LeticiaNeural"),
    ("feminina", "pt-BR-ManuelaNeural"),
    ("masculina", "pt-BR-NicolauNeural"),
    ("feminina", "pt-BR-ThalitaNeural"),
    ("masculina", "pt-BR-ValerioNeural"),
    ("feminina", "pt-BR-YaraNeural"),
]

DEFAULT_TEXT = (
    "Link, escute com atenção. Uma grande aventura está prestes a começar."
)


async def generate_sample(
    edge_tts,
    index: int,
    category: str,
    voice: str,
    text: str,
    output_dir: Path,
) -> bool:
    output = output_dir / f"{index:02d}_{category}_{voice}.mp3"

    print(f"[{index:02d}/{len(VOICES):02d}] {voice}")

    try:
        communicator = edge_tts.Communicate(
            text=text,
            voice=voice,
            rate="+0%",
            pitch="+0Hz",
        )
        await communicator.save(str(output))
    except Exception as exc:
        print(f"    FALHOU: {exc}")
        return False

    print(f"    OK -> {output.name}")
    return True


async def async_main() -> int:
    parser = argparse.ArgumentParser(
        description="Gera amostras das vozes PT-BR para escolher personagens."
    )
    parser.add_argument(
        "--text",
        default=DEFAULT_TEXT,
        help="Texto usado em todas as amostras.",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Pasta de saída. Padrão: <repo>\\dublagem_vozes_teste",
    )
    args = parser.parse_args()

    try:
        import edge_tts
    except ImportError:
        print(
            "ERRO: edge-tts não está instalado. Rode: "
            "py -m pip install --upgrade edge-tts",
            file=sys.stderr,
        )
        return 1

    root = Path(__file__).resolve().parents[2]
    output_dir = (
        Path(args.output_dir).resolve()
        if args.output_dir
        else root / "dublagem_vozes_teste"
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    ok = 0

    for index, (category, voice) in enumerate(VOICES, start=1):
        if await generate_sample(
            edge_tts,
            index,
            category,
            voice,
            args.text,
            output_dir,
        ):
            ok += 1

    print()
    print(f"Concluído: {ok}/{len(VOICES)} vozes geradas.")
    print(f"Pasta: {output_dir}")
    print()
    print("Ouça os arquivos e anote os números que combinam com:")
    print("  Navi")
    print("  Saria")
    print("  Grande Árvore Deku")
    print("  Mido")
    print("  Zelda")
    print("  Ganondorf")

    return 0


def main() -> int:
    try:
        return asyncio.run(async_main())
    except KeyboardInterrupt:
        print("\nCancelado.")
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
