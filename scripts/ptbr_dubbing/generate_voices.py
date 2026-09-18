#!/usr/bin/env python3
"""
Gera arquivos WAV de dublagem PT-BR a partir das mensagens traduzidas do Shipwright.

Uso inicial:
    py scripts\\ptbr_dubbing\\generate_voices.py --text-id 1000

O script:
1. localiza o texto 0x1000 nos PTBRData_*.cpp;
2. separa as paginas em <BOX_BREAK>;
3. remove os tokens de formatacao;
4. gera a voz com edge-tts;
5. converte para WAV PCM 16-bit / 44.1 kHz / mono com ffmpeg;
6. salva diretamente em x64/Release/voices/ptbr.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import shutil
import subprocess
import sys
import tempfile
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


def parse_text_id(value: str) -> int:
    value = value.strip()
    if value.lower().startswith("0x"):
        return int(value, 16)
    # Os IDs do projeto sao tradicionalmente escritos em hexadecimal.
    return int(value, 16)


def load_messages(root: Path) -> dict[int, str]:
    ptbr_dir = root / "soh" / "soh" / "Enhancements" / "PTBR"
    messages: dict[int, str] = {}

    for path in sorted(ptbr_dir.glob("PTBRData_*.cpp")):
        content = path.read_text(encoding="utf-8")
        for match in ENTRY_RE.finditer(content):
            text_id = int(match.group(1), 16)
            messages[text_id] = match.group(2)

    if not messages:
        raise RuntimeError(
            f"Nenhuma mensagem PT-BR encontrada em: {ptbr_dir}"
        )

    return messages


def split_pages(tokens: str) -> list[str]:
    return PAGE_BREAK_RE.split(tokens)


def clean_spoken_text(tokens: str, player_name: str) -> str:
    text = tokens
    text = text.replace("<NEWLINE>", " ")
    text = text.replace("<NAME>", player_name)

    # Escolhas exibidas na caixa nao devem ser lidas como parte da fala do NPC.
    text = text.replace("<TWO_CHOICE>", " ")
    text = text.replace("<THREE_CHOICE>", " ")

    # Os demais tokens controlam cor, velocidade, SFX, icones, fluxo etc.
    text = TAG_RE.sub(" ", text)
    text = SPACE_RE.sub(" ", text).strip()

    # Pequena normalizacao para evitar pausas artificiais.
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    return text


def load_voice_map(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "default": {
                "speaker": "Padrao",
                "voice": "pt-BR-ThalitaMultilingualNeural",
                "rate": "+0%",
                "pitch": "+0Hz",
            },
            "entries": {},
        }

    return json.loads(path.read_text(encoding="utf-8"))


def voice_settings(
    config: dict[str, Any],
    text_id: int,
    page: int,
) -> dict[str, str]:
    default = dict(config.get("default", {}))
    entries = config.get("entries", {})

    id_key = f"{text_id:04X}"
    page_key = f"{text_id:04X}:{page:02d}"

    selected = dict(default)
    if id_key in entries:
        selected.update(entries[id_key])
    if page_key in entries:
        selected.update(entries[page_key])

    selected.setdefault("speaker", "Padrao")
    selected.setdefault("voice", "pt-BR-ThalitaMultilingualNeural")
    selected.setdefault("rate", "+0%")
    selected.setdefault("pitch", "+0Hz")
    return selected


async def synthesize_mp3(
    text: str,
    output_path: Path,
    voice: str,
    rate: str,
    pitch: str,
) -> None:
    try:
        import edge_tts
    except ImportError as exc:
        raise RuntimeError(
            "edge-tts nao esta instalado. Rode: py -m pip install --upgrade edge-tts"
        ) from exc

    communicator = edge_tts.Communicate(
        text=text,
        voice=voice,
        rate=rate,
        pitch=pitch,
    )
    await communicator.save(str(output_path))


def convert_to_wav(mp3_path: Path, wav_path: Path) -> None:
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise RuntimeError(
            "ffmpeg nao foi encontrado no PATH. Feche e reabra o terminal depois da instalacao."
        )

    result = subprocess.run(
        [
            ffmpeg,
            "-y",
            "-loglevel",
            "error",
            "-i",
            str(mp3_path),
            "-ac",
            "1",
            "-ar",
            "44100",
            "-c:a",
            "pcm_s16le",
            str(wav_path),
        ],
        text=True,
        capture_output=True,
    )

    if result.returncode != 0:
        raise RuntimeError(
            "Falha ao converter o audio com ffmpeg:\n" + result.stderr.strip()
        )


async def generate_text_id(
    text_id: int,
    tokens: str,
    config: dict[str, Any],
    output_dir: Path,
    player_name: str,
    overwrite: bool,
    dry_run: bool,
) -> int:
    pages = split_pages(tokens)
    generated = 0

    print(f"\n0x{text_id:04X}: {len(pages)} pagina(s)")

    for page_index, page_tokens in enumerate(pages):
        spoken = clean_spoken_text(page_tokens, player_name)
        settings = voice_settings(config, text_id, page_index)
        output = output_dir / f"{text_id:04X}_{page_index:02d}.wav"

        print(
            f"  [{page_index:02d}] {settings['speaker']} | "
            f"{settings['voice']} | {settings['rate']} | {settings['pitch']}"
        )
        print(f"       {spoken}")
        print(f"       -> {output}")

        if not spoken:
            print("       ignorado: pagina sem texto falado")
            continue

        if output.exists() and not overwrite:
            print("       ignorado: arquivo ja existe (use --overwrite para substituir)")
            continue

        if dry_run:
            continue

        output_dir.mkdir(parents=True, exist_ok=True)

        with tempfile.TemporaryDirectory(prefix="ptbr_voice_") as temp_dir:
            mp3_path = Path(temp_dir) / "voice.mp3"
            await synthesize_mp3(
                spoken,
                mp3_path,
                settings["voice"],
                settings["rate"],
                settings["pitch"],
            )
            convert_to_wav(mp3_path, output)

        generated += 1
        print("       OK")

    return generated


def configured_text_ids(config: dict[str, Any]) -> list[int]:
    ids: set[int] = set()
    for key in config.get("entries", {}).keys():
        id_part = key.split(":", 1)[0]
        try:
            ids.add(int(id_part, 16))
        except ValueError:
            pass
    return sorted(ids)


async def async_main() -> int:
    parser = argparse.ArgumentParser(
        description="Gerador de dublagem PT-BR para Ship of Harkinian."
    )
    parser.add_argument(
        "--text-id",
        action="append",
        default=[],
        help="ID hexadecimal da mensagem. Ex.: 1000 ou 0x1000. Pode repetir.",
    )
    parser.add_argument(
        "--configured",
        action="store_true",
        help="Gera todos os text IDs cadastrados em voice_map.json.",
    )
    parser.add_argument(
        "--name",
        default="Link",
        help="Nome falado quando a mensagem contem <NAME>. Padrao: Link.",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Pasta de saida. Padrao: x64/Release/voices/ptbr.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Substitui WAVs que ja existem.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Mostra o que seria gerado sem criar audio.",
    )
    args = parser.parse_args()

    root = repo_root()
    messages = load_messages(root)

    config_path = Path(__file__).with_name("voice_map.json")
    config = load_voice_map(config_path)

    requested: list[int] = [parse_text_id(value) for value in args.text_id]

    if args.configured:
        requested.extend(configured_text_ids(config))

    requested = sorted(set(requested))

    if not requested:
        parser.error("Informe --text-id 1000 ou use --configured.")

    output_dir = (
        Path(args.output_dir).resolve()
        if args.output_dir
        else root / "x64" / "Release" / "voices" / "ptbr"
    )

    missing = [text_id for text_id in requested if text_id not in messages]
    if missing:
        formatted = ", ".join(f"0x{x:04X}" for x in missing)
        raise RuntimeError(f"Text ID(s) nao encontrado(s): {formatted}")

    total = 0
    for text_id in requested:
        total += await generate_text_id(
            text_id=text_id,
            tokens=messages[text_id],
            config=config,
            output_dir=output_dir,
            player_name=args.name,
            overwrite=args.overwrite,
            dry_run=args.dry_run,
        )

    print(f"\nConcluido. {total} arquivo(s) WAV gerado(s).")
    return 0


def main() -> int:
    try:
        return asyncio.run(async_main())
    except KeyboardInterrupt:
        print("\nCancelado.")
        return 130
    except Exception as exc:
        print(f"\nERRO: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
