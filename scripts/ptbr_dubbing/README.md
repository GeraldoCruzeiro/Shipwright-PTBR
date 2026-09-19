# Dublagem PT-BR - gerador de vozes

Este diretório contém o pipeline de dublagem PT-BR usado por `PTBRVoice.cpp`.

O mapeamento de falantes está separado do elenco:

- `speaker_map.json`: define quem fala cada `textId`/página;
- `voice_cast.json`: guarda a voz ElevenLabs escolhida para cada personagem;
- `character_profiles.json`: guarda a personalidade e os ajustes de atuação de cada personagem;
- `runtime_voice_variants.json`: define as variantes necessárias para IDs reutilizados por mais de um personagem;
- `generate_voices.py`: gera os WAVs finais;
- `PTBRVoice.cpp`: escolhe em runtime a variante correta quando um mesmo `textId` pode pertencer a atores diferentes.

## Pré-requisitos

- Python 3.10+;
- `ffmpeg` disponível no `PATH`;
- uma chave da ElevenLabs em `ELEVENLABS_API_KEY`.

A chave pode ficar no ambiente ou no arquivo `.env` da raiz do repositório:

```text
ELEVENLABS_API_KEY=sua_chave_aqui
```

Nunca commite a chave da API.

O gerador usa por padrão:

```text
model_id = eleven_flash_v2_5
speed = 0.88
output_format = mp3_44100_128
```

O MP3 retornado pela API é convertido localmente pelo `ffmpeg` para WAV PCM 16-bit, 44,1 kHz, mono, formato usado pelo runtime PT-BR.

## 1. Validar tudo sem consumir créditos

Antes de gerar qualquer áudio:

```powershell
py scripts\ptbr_dubbing\generate_voices.py --all --dry-run
```

O dry-run valida o elenco, os marcadores runtime e o mapeamento e mostra quais arquivos seriam produzidos. Ele não chama a API da ElevenLabs.

Também é possível validar somente um ID:

```powershell
py scripts\ptbr_dubbing\generate_voices.py --text-id 1000 --dry-run
```

Ou todas as falas de um personagem:

```powershell
py scripts\ptbr_dubbing\generate_voices.py --speaker navi --dry-run
```

## 2. Estimar o consumo antes de gastar creditos

Para calcular o tamanho real da dublagem sem chamar a API:

```powershell
py scripts\ptbr_dubbing\generate_voices.py --estimate
```

O relatorio usa exatamente a mesma limpeza de texto e a mesma configuracao de variantes runtime da geracao real. Ele mostra:

- quantidade de mensagens e paginas faladas;
- paginas estaticas e paginas runtime;
- quantidade de variantes runtime que exigem TTS;
- caracteres estaticos;
- caracteres runtime base;
- caracteres extras causados pelas variantes runtime;
- total de caracteres enviados ao TTS;
- quantidade estimada de chamadas TTS;
- uma referencia nominal de creditos em 1 credito por caractere.

O WAV base de um ID runtime nao adiciona custo: ele e apenas copiado da variante definida como fallback.

A estimativa nao le a chave da API e nao consome creditos da ElevenLabs.

Tambem e possivel estimar somente um personagem:

```powershell
py scripts\ptbr_dubbing\generate_voices.py --speaker navi --estimate
```

Ou IDs especificos:

```powershell
py scripts\ptbr_dubbing\generate_voices.py --text-id 1000 --estimate
```

A estimativa agora considera a taxa do modelo: Flash/Turbo v2/v2.5 usa como referencia 0,5 credito por caractere em planos self-service; Multilingual v2 usa 1 credito por caractere. Vozes compartilhadas com multiplicador proprio podem consumir mais.

## 3. Gerar um teste pequeno

Exemplo com o `textId 0x1000`:

```powershell
py scripts\ptbr_dubbing\generate_voices.py --text-id 1000 --overwrite
```

Para gerar somente uma pagina especifica de um dialogo, use `--page`. O indice comeca em 0:

```powershell
py scripts\ptbr_dubbing\generate_voices.py --text-id 1034 --page 1 --prosody-pauses --overwrite
```

Nesse exemplo apenas a pagina 1 de `0x1034` e sintetizada, economizando creditos durante os testes de personalidade. A opcao `--page` exige exatamente um `--text-id`.

A saída padrão é:

```text
x64\Release\voices\ptbr
```

Para um diálogo comum, os arquivos seguem o formato:

```text
1000_00.wav
1000_01.wav
1000_02.wav
```

## 4. Nome dinamico do jogador

O texto do jogo pode conter `<NAME>`, que e substituido em runtime pelo nome salvo pelo jogador.

Por padrao, a dublagem nao pronuncia um nome fixo. O gerador transforma `<NAME>` em uma pequena pausa natural antes de enviar a fala ao TTS. Assim:

```text
Texto:
Ola, <NAME>! Que bom ver voce novamente.

Legenda:
Ola, Geraldo! Que bom ver voce novamente.

Audio:
Ola... Que bom ver voce novamente.
```

Isso permite que a legenda continue usando qualquer nome escolhido no save sem obrigar a dublagem a falar "Link".

Se for necessario criar uma versao pessoal com nome fixo, ainda e possivel usar:

```powershell
py scripts\ptbr_dubbing\generate_voices.py --all --name Link
```

A opcao `--name` deve ser usada apenas quando se deseja deliberadamente fixar o nome falado nos WAVs.

## 5. IDs compartilhados e variantes runtime

Alguns IDs originais de Ocarina of Time são reutilizados por personagens diferentes.

