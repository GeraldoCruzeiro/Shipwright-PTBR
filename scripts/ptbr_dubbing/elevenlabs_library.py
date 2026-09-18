#!/usr/bin/env python3
r"""
Baixa amostras da ElevenLabs Voice Library para montar o elenco PT-BR.

Por padrão tenta encontrar vozes verificadas para pt-BR. Se não houver
resultados suficientes, amplia automaticamente para português (pt).

Uso:
    py scripts\ptbr_dubbing\elevenlabs_library.py

Exemplos:
    py scripts\ptbr_dubbing\elevenlabs_library.py --limit 30
    py scripts\ptbr_dubbing\elevenlabs_library.py --gender female --limit 20
    py scripts\ptbr_dubbing\elevenlabs_library.py --gender male --limit 20
    py scripts\ptbr_dubbing\elevenlabs_library.py --all --limit 40

Saída:
    dublagem_vozes_elevenlabs\
        001_NomeDaVoz.mp3
        002_OutraVoz.mp3
        ...
        catalogo.json

O script usa somente a biblioteca padrão do Python.
Se ELEVENLABS_API_KEY estiver definida no ambiente ou no arquivo .env da
raiz do projeto, ela será enviada à API. A chave nunca é impressa.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

API_URL = "https://api.elevenlabs.io/v1/shared-voices"


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_dotenv_value(path: Path, key: str) -> str | None:
    if not path.exists():
        return None

    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None

    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        if name.strip() != key:
            continue

        value = value.strip().strip('"').strip("'")
        return value or None

    return None


def get_api_key(root: Path) -> str | None:
    return (
        os.getenv("ELEVENLABS_API_KEY")
        or load_dotenv_value(root / ".env", "ELEVENLABS_API_KEY")
    )


def safe_filename(value: str) -> str:
    value = re.sub(r'[<>:"/\\|?*]+', "_", value)
    value = re.sub(r"\s+", "_", value).strip("._ ")
    return value[:100] or "voz"


def request_json(url: str, api_key: str | None) -> dict[str, Any]:
    headers = {
        "Accept": "application/json",
        "User-Agent": "Shipwright-PTBR-Dubbing/1.0",
    }

    if api_key:
        headers["xi-api-key"] = api_key

    request = urllib.request.Request(url, headers=headers)

    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        if exc.code in (401, 403):
            raise RuntimeError(
                "A ElevenLabs recusou o acesso à Voice Library pela API "
                f"(HTTP {exc.code}). Se sua conta exigir autenticação, crie "
                "uma API key e defina ELEVENLABS_API_KEY. Em alguns planos, "
                "a Voice Library não fica disponível via API.\n"
                f"Resposta: {body[:500]}"
            ) from exc

        raise RuntimeError(
            f"Erro HTTP {exc.code} ao consultar a ElevenLabs: {body[:500]}"
        ) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(
            f"Falha de conexão com a ElevenLabs: {exc.reason}"
        ) from exc


def request_bytes(url: str) -> bytes:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Shipwright-PTBR-Dubbing/1.0",
        },
    )

    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def best_preview(voice: dict[str, Any]) -> str | None:
    verified = voice.get("verified_languages") or []

    # Preferência máxima: amostra já verificada em pt-BR.
    for item in verified:
        if item.get("locale") == "pt-BR" and item.get("preview_url"):
            return str(item["preview_url"])

    # Segunda opção: qualquer amostra em português.
    for item in verified:
        if item.get("language") == "pt" and item.get("preview_url"):
            return str(item["preview_url"])

    preview = voice.get("preview_url")
    return str(preview) if preview else None


def make_query(
    page_size: int,
    page: int,
    gender: str | None,
    locale: str | None,
    language: str | None,
) -> str:
    params: dict[str, Any] = {
        "page_size": min(max(page_size, 1), 100),
        "page": max(page, 0),
        "sort": "trending",
        "include_live_moderated": "false",
    }

    if gender:
        params["gender"] = gender
    if locale:
        params["locale"] = locale
    if language:
        params["language"] = language

    return API_URL + "?" + urllib.parse.urlencode(params)


def fetch_voices(
    api_key: str | None,
    limit: int,
    gender: str | None,
    all_languages: bool,
) -> list[dict[str, Any]]:
    filters: list[tuple[str | None, str | None, str]]

    if all_languages:
        filters = [(None, None, "sem filtro de idioma")]
    else:
        filters = [
            ("pt-BR", None, "locale pt-BR"),
            (None, "pt", "idioma português"),
        ]

    seen: set[str] = set()
    results: list[dict[str, Any]] = []

    for locale, language, label in filters:
        print(f"Consultando Voice Library: {label}...")

        page = 0
        while len(results) < limit:
            remaining = limit - len(results)
            url = make_query(
                page_size=min(max(remaining, 20), 100),
                page=page,
                gender=gender,
                locale=locale,
                language=language,
            )

            data = request_json(url, api_key)
            voices = data.get("voices") or []

            if not voices:
                break

            for voice in voices:
                voice_id = str(voice.get("voice_id", ""))
                if not voice_id or voice_id in seen:
                    continue

                if best_preview(voice) is None:
                    continue

                seen.add(voice_id)
                results.append(voice)

                if len(results) >= limit:
                    break

            if not data.get("has_more") or len(results) >= limit:
                break

            page += 1

        if len(results) >= limit:
            break

    return results


def save_catalog(
    output_dir: Path,
    voices: list[dict[str, Any]],
) -> None:
    catalog: list[dict[str, Any]] = []

    for index, voice in enumerate(voices, start=1):
        name = str(voice.get("name") or f"Voz_{index:03d}")
        voice_id = str(voice.get("voice_id") or "")
        owner_id = str(voice.get("public_owner_id") or "")
        preview_url = best_preview(voice)

        if not preview_url:
            continue

        filename = f"{index:03d}_{safe_filename(name)}.mp3"
        output_path = output_dir / filename

        print(
            f"[{index:03d}/{len(voices):03d}] {name} | "
            f"{voice.get('gender', '?')} | {voice.get('age', '?')} | "
            f"{voice.get('accent', '?')}"
        )

        try:
            output_path.write_bytes(request_bytes(preview_url))
        except Exception as exc:
            print(f"    FALHOU ao baixar preview: {exc}")
            continue

        print(f"    OK -> {filename}")

        catalog.append(
            {
                "numero": index,
                "arquivo": filename,
                "name": name,
                "voice_id": voice_id,
                "public_owner_id": owner_id,
                "gender": voice.get("gender"),
                "age": voice.get("age"),
                "accent": voice.get("accent"),
                "descriptive": voice.get("descriptive"),
                "use_case": voice.get("use_case"),
                "category": voice.get("category"),
                "language": voice.get("language"),
                "description": voice.get("description"),
                "preview_url": preview_url,
                "free_users_allowed": voice.get("free_users_allowed"),
                "verified_languages": voice.get("verified_languages") or [],
            }
        )

    (output_dir / "catalogo.json").write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Baixa previews da ElevenLabs Voice Library para seleção "
            "do elenco da dublagem."
        )
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=30,
        help="Quantidade de vozes a baixar. Padrão: 30.",
    )
    parser.add_argument(
        "--gender",
        choices=["male", "female"],
        default=None,
        help="Filtra por gênero quando disponível.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help=(
            "Não limita a português. Útil para procurar timbres adicionais "
            "em vozes multilíngues."
        ),
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help=(
            "Pasta de saída. Padrão: "
            "<repo>\\dublagem_vozes_elevenlabs"
        ),
    )
    args = parser.parse_args()

    if args.limit < 1:
        parser.error("--limit deve ser maior que zero.")

    root = repo_root()
    api_key = get_api_key(root)

    if api_key:
        print("API key da ElevenLabs encontrada.")
    else:
        print(
            "Nenhuma API key encontrada. Tentando acessar os previews "
            "públicos da Voice Library."
        )

    output_dir = (
        Path(args.output_dir).resolve()
        if args.output_dir
        else root / "dublagem_vozes_elevenlabs"
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        voices = fetch_voices(
            api_key=api_key,
            limit=args.limit,
            gender=args.gender,
            all_languages=args.all,
        )
    except Exception as exc:
        print(f"\nERRO: {exc}", file=sys.stderr)
        return 1

    if not voices:
        print(
            "\nNenhuma voz encontrada com os filtros usados. "
            "Tente novamente com --all."
        )
        return 1

    print(f"\nEncontradas {len(voices)} vozes. Baixando amostras...")
    save_catalog(output_dir, voices)

    print()
    print("Concluído.")
    print(f"Pasta: {output_dir}")
    print("Catálogo: catalogo.json")
    print()
    print(
        "Ouça os MP3s e anote os números das vozes que combinam com "
        "Navi, Saria, Árvore Deku, Mido, Zelda e Ganondorf."
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
