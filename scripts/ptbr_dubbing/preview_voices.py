#!/usr/bin/env python3
r"""
Gera amostras das vozes PT-BR atualmente disponíveis no Edge TTS.

Uso:
    py scripts\ptbr_dubbing\preview_voices.py

Saída:
    dublagem_vozes_teste\*.mp3

O script consulta a lista atual do serviço em vez de depender de nomes
fixos que podem deixar de existir. Para cada voz PT-BR encontrada,
gera quatro variações de timbre usando velocidade e pitch.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

DEFAULT_TEXT = (
    "Link, escute com atenção. Uma grande aventura está prestes a começar."
)

VARIANTS = [
    ("neutra", "+0%", "+0Hz"),
    ("jovem", "+8%", "+20Hz"),
    ("suave", "-3%", "+10Hz"),
    ("grave", "-8%", "-25Hz"),
]


async def generate_sample(
    edge_tts,
    index: int,
    total: int,
    gender: str,
    voice: str,
    variant: str,
    rate: str,
    pitch: str,
    text: str,
    output_dir: Path,
) -> bool:
    safe_gender = gender.lower() if gender else "desconhecida"
    output = output_dir / (
        f"{index:02d}_{safe_gender}_{voice}_{variant}.mp3"
    )

    print(
        f"[{index:02d}/{total:02d}] {voice} | "
        f"{variant} | rate={rate} | pitch={pitch}"
    )

    try:
        communicator = edge_tts.Communicate(
            text=text,
            voice=voice,
            rate=rate,
            pitch=pitch,
        )
        await communicator.save(str(output))
    except Exception as exc:
        print(f"    FALHOU: {exc}")
        return False

    print(f"    OK -> {output.name}")
    return True


async def async_main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Consulta as vozes PT-BR atuais do Edge TTS e gera amostras "
            "com variações de timbre."
        )
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

    print("Consultando as vozes PT-BR disponíveis atualmente...")

    try:
        available = await edge_tts.list_voices()
    except Exception as exc:
        print(f"ERRO ao consultar as vozes: {exc}", file=sys.stderr)
        return 1

    voices = [
        voice
        for voice in available
        if voice.get("Locale") == "pt-BR"
        or str(voice.get("ShortName", "")).startswith("pt-BR-")
    ]

    voices.sort(key=lambda item: str(item.get("ShortName", "")))

    if not voices:
        print("ERRO: nenhuma voz pt-BR foi retornada pelo Edge TTS.")
        return 1

    print(f"Encontradas {len(voices)} voz(es) PT-BR:")
    for voice in voices:
        print(
            f"  - {voice.get('ShortName')} "
            f"({voice.get('Gender', 'desconhecido')})"
        )

    root = Path(__file__).resolve().parents[2]
    output_dir = (
        Path(args.output_dir).resolve()
        if args.output_dir
        else root / "dublagem_vozes_teste"
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    jobs = []
    for voice in voices:
        short_name = str(voice.get("ShortName", "")).strip()
        if not short_name:
            continue

        gender = str(voice.get("Gender", "desconhecida"))
        for variant, rate, pitch in VARIANTS:
            jobs.append(
                (
                    gender,
                    short_name,
                    variant,
                    rate,
                    pitch,
                )
            )

    ok = 0
    total = len(jobs)

    for index, (gender, voice, variant, rate, pitch) in enumerate(
        jobs,
        start=1,
    ):
        if await generate_sample(
            edge_tts=edge_tts,
            index=index,
            total=total,
            gender=gender,
            voice=voice,
            variant=variant,
            rate=rate,
            pitch=pitch,
            text=args.text,
            output_dir=output_dir,
        ):
            ok += 1

    print()
    print(f"Concluído: {ok}/{total} amostras geradas.")
    print(f"Pasta: {output_dir}")
    print()
    print("Escolha as amostras que combinam com:")
    print("  Navi")
    print("  Saria")
    print("  Grande Árvore Deku")
    print("  Mido")
    print("  Zelda")
    print("  Ganondorf")
    print()
    print(
        "Anote o nome completo do arquivo escolhido para cada personagem."
    )

    return 0


def main() -> int:
    try:
        return asyncio.run(async_main())
    except KeyboardInterrupt:
        print("\nCancelado.")
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
