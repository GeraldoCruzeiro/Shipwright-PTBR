# Dublagem PT-BR - gerador de vozes

Este diretório automatiza a geração dos WAVs usados por `PTBRVoice.cpp`.

## Pré-requisitos

- Python
- `edge-tts`
- `ffmpeg` disponível no PATH

Instalação do edge-tts:

```powershell
py -m pip install --upgrade edge-tts
```

## Teste inicial da Navi

Na raiz do repositório:

```powershell
py scripts\ptbr_dubbing\generate_voices.py --text-id 1000 --overwrite
```

O script lê a tradução de `0x1000`, separa as páginas em `<BOX_BREAK>`,
gera os áudios e grava diretamente em:

```text
x64\Release\voices\ptbr\1000_00.wav
x64\Release\voices\ptbr\1000_01.wav
```

## Visualizar sem gerar áudio

```powershell
py scripts\ptbr_dubbing\generate_voices.py --text-id 1000 --dry-run
```

## Mapa de vozes

O arquivo `voice_map.json` define a voz por mensagem.

Uma chave como:

```json
"1000": {
  "speaker": "Navi",
  "voice": "pt-BR-ThalitaMultilingualNeural",
  "rate": "+5%",
  "pitch": "+20Hz"
}
```

vale para todas as páginas do text ID `0x1000`.

Também é possível configurar uma página específica:

```json
"1015:02": {
  "speaker": "Grande Arvore Deku",
  "voice": "NOME_DA_VOZ",
  "rate": "-5%",
  "pitch": "-20Hz"
}
```

A configuração específica da página tem prioridade sobre a configuração do text ID.

## Gerar todos os IDs já cadastrados

```powershell
py scripts\ptbr_dubbing\generate_voices.py --configured --overwrite
```

Não use uma única voz para o jogo inteiro. O fluxo recomendado é cadastrar cada personagem
no `voice_map.json` e então gerar os IDs correspondentes.


## Escolher as vozes dos personagens

Antes de gerar o jogo inteiro, gere amostras das vozes PT-BR disponíveis:

```powershell
py scripts\ptbr_dubbing\preview_voices.py
```

As amostras são salvas em:

```text
dublagem_vozes_teste
```

Todos os arquivos usam o mesmo texto para facilitar a comparação de timbre.
Depois de ouvir, escolha uma voz para cada personagem principal antes de preencher
o `voice_map.json`.
