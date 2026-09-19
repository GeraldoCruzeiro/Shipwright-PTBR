#!/usr/bin/env python3
"""
Gera WAVs de dublagem PT-BR usando o elenco selecionado no ElevenLabs.

Fontes de verdade:
- speaker_map.json: textId/pagina -> personagem ou marcador de runtime
- voice_cast.json: personagem -> voice_id da ElevenLabs
- runtime_voice_variants.json: falantes possiveis nos IDs compartilhados

Exemplos:
    py scripts\\ptbr_dubbing\\generate_voices.py --text-id 1000 --dry-run
    py scripts\\ptbr_dubbing\\generate_voices.py --speaker navi --dry-run
    py scripts\\ptbr_dubbing\\generate_voices.py --all --dry-run
    py scripts\\ptbr_dubbing\\generate_voices.py --estimate
    py scripts\\ptbr_dubbing\\generate_voices.py --text-id 1000 --prosody-pauses --overwrite
    py scripts\\ptbr_dubbing\\generate_voices.py --all --overwrite

Os audios finais sao WAV PCM s16le, 44.1 kHz, mono, salvos em:
    x64/Release/voices/ptbr
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

try:
    from elevenlabs_library import get_api_key
except ImportError:
    from scripts.ptbr_dubbing.elevenlabs_library import get_api_key


ENTRY_RE = re.compile(
    r'\{\s*(0x[0-9A-Fa-f]+),\s*R"PTBR\((.*?)\)PTBR",\s*0x[0-9A-Fa-f]+\s*\}',
    re.DOTALL,
)
PAGE_BREAK_RE = re.compile(r"<BOX_BREAK(?:_DELAYED:[^>]*)?>")
TAG_RE = re.compile(r"<[^>]+>")
SPACE_RE = re.compile(r"\s+")

API_BASE = "https://api.elevenlabs.io/v1/text-to-speech"
DEFAULT_MODEL_ID = "eleven_flash_v2_5"
DEFAULT_OUTPUT_FORMAT = "mp3_44100_128"
NO_DUB = "__no_dub__"
ESTIMATE_CREDITS_PER_CHARACTER = 1.0
DEFAULT_SPEED = 0.87
MAX_PROSODY_BREAKS_PER_PAGE = 8


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def parse_text_id(value: str) -> int:
    value = value.strip()
    if value.lower().startswith("0x"):
        return int(value, 16)
    return int(value, 16)


def load_json(path: Path) -> Any:
    if not path.exists():
        raise RuntimeError(f"Arquivo nao encontrado: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


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


def clean_spoken_text(
    tokens: str,
    player_name: str | None,
) -> str:
    text = tokens

    # Tudo apos o marcador de escolha e UI, nao fala do personagem.
    for marker in ("<TWO_CHOICE>", "<THREE_CHOICE>"):
        if marker in text:
            text = text.split(marker, 1)[0]

    text = text.replace("<NEWLINE>", " ")

    # <NAME> e dinamico no save do jogo. Por padrao, a dublagem nao
    # pronuncia um nome fixo: o marcador vira uma pausa natural, enquanto
    # a legenda continua mostrando o nome escolhido pelo jogador.
    if player_name:
        text = text.replace("<NAME>", player_name)
    else:
        # Consome tambem a pontuacao imediatamente ligada ao nome. Assim
        # "<NAME>...?", "<NAME>!" e casos semelhantes viram uma unica pausa.
        text = re.sub(r"<NAME>\s*[.!?,;:]*", "...", text)

    text = TAG_RE.sub(" ", text)
    text = SPACE_RE.sub(" ", text).strip()
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)

    if not player_name:
        # Evita combinacoes artificiais criadas ao remover o nome.
        text = re.sub(r"\.{4,}", "...", text)
        text = re.sub(r"[,;:]\s*\.\.\.", "...", text)
        text = re.sub(r"\s+\.\.\.", "...", text)
        text = re.sub(r"\.\.\.\s*[,;:!?]+", "...", text)
        text = re.sub(r"^\.\.\.\s*", "", text)

        # Se a pagina continha apenas o nome/pontuacao, nao ha fala util
        # para sintetizar.
        if re.fullmatch(r"[\s.!?,;:'\"-]*", text):
            return ""

    return text


def add_punctuation_pauses(text: str) -> str:
    """Adiciona pausas SSML conservadoras sem remover a pontuacao original."""
    if not text:
        return text

    pause_by_mark = {
        "...": "0.45s",
        "?": "0.32s",
        ".": "0.28s",
        "!": "0.25s",
        ";": "0.20s",
        ":": "0.20s",
        ",": "0.12s",
    }
    punctuation_re = re.compile(r"\.\.\.|[.!?;:,]")
    inserted = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal inserted
        mark = match.group(0)

        if inserted >= MAX_PROSODY_BREAKS_PER_PAGE:
            return mark

        # So adiciona pausa quando ainda existe fala depois da pontuacao.
        tail = text[match.end():]
        if not tail:
            return mark

        # Evita tratar separadores internos sem espaco como pausa de frase.
        first = tail[0]
        if not (first.isspace() or first in '"\'”’)]}'):
            return mark

        meaningful = tail.lstrip()
        while meaningful and meaningful[0] in '"\'”’)]}':
            meaningful = meaningful[1:].lstrip()
        if not meaningful:
            return mark

        inserted += 1
        return f'{mark} <break time="{pause_by_mark[mark]}" />'

    return punctuation_re.sub(replace, text)


def load_speaker_entries(root: Path) -> dict[str, str]:
    data = load_json(root / "scripts" / "ptbr_dubbing" / "speaker_map.json")
    entries = data.get("entries", {})
    if not isinstance(entries, dict):
        raise RuntimeError("speaker_map.json nao possui objeto 'entries'.")
    return {str(k): str(v) for k, v in entries.items()}


def load_cast(root: Path) -> dict[str, dict[str, Any]]:
    data = load_json(root / "scripts" / "ptbr_dubbing" / "voice_cast.json")
    if not isinstance(data, dict):
        raise RuntimeError("voice_cast.json deve ser um objeto JSON.")
    return data


def load_runtime_markers(root: Path) -> dict[str, dict[str, Any]]:
    data = load_json(
        root / "scripts" / "ptbr_dubbing" / "runtime_voice_variants.json"
    )
    markers = data.get("markers", {})
    if not isinstance(markers, dict):
        raise RuntimeError(
            "runtime_voice_variants.json nao possui objeto 'markers'."
        )
    return markers


def page_speaker(
    entries: dict[str, str],
    text_id: int,
    page: int,
) -> str | None:
    id_key = f"{text_id:04X}"
    page_key = f"{text_id:04X}:{page:02d}"
    return entries.get(page_key, entries.get(id_key))


def validate_configuration(
    entries: dict[str, str],
    cast: dict[str, dict[str, Any]],
    runtime_markers: dict[str, dict[str, Any]],
) -> None:
    errors: list[str] = []

    for key, speaker in entries.items():
        if speaker == NO_DUB:
            continue

        if speaker.startswith("__runtime_"):
            if speaker not in runtime_markers:
                errors.append(
                    f"{key}: marcador runtime sem configuracao: {speaker}"
                )
            continue

        if speaker not in cast:
            errors.append(
                f"{key}: speaker '{speaker}' nao existe em voice_cast.json"
            )

    for marker, config in runtime_markers.items():
        speakers = config.get("speakers") or []
        fallback = config.get("fallback_speaker")

        if not isinstance(speakers, list) or not speakers:
            errors.append(f"{marker}: lista 'speakers' vazia ou invalida")
            continue

        for speaker in speakers:
            if speaker not in cast:
                errors.append(
                    f"{marker}: speaker '{speaker}' ausente em voice_cast.json"
                )

        if fallback not in speakers:
            errors.append(
                f"{marker}: fallback_speaker deve existir em 'speakers'"
            )

    for speaker, data in cast.items():
        voice_id = str((data or {}).get("voice_id") or "").strip()
        if not voice_id:
            errors.append(f"{speaker}: voice_id vazio em voice_cast.json")

    if errors:
        preview = "\n".join(f"- {item}" for item in errors[:50])
        extra = ""
        if len(errors) > 50:
            extra = f"\n... e mais {len(errors) - 50} erro(s)."
        raise RuntimeError(
            "Configuracao de dublagem invalida:\n" + preview + extra
        )


def cast_voice_id(
    cast: dict[str, dict[str, Any]],
    speaker: str,
) -> str:
    data = cast.get(speaker)
    if not data:
        raise RuntimeError(f"Speaker sem elenco: {speaker}")

    voice_id = str(data.get("voice_id") or "").strip()
    if not voice_id:
        raise RuntimeError(f"Speaker sem voice_id: {speaker}")

    return voice_id


def speaker_display_name(
    cast: dict[str, dict[str, Any]],
    speaker: str,
) -> str:
    data = cast.get(speaker) or {}
    name = str(data.get("name") or "").strip()
    return name or speaker


def elevenlabs_request(
    text: str,
    voice_id: str,
    api_key: str,
    model_id: str,
    speed: float,
    attempts: int = 3,
) -> bytes:
    encoded_voice = urllib.parse.quote(voice_id, safe="")
    url = (
        f"{API_BASE}/{encoded_voice}"
        f"?output_format={DEFAULT_OUTPUT_FORMAT}"
    )

    payload = json.dumps(
        {
            "text": text,
            "model_id": model_id,
            "voice_settings": {
                "speed": speed,
            },
        },
        ensure_ascii=False,
    ).encode("utf-8")

    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
        "User-Agent": "Shipwright-PTBR-Dubbing/2.0",
    }

    last_error: Exception | None = None

    for attempt in range(1, attempts + 1):
        request = urllib.request.Request(
            url,
            data=payload,
            headers=headers,
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                return response.read()
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            last_error = RuntimeError(
                f"ElevenLabs HTTP {exc.code}: {body[:700]}"
            )

            if exc.code == 429 or 500 <= exc.code <= 504:
                if attempt < attempts:
                    time.sleep(2 ** (attempt - 1))
                    continue

            raise last_error from exc
        except urllib.error.URLError as exc:
            last_error = RuntimeError(
                f"Falha de conexao com ElevenLabs: {exc.reason}"
            )
            if attempt < attempts:
                time.sleep(2 ** (attempt - 1))
                continue
            raise last_error from exc

    if last_error is not None:
        raise last_error

    raise RuntimeError("Falha desconhecida ao chamar ElevenLabs.")


def convert_to_wav(mp3_path: Path, wav_path: Path) -> None:
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise RuntimeError(
            "ffmpeg nao foi encontrado no PATH."
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
            "Falha ao converter audio com ffmpeg:\n"
            + result.stderr.strip()
        )


def synthesize_wav(
    text: str,
    speaker: str,
    cast: dict[str, dict[str, Any]],
    output: Path,
    api_key: str,
    model_id: str,
    speed: float,
) -> None:
    voice_id = cast_voice_id(cast, speaker)
    mp3_bytes = elevenlabs_request(
        text=text,
        voice_id=voice_id,
        api_key=api_key,
        model_id=model_id,
        speed=speed,
    )

    output.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="ptbr_voice_") as temp_dir:
        mp3_path = Path(temp_dir) / "voice.mp3"
        mp3_path.write_bytes(mp3_bytes)
        convert_to_wav(mp3_path, output)


def should_generate(
    output: Path,
    overwrite: bool,
) -> bool:
    return overwrite or not output.exists()


def generate_single(
    text_id: int,
    page_index: int,
    spoken: str,
    speaker: str,
    output: Path,
    cast: dict[str, dict[str, Any]],
    api_key: str | None,
    model_id: str,
    speed: float,
    prosody_pauses: bool,
    overwrite: bool,
    dry_run: bool,
) -> int:
    display = speaker_display_name(cast, speaker)
    tts_text = add_punctuation_pauses(spoken) if prosody_pauses else spoken

    print(
        f"  [{page_index:02d}] {speaker} | {display}\n"
        f"       {spoken}\n"
        f"       -> {output}"
    )
    if prosody_pauses and tts_text != spoken:
        print(f"       prosodia API: {tts_text}")

    if not spoken:
        print("       ignorado: pagina sem texto falado")
        return 0

    if not should_generate(output, overwrite):
        print("       ignorado: arquivo ja existe")
        return 0

    if dry_run:
        return 0

    if not api_key:
        raise RuntimeError(
            "ELEVENLABS_API_KEY nao encontrada. "
            "Defina no ambiente ou no .env da raiz."
        )

    synthesize_wav(
        text=tts_text,
        speaker=speaker,
        cast=cast,
        output=output,
        api_key=api_key,
        model_id=model_id,
        speed=speed,
    )
    print("       OK")
    return 1


def generate_runtime_page(
    text_id: int,
    page_index: int,
    spoken: str,
    marker: str,
    marker_config: dict[str, Any],
    output_dir: Path,
    cast: dict[str, dict[str, Any]],
    api_key: str | None,
    model_id: str,
    speed: float,
    prosody_pauses: bool,
    overwrite: bool,
    dry_run: bool,
    speaker_filter: str | None,
) -> int:
    speakers = [str(x) for x in marker_config.get("speakers") or []]
    fallback = str(marker_config.get("fallback_speaker") or "")

    if speaker_filter:
        speakers = [s for s in speakers if s == speaker_filter]

    print(f"  [{page_index:02d}] runtime {marker}")

    generated = 0
    for speaker in speakers:
        variant_output = (
            output_dir
            / f"{text_id:04X}_{page_index:02d}_{speaker}.wav"
        )
        generated += generate_single(
            text_id=text_id,
            page_index=page_index,
            spoken=spoken,
            speaker=speaker,
            output=variant_output,
            cast=cast,
            api_key=api_key,
            model_id=model_id,
            speed=speed,
            prosody_pauses=prosody_pauses,
            overwrite=overwrite,
            dry_run=dry_run,
        )

    # O arquivo base existe apenas como fallback de seguranca para o runtime.
    # Ele e uma copia do fallback_speaker, portanto nao consome TTS adicional.
    if not speaker_filter or speaker_filter == fallback:
        fallback_variant = (
            output_dir
            / f"{text_id:04X}_{page_index:02d}_{fallback}.wav"
        )
        base_output = output_dir / f"{text_id:04X}_{page_index:02d}.wav"

        print(
            f"       fallback base: {fallback} -> {base_output}"
        )

        if not dry_run and fallback_variant.exists():
            if should_generate(base_output, overwrite):
                base_output.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(fallback_variant, base_output)

    return generated


def generate_text_id(
    text_id: int,
    tokens: str,
    entries: dict[str, str],
    cast: dict[str, dict[str, Any]],
    runtime_markers: dict[str, dict[str, Any]],
    output_dir: Path,
    player_name: str | None,
    api_key: str | None,
    model_id: str,
    speed: float,
    prosody_pauses: bool,
    overwrite: bool,
    dry_run: bool,
    speaker_filter: str | None,
) -> int:
    pages = split_pages(tokens)
    generated = 0

    print(f"\n0x{text_id:04X}: {len(pages)} pagina(s)")

    for page_index, page_tokens in enumerate(pages):
        mapped = page_speaker(entries, text_id, page_index)

        if mapped is None:
            print(
                f"  [{page_index:02d}] ERRO: pagina sem speaker_map"
            )
            continue

        if mapped == NO_DUB:
            print(f"  [{page_index:02d}] sem dublagem")
            continue

        spoken = clean_spoken_text(page_tokens, player_name)

        if mapped.startswith("__runtime_"):
            marker_config = runtime_markers.get(mapped)
            if marker_config is None:
                raise RuntimeError(
                    f"Marcador runtime sem configuracao: {mapped}"
                )

            if (
                speaker_filter
                and speaker_filter
                not in marker_config.get("speakers", [])
            ):
                continue

            generated += generate_runtime_page(
                text_id=text_id,
                page_index=page_index,
                spoken=spoken,
                marker=mapped,
                marker_config=marker_config,
                output_dir=output_dir,
                cast=cast,
                api_key=api_key,
                model_id=model_id,
                speed=speed,
                overwrite=overwrite,
                dry_run=dry_run,
                speaker_filter=speaker_filter,
            )
            continue

        if speaker_filter and mapped != speaker_filter:
            continue

        output = output_dir / f"{text_id:04X}_{page_index:02d}.wav"
        generated += generate_single(
            text_id=text_id,
            page_index=page_index,
            spoken=spoken,
            speaker=mapped,
            output=output,
            cast=cast,
            api_key=api_key,
            model_id=model_id,
            speed=speed,
            prosody_pauses=prosody_pauses,
            overwrite=overwrite,
            dry_run=dry_run,
        )

    return generated


def estimate_usage(
    requested: list[int],
    messages: dict[int, str],
    entries: dict[str, str],
    runtime_markers: dict[str, dict[str, Any]],
    player_name: str | None,
    speaker_filter: str | None,
) -> dict[str, int]:
    message_ids: set[int] = set()
    spoken_pages = 0
    static_pages = 0
    runtime_pages = 0
    runtime_variants = 0
    static_characters = 0
    runtime_base_characters = 0
    runtime_extra_characters = 0
    tts_requests = 0

    for text_id in requested:
        pages = split_pages(messages[text_id])

        for page_index, page_tokens in enumerate(pages):
            mapped = page_speaker(entries, text_id, page_index)

            if mapped is None or mapped == NO_DUB:
                continue

            spoken = clean_spoken_text(page_tokens, player_name)
            if not spoken:
                continue

            if mapped.startswith("__runtime_"):
                marker_config = runtime_markers.get(mapped)
                if marker_config is None:
                    raise RuntimeError(
                        f"Marcador runtime sem configuracao: {mapped}"
                    )

                speakers = [
                    str(x)
                    for x in marker_config.get("speakers") or []
                ]
                if speaker_filter:
                    speakers = [
                        speaker
                        for speaker in speakers
                        if speaker == speaker_filter
                    ]

                variant_count = len(speakers)
                if variant_count == 0:
                    continue

                chars = len(spoken)
                message_ids.add(text_id)
                spoken_pages += 1
                runtime_pages += 1
                runtime_variants += variant_count
                runtime_base_characters += chars
                runtime_extra_characters += chars * (variant_count - 1)
                tts_requests += variant_count
                continue

            if speaker_filter and mapped != speaker_filter:
                continue

            chars = len(spoken)
            message_ids.add(text_id)
            spoken_pages += 1
            static_pages += 1
            static_characters += chars
            tts_requests += 1

    runtime_total_characters = (
        runtime_base_characters + runtime_extra_characters
    )
    total_characters = static_characters + runtime_total_characters
    estimated_credits = round(
        total_characters * ESTIMATE_CREDITS_PER_CHARACTER
    )

    return {
        "message_ids": len(message_ids),
        "spoken_pages": spoken_pages,
        "static_pages": static_pages,
        "runtime_pages": runtime_pages,
        "runtime_variants": runtime_variants,
        "static_characters": static_characters,
        "runtime_base_characters": runtime_base_characters,
        "runtime_extra_characters": runtime_extra_characters,
        "runtime_total_characters": runtime_total_characters,
        "total_characters": total_characters,
        "tts_requests": tts_requests,
        "estimated_credits": estimated_credits,
    }


def print_usage_estimate(stats: dict[str, int], model_id: str) -> None:
    print("\nESTIMATIVA DE USO ELEVENLABS")
    print("=" * 52)
    print(f"Modelo configurado:              {model_id}")
    print(f"Mensagens com fala:              {stats['message_ids']:,}")
    print(f"Paginas faladas:                 {stats['spoken_pages']:,}")
    print(f"  Paginas estaticas:             {stats['static_pages']:,}")
    print(f"  Paginas runtime:               {stats['runtime_pages']:,}")
    print(f"Variantes runtime a sintetizar:  {stats['runtime_variants']:,}")
    print(f"Chamadas TTS estimadas:          {stats['tts_requests']:,}")
    print("-" * 52)
    print(
        "Caracteres estaticos:            "
        f"{stats['static_characters']:,}"
    )
    print(
        "Caracteres runtime base:         "
        f"{stats['runtime_base_characters']:,}"
    )
    print(
        "Extras por variantes runtime:    "
        f"{stats['runtime_extra_characters']:,}"
    )
    print(
        "Caracteres runtime totais:       "
        f"{stats['runtime_total_characters']:,}"
    )
    print("-" * 52)
    print(
        "TOTAL enviado ao TTS:            "
        f"{stats['total_characters']:,} caracteres"
    )
    print(
        "Creditos estimados (1 por char): "
        f"{stats['estimated_credits']:,}"
    )
    print(
        "\nObservacao: a linha de creditos usa a referencia nominal "
        "de 1 credito por caractere. O consumo real pode variar "
        "conforme modelo/plano da ElevenLabs."
    )
    print(
        "O WAV base dos IDs runtime nao gera chamada adicional; "
        "ele e apenas copiado da variante de fallback."
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Gerador ElevenLabs da dublagem PT-BR do Ship of Harkinian."
    )
    parser.add_argument(
        "--text-id",
        action="append",
        default=[],
        help="ID hexadecimal. Ex.: 1000 ou 0x1000. Pode repetir.",
    )
    parser.add_argument(
        "--speaker",
        default=None,
        help=(
            "Gera apenas falas de uma chave de voice_cast.json. "
            "Ex.: navi, saria, npc_masculino."
        ),
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Gera todas as paginas faladas mapeadas.",
    )
    parser.add_argument(
        "--configured",
        action="store_true",
        help="Alias legado de --all.",
    )
    parser.add_argument(
        "--name",
        default=None,
        help=(
            "Opcional: forca um nome fixo para <NAME>. "
            "Sem esta opcao, <NAME> vira uma pausa na dublagem e a legenda "
            "continua usando o nome dinamico do save."
        ),
    )
    parser.add_argument(
        "--model-id",
        default=DEFAULT_MODEL_ID,
        help=(
            "Modelo TTS da ElevenLabs. "
            f"Padrao: {DEFAULT_MODEL_ID}."
        ),
    )
    parser.add_argument(
        "--speed",
        type=float,
        default=DEFAULT_SPEED,
        help=(
            "Velocidade da voz na ElevenLabs, de 0.7 a 1.2. "
            f"Padrao do projeto: {DEFAULT_SPEED}. Ex.: --speed 0.90."
        ),
    )
    parser.add_argument(
        "--prosody-pauses",
        action="store_true",
        help=(
            "Adiciona pausas SSML conservadoras apos pontuacao para testar "
            "cadencia mais natural. Mantem a pontuacao original."
        ),
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Pasta de saida. Padrao: x64/Release/voices/ptbr.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Substitui WAVs existentes.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Valida e mostra os arquivos sem consumir TTS.",
    )
    parser.add_argument(
        "--estimate",
        action="store_true",
        help=(
            "Calcula paginas, variantes, caracteres e creditos estimados "
            "sem chamar a API. Sem outro filtro, estima toda a dublagem."
        ),
    )
    args = parser.parse_args()

    root = repo_root()
    messages = load_messages(root)
    entries = load_speaker_entries(root)
    cast = load_cast(root)
    runtime_markers = load_runtime_markers(root)

    validate_configuration(entries, cast, runtime_markers)

    if not 0.7 <= args.speed <= 1.2:
        parser.error("--speed deve estar entre 0.7 e 1.2.")

    if args.speaker and args.speaker not in cast:
        parser.error(
            f"Speaker '{args.speaker}' nao existe em voice_cast.json."
        )

    requested = [parse_text_id(value) for value in args.text_id]

    if args.all or args.configured or args.speaker or args.estimate:
        requested.extend(messages.keys())

    requested = sorted(set(requested))

    if not requested:
        parser.error(
            "Informe --text-id 1000, --speaker navi, --all ou --estimate."
        )

    missing = [text_id for text_id in requested if text_id not in messages]
    if missing:
        formatted = ", ".join(f"0x{x:04X}" for x in missing)
        raise RuntimeError(
            f"Text ID(s) nao encontrado(s): {formatted}"
        )

    if args.estimate:
        stats = estimate_usage(
            requested=requested,
            messages=messages,
            entries=entries,
            runtime_markers=runtime_markers,
            player_name=args.name,
            speaker_filter=args.speaker,
        )
        print_usage_estimate(stats, args.model_id)
        print("\nEstimativa concluida. Nenhuma chamada a ElevenLabs foi feita.")
        return 0

    output_dir = (
        Path(args.output_dir).resolve()
        if args.output_dir
        else root / "x64" / "Release" / "voices" / "ptbr"
    )

    api_key = None if args.dry_run else get_api_key(root)

    if not args.dry_run and not api_key:
        raise RuntimeError(
            "ELEVENLABS_API_KEY nao encontrada. "
            "Defina a chave no ambiente ou no .env da raiz."
        )

    total = 0
    for text_id in requested:
        total += generate_text_id(
            text_id=text_id,
            tokens=messages[text_id],
            entries=entries,
            cast=cast,
            runtime_markers=runtime_markers,
            output_dir=output_dir,
            player_name=args.name,
            api_key=api_key,
            model_id=args.model_id,
            speed=args.speed,
            prosody_pauses=args.prosody_pauses,
            overwrite=args.overwrite,
            dry_run=args.dry_run,
            speaker_filter=args.speaker,
        )

    if args.dry_run:
        print("\nDry-run concluido. Nenhum credito da ElevenLabs foi consumido.")
    else:
        print(f"\nConcluido. {total} WAV(s) novo(s) gerado(s).")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nCancelado.")
        raise SystemExit(130)
    except Exception as exc:
        print(f"\nERRO: {exc}", file=sys.stderr)
        raise SystemExit(1)
