#!/usr/bin/env python3
r"""
Consulta e baixa amostras da ElevenLabs Voice Library para montar o elenco PT-BR.

Uso geral:
    py scripts\ptbr_dubbing\elevenlabs_library.py --limit 30

Busca por personagem:
    py scripts\ptbr_dubbing\elevenlabs_library.py --character navi --limit 15

O modo --character:
1. carrega scripts/ptbr_dubbing/character_profiles.json;
2. filtra primeiro por gênero;
3. prioriza vozes verificadas para pt-BR/português;
4. ranqueia localmente idade, descrição, use case e palavras-chave;
5. baixa somente as melhores candidatas em dublagem_selecao/<personagem>/.

A consulta e o download de previews não geram novo TTS.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import unicodedata
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


def normalize(value: Any) -> str:
    text = "" if value is None else str(value)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower().replace("_", " ").replace("-", " ")
    return re.sub(r"\s+", " ", text).strip()


def load_profiles(root: Path) -> dict[str, dict[str, Any]]:
    path = root / "scripts" / "ptbr_dubbing" / "character_profiles.json"
    if not path.exists():
        raise RuntimeError(f"Arquivo de perfis não encontrado: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def load_cast(root: Path) -> dict[str, dict[str, Any]]:
    path = root / "scripts" / "ptbr_dubbing" / "voice_cast.json"
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def used_voice_ids(
    cast: dict[str, dict[str, Any]],
    exclude_character: str | None = None,
) -> dict[str, str]:
    used: dict[str, str] = {}
    for character, data in cast.items():
        if character == exclude_character:
            continue
        voice_id = str((data or {}).get("voice_id") or "").strip()
        if voice_id:
            used[voice_id] = character
    return used


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
                f"(HTTP {exc.code}). Verifique ELEVENLABS_API_KEY no .env.\n"
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
        headers={"User-Agent": "Shipwright-PTBR-Dubbing/1.0"},
    )

    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def best_preview(voice: dict[str, Any]) -> str | None:
    verified = voice.get("verified_languages") or []

    for item in verified:
        if item.get("locale") == "pt-BR" and item.get("preview_url"):
            return str(item["preview_url"])

    for item in verified:
        if item.get("language") == "pt" and item.get("preview_url"):
            return str(item["preview_url"])

    preview = voice.get("preview_url")
    return str(preview) if preview else None


def portuguese_score(voice: dict[str, Any]) -> int:
    score = 0
    for item in voice.get("verified_languages") or []:
        if item.get("locale") == "pt-BR":
            score = max(score, 12)
        elif item.get("language") == "pt":
            score = max(score, 7)

    if normalize(voice.get("language")) == "pt":
        score = max(score, 5)

    return score


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


def voice_corpus(voice: dict[str, Any]) -> str:
    verified_parts: list[str] = []
    for item in voice.get("verified_languages") or []:
        verified_parts.extend(
            [
                str(item.get("language") or ""),
                str(item.get("locale") or ""),
                str(item.get("accent") or ""),
            ]
        )

    parts = [
        voice.get("name"),
        voice.get("gender"),
        voice.get("age"),
        voice.get("accent"),
        voice.get("descriptive"),
        voice.get("use_case"),
        voice.get("category"),
        voice.get("language"),
        voice.get("description"),
        *verified_parts,
    ]

    return normalize(" ".join("" if p is None else str(p) for p in parts))


def score_voice(
    voice: dict[str, Any],
    profile: dict[str, Any],
) -> tuple[int, list[str]]:
    score = portuguese_score(voice)
    reasons: list[str] = []

    wanted_gender = normalize(profile.get("gender"))
    actual_gender = normalize(voice.get("gender"))
    if wanted_gender and actual_gender:
        if wanted_gender == actual_gender:
            score += 15
            reasons.append("gênero compatível")
        else:
            score -= 30

    wanted_age = normalize(profile.get("age"))
    actual_age = normalize(voice.get("age"))
    if wanted_age and actual_age:
        if wanted_age == actual_age:
            score += 12
            reasons.append("idade compatível")
        elif wanted_age in actual_age or actual_age in wanted_age:
            score += 8

    corpus = voice_corpus(voice)
    matched: list[str] = []

    for keyword in profile.get("keywords", []):
        key = normalize(keyword)
        if key and key in corpus:
            matched.append(keyword)
            score += 4

    use_case = normalize(voice.get("use_case"))
    if "character" in use_case or "animation" in use_case:
        score += 5
        reasons.append("voz voltada a personagem")

    descriptive = normalize(voice.get("descriptive"))
    if descriptive and any(normalize(k) == descriptive for k in profile.get("keywords", [])):
        score += 3

    if matched:
        reasons.append("perfil: " + ", ".join(matched[:5]))

    pt_score = portuguese_score(voice)
    if pt_score >= 12:
        reasons.append("pt-BR verificado")
    elif pt_score >= 7:
        reasons.append("português verificado")

    return score, reasons


def rank_for_character(
    voices: list[dict[str, Any]],
    profile: dict[str, Any],
    limit: int,
) -> list[dict[str, Any]]:
    ranked: list[dict[str, Any]] = []

    for voice in voices:
        score, reasons = score_voice(voice, profile)
        item = dict(voice)
        item["_match_score"] = score
        item["_match_reasons"] = reasons
        ranked.append(item)

    ranked.sort(
        key=lambda item: (
            int(item.get("_match_score", 0)),
            int(item.get("cloned_by_count") or 0),
            int(item.get("usage_character_count_1y") or 0),
        ),
        reverse=True,
    )
    return ranked[:limit]


def save_catalog(
    output_dir: Path,
    voices: list[dict[str, Any]],
    character: str | None = None,
    profile: dict[str, Any] | None = None,
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
        match_score = voice.get("_match_score")
        reasons = voice.get("_match_reasons") or []

        extra = ""
        if match_score is not None:
            extra = f" | compatibilidade={match_score}"

        print(
            f"[{index:03d}/{len(voices):03d}] {name} | "
            f"{voice.get('gender', '?')} | {voice.get('age', '?')} | "
            f"{voice.get('accent', '?')}{extra}"
        )
        if reasons:
            print("    " + "; ".join(str(x) for x in reasons))

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
                "character": character,
                "character_profile": profile,
                "match_score": match_score,
                "match_reasons": reasons,
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
                "rate": voice.get("rate"),
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
        help="Quantidade de vozes finais a baixar. Padrão: 30.",
    )
    parser.add_argument(
        "--gender",
        choices=["male", "female"],
        default=None,
        help="Filtra por gênero quando não estiver usando --character.",
    )
    parser.add_argument(
        "--character",
        default=None,
        help=(
            "Chave do personagem em character_profiles.json. "
            "Ex.: navi, saria, ganondorf."
        ),
    )
    parser.add_argument(
        "--list-characters",
        action="store_true",
        help="Lista os personagens configurados e encerra.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help=(
            "Não limita a português. Útil para ampliar a busca quando "
            "faltarem candidatos."
        ),
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Pasta de saída personalizada.",
    )
    args = parser.parse_args()

    if args.limit < 1:
        parser.error("--limit deve ser maior que zero.")

    root = repo_root()
    profiles = load_profiles(root)
    cast = load_cast(root)

    if args.list_characters:
        print("Personagens configurados:")
        for key, profile in profiles.items():
            print(f"  {key:24s} -> {profile.get('name', key)}")
        return 0

    profile: dict[str, Any] | None = None
    character_key: str | None = None
    gender = args.gender

    if args.character:
        character_key = normalize(args.character).replace(" ", "_")
        if character_key not in profiles:
            available = ", ".join(profiles.keys())
            parser.error(
                f"Personagem '{args.character}' não encontrado. "
                f"Disponíveis: {available}"
            )
        profile = profiles[character_key]
        gender = profile.get("gender") or gender

        print("=" * 68)
        print(f"PERSONAGEM: {profile.get('name', character_key)}")
        print(f"Perfil: {profile.get('description_pt', '')}")
        print(f"Gênero: {profile.get('gender', '?')}")
        print(f"Faixa etária: {profile.get('age', '?')}")
        print("Palavras-chave: " + ", ".join(profile.get("keywords", [])))
        print("=" * 68)

    api_key = get_api_key(root)

    if api_key:
        print("API key da ElevenLabs encontrada.")
    else:
        print(
            "Nenhuma API key encontrada. Tentando acessar os previews "
            "públicos da Voice Library."
        )

    if args.output_dir:
        output_dir = Path(args.output_dir).resolve()
    elif character_key:
        output_dir = root / "dublagem_selecao" / character_key
    else:
        output_dir = root / "dublagem_vozes_elevenlabs"

    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        if profile is not None:
            # Busca um conjunto bem maior e só depois ranqueia. Assim o usuário
            # ouve poucas vozes, mas elas vieram de uma triagem ampla.
            pool_size = min(max(args.limit * 6, 60), 100)
            pool = fetch_voices(
                api_key=api_key,
                limit=pool_size,
                gender=gender,
                all_languages=args.all,
            )

            already_used = used_voice_ids(
                cast,
                exclude_character=character_key,
            )
            if already_used:
                before = len(pool)
                pool = [
                    voice
                    for voice in pool
                    if str(voice.get("voice_id") or "").strip()
                    not in already_used
                ]
                removed = before - len(pool)
                if removed:
                    print(
                        f"Ignoradas {removed} voz(es) já usadas por "
                        "outros personagens."
                    )

            voices = rank_for_character(pool, profile, args.limit)
        else:
            voices = fetch_voices(
                api_key=api_key,
                limit=args.limit,
                gender=gender,
                all_languages=args.all,
            )
    except Exception as exc:
        print(f"\nERRO: {exc}", file=sys.stderr)
        return 1

    if not voices:
        print(
            "\nNenhuma voz encontrada com os filtros usados. "
            "Tente novamente adicionando --all."
        )
        return 1

    print(f"\nSelecionadas {len(voices)} vozes. Baixando previews...")
    save_catalog(
        output_dir=output_dir,
        voices=voices,
        character=character_key,
        profile=profile,
    )

    print()
    print("Concluído.")
    print(f"Pasta: {output_dir}")
    print("Catálogo: catalogo.json")

    if character_key:
        print()
        print(
            "Ouça os MP3s desta pasta e escolha pelo número. "
            "Exemplo: 'Navi = 003'."
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