Exemplo: `0x002D` pode pertencer à Operadora do Boliche Bombchu ou ao Dono da Galeria de Tiro.

Nesses casos o gerador cria variantes:

```text
002D_00_operadora_boliche_bombchu.wav
002D_00_dono_tiro_ao_alvo.wav
```

O `PTBRVoice.cpp` identifica o ator ativo e tenta primeiro o arquivo com o sufixo do falante.

Também existe:

```text
002D_00.wav
```

Esse arquivo base é apenas um fallback de segurança. Ele é copiado de uma das variantes definidas em `runtime_voice_variants.json`, sem fazer uma chamada TTS extra.

Outros casos runtime incluem:

- NPC masculino/feminino;
- Flat/Sharp;
- Galeria de Tiro/Zora do mergulho;
- lojistas que reutilizam mensagens genéricas;
- Dampé/Boliche/lojas;
- loja/Avó das Poções.

## 6. Gerar por personagem

Para gerar somente a Navi:

```powershell
py scripts\ptbr_dubbing\generate_voices.py --speaker navi
```

Para substituir WAVs já existentes:

```powershell
py scripts\ptbr_dubbing\generate_voices.py --speaker navi --overwrite
```

## 7. Gerar toda a dublagem

Só faça isso depois de validar uma amostra no jogo:

```powershell
py scripts\ptbr_dubbing\generate_voices.py --all
```

Para recriar todos os WAVs:

```powershell
py scripts\ptbr_dubbing\generate_voices.py --all --overwrite
```

A geração completa consome créditos da ElevenLabs. O fluxo recomendado é:

1. `--all --dry-run`;
2. `--estimate` para conhecer o volume total antes de assinar/consumir créditos;
3. gerar um ou poucos `textId`;
4. compilar/abrir o SoH e testar sincronização, volume e troca de páginas;
5. gerar um personagem completo;
6. somente então gerar `--all`.

## 8. Seleção de vozes

O elenco definitivo fica em:

```text
scripts\ptbr_dubbing\voice_cast.json
```

Cada personagem deve possuir um `voice_id` válido da ElevenLabs.

O arquivo antigo `voice_map.json` não é mais a fonte de verdade do gerador. O pipeline atual usa `speaker_map.json` + `voice_cast.json`.

Para consultar novas vozes da Voice Library quando necessário:

```powershell
py scripts\ptbr_dubbing\elevenlabs_library.py --character navi --limit 15
```

## 9. Modelo, velocidade e prosodia

A configuracao padrao do projeto foi fechada provisoriamente em:

```text
model_id = eleven_flash_v2_5
speed = 0.88
```

A velocidade ainda pode ser sobrescrita com `--speed`. O intervalo aceito pela ElevenLabs e de 0.7 a 1.2.

Para testar pausas adicionais de prosodia sem sobrescrever os WAVs anteriores:

```powershell
py scripts\ptbr_dubbing\generate_voices.py --text-id 1000 --prosody-pauses --output-dir x64\Release\voices\teste_flash_088_prosodia --overwrite
```

O modo `--prosody-pauses` mantem a pontuacao original e adiciona pausas SSML conservadoras apenas quando ainda existe fala depois do sinal. Os tempos atuais sao:

```text
,    0.12 s
; :  0.20 s
!    0.25 s
.    0.28 s
?    0.32 s
...  0.45 s
```

Para reduzir risco de artefatos, o gerador limita a no maximo 8 pausas SSML por pagina. Esse modo permanece opcional ate ser validado em jogo.

Use uma pasta de saida separada ao comparar configuracoes para nao sobrescrever os WAVs anteriores.

## 10. Personalidade vocal por personagem

Cada um dos 61 personagens possui um bloco `voice_settings` em:

```text
scripts/ptbr_dubbing/character_profiles.json
```

O gerador envia esses ajustes em cada requisicao da ElevenLabs:

```json
{
  "stability": 0.62,
  "similarity_boost": 0.87,
  "style": 0.12,
  "use_speaker_boost": true
}
```

A velocidade continua global em `0.88`, pois esse valor foi validado nos testes de Navi, Ganondorf e Grande Arvore Deku. A personalidade e diferenciada principalmente por:

- `stability`: menor = mais variacao/expressividade; maior = mais controle e consistencia;
- `similarity_boost`: preserva a identidade da voz escolhida;
- `style`: aumenta moderadamente o estilo natural da voz;
- `use_speaker_boost`: reforca a semelhanca com o locutor original.

Exemplos atuais:

```text
Navi:          stability 0.35 | similarity 0.82 | style 0.12
Ganondorf:     stability 0.62 | similarity 0.87 | style 0.12
Arvore Deku:   stability 0.70 | similarity 0.87 | style 0.06
Mido:          stability 0.36 | similarity 0.80 | style 0.14
Twinrova:      stability 0.44 | similarity 0.87 | style 0.18
NPC generico:  stability 0.55 | similarity 0.83 | style 0.04
```

Durante a geracao/dry-run, o terminal mostra os ajustes efetivamente usados para cada fala.

## 11. Diagnóstico

Se aparecer:

```text
ELEVENLABS_API_KEY nao encontrada
```

confira a variável de ambiente ou o `.env`.

Se aparecer:

```text
ffmpeg nao foi encontrado no PATH
```

instale/configure o ffmpeg e abra um novo terminal.

Se o jogo não encontrar uma variante runtime, o `PTBRVoice.cpp` registra um aviso e tenta o WAV base `ID_PAGINA.wav`.
