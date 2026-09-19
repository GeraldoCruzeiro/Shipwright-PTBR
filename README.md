# The Legend of Zelda: Ocarina of Time — PT-BR para Ship of Harkinian

Projeto comunitário/fan-made baseado no **Ship of Harkinian**, com foco em oferecer uma experiência completa em **Português do Brasil** para *The Legend of Zelda: Ocarina of Time* no PC.

> **Importante:** este repositório **não contém ROM do jogo, `oot.o2r` extraído da ROM, nem arquivos proprietários da Nintendo**. Para jogar, você precisa possuir e fornecer uma cópia legal e compatível de *Ocarina of Time*. Este projeto não é afiliado, patrocinado ou endossado pela Nintendo, HarbourMasters, ElevenLabs ou pelos autores dos mods gráficos utilizados.

## O que esta versão adiciona

- tradução PT-BR integrada ao código do Ship of Harkinian;
- revisão de **2.163 mensagens** do jogo;
- dublagem PT-BR com seleção de falante por personagem e tratamento de IDs reutilizados;
- pacote final local validado com **2.971 WAVs**, sem arquivos vazios ou corrompidos;
- preset gráfico automático:
  - 60 FPS de interpolação;
  - resolução interna em 125%;
  - MSAA 4x;
  - VSync;
  - LOD de alta qualidade;
  - distância de atores em 2x;
  - itens/projéteis 3D;
  - suporte a fundos 3D;
- integração opcional e automatizada com **OoT Reloaded 4K**;
- integração seletiva com modelos 3DS de Link, NPCs, inimigos, animais, inventário, templos e backgrounds;
- scripts para instalação, validação, geração de vozes e empacotamento de releases.

## Instalação recomendada — Windows x64

A forma mais simples para usuários finais é baixar o pacote pronto na página **Releases** deste repositório.

1. Baixe o arquivo `Shipwright-PTBR-<versão>-Windows-x64.zip`.
2. Extraia para uma pasta comum, por exemplo `C:\Games\Shipwright-PTBR`.
3. Coloque na mesma pasta uma **ROM legal e compatível** de *Ocarina of Time* quando solicitado pelo Ship of Harkinian.
4. Execute:
   ```text
   INSTALAR_E_JOGAR_PTBR.bat
   ```
5. Na primeira execução, o instalador prepara os mods gráficos. O perfil padrão usa **OoT Reloaded 4K**, portanto o download pode passar de 4 GB.
6. O Ship of Harkinian processará sua ROM localmente e criará os arquivos necessários para execução.

A ROM permanece no seu computador. **Não envie ROMs, `oot.o2r` ou saves para este repositório.**

### Se o 4K ficar pesado

Troque apenas o texture pack para HD:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File ".\scripts\ptbr_graphics\install_oot_reloaded.ps1" -OutputDir "." -Quality HD
```

Para voltar ao 4K:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File ".\scripts\ptbr_graphics\install_oot_reloaded.ps1" -OutputDir "." -Quality 4K
```

## ROM compatível

Use uma ROM obtida legalmente de uma cópia que você possui. O projeto original mantém uma ferramenta para verificar compatibilidade:

- https://ship.equipment/

A versão usada durante o desenvolvimento deste projeto foi a variante **NTSC-U v1.2**, mas o suporte efetivo depende das versões aceitas pelo Ship of Harkinian.

## Dublagem PT-BR

O runtime procura os áudios em:

```text
voices\ptbr\
```

Formato:

```text
1000_00.wav
1000_01.wav
002D_00_operadora_boliche_bombchu.wav
002D_00_dono_tiro_ao_alvo.wav
```

Alguns `textId` são usados por mais de um personagem. Nesses casos, o código em `PTBRVoice.cpp` identifica o falante em runtime e seleciona a variante correta.

O pacote oficial de release deve incluir os WAVs prontos. **Os WAVs não ficam versionados no Git**, para evitar inflar o repositório e para separar código-fonte de artefatos distribuíveis.

Para gerar ou recriar a dublagem, consulte:

- [scripts/ptbr_dubbing/README.md](scripts/ptbr_dubbing/README.md)

A geração usa uma chave própria da ElevenLabs e pode consumir créditos. Nunca publique sua `ELEVENLABS_API_KEY`.

## Gráficos

O pacote gráfico foi montado para preservar o **OoT Reloaded 4K** como base e adicionar somente componentes 3D selecionados por cima.

### OoT Reloaded

O instalador baixa os arquivos diretamente da release oficial do projeto, valida SHA-256 e instala os `.o2r` em `mods\`.

- Projeto: https://github.com/GhostlyDark/OoT-Reloaded
- Versão atualmente fixada pelo instalador: `v11.0.0`
- Perfil padrão: `4K`

### Modelos 3DS

O script `scripts/ptbr_graphics/install_3d_models.ps1` consulta os arquivos diretamente no GameBanana e instala uma seleção compatível com o Reloaded:

- Djipi's 3DS Experience: https://gamebanana.com/mods/477979
- Playas 3DS Adult/Young Link: https://gamebanana.com/mods/475743

Para reduzir conflitos, o projeto não instala automaticamente os módulos globais `World`, `Scenes`, `Main Textures`, `Aria`, `Crescent` e outros componentes conhecidos por competir com o Reloaded.

## Tecnologias utilizadas

| Área | Tecnologia |
|---|---|
| Engine/port | Ship of Harkinian |
| Linguagem principal | C/C++20 |
| Build | CMake + MSVC/Ninja |
| Runtime gráfico | libultraship / Fast3D |
| Áudio | SDL2 |
| Tradução PT-BR | tabelas C++ integradas ao runtime |
| Dublagem | ElevenLabs + Python + FFmpeg |
| Automação | PowerShell |
| Texture pack | OoT Reloaded |
| Modelos 3D | Djipi's 3DS Experience + Playas 3DS Link |
| CI | GitHub Actions |

## Para desenvolvedores

Clone com submódulos:

```powershell
git clone --recursive https://github.com/GeraldoCruzeiro/Shipwright-PTBR.git
cd Shipwright-PTBR
```

Se já clonou sem submódulos:

```powershell
git submodule update --init --recursive
```

As instruções gerais de compilação do projeto-base permanecem em:

- [docs/BUILDING.md](docs/BUILDING.md)

Os downloads gráficos automáticos ficam **desativados por padrão em builds de desenvolvimento/CI**. Para instalá-los após compilar:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File ".\scripts\ptbr_graphics\install_oot_reloaded.ps1" -OutputDir ".\x64\Release" -Quality 4K
powershell -NoProfile -ExecutionPolicy Bypass -File ".\scripts\ptbr_graphics\install_3d_models.ps1" -OutputDir ".\x64\Release"
```

### Gerar o pacote público Windows

Depois de compilar `Release x64` e ter a dublagem em `x64\Release\voices\ptbr`:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File ".\scripts\ptbr_release\package_windows.ps1" -Version "v1.0.0"
```

O script gera um ZIP em `dist\`, remove ROMs, `oot.o2r`, saves, configurações pessoais e mods de terceiros já baixados, mas mantém o executável, `soh.o2r`, a dublagem e os instaladores que obtêm os mods a partir das fontes originais.

Para o fluxo completo de release + publicação do repositório, consulte:

- [docs/PUBLICACAO.md](docs/PUBLICACAO.md)

## Estrutura PT-BR

```text
soh/soh/Enhancements/PTBR/
├── PTBRData*.cpp
├── PTBRMessages.cpp
├── PTBRFont*.h
├── PTBRVoice.cpp
└── PTBR_VALIDATION_REPORT.md

scripts/
├── ptbr_dubbing/
├── ptbr_graphics/
└── ptbr_release/
```

## Créditos e direitos

Este projeto existe sobre trabalho de diversas comunidades. Os créditos detalhados, links para os projetos originais e observações de distribuição estão em:

- [docs/PTBR_CREDITOS_E_DIREITOS.md](docs/PTBR_CREDITOS_E_DIREITOS.md)
- [docs/CREDITS.md](docs/CREDITS.md)
- [NOTICE.md](NOTICE.md)

Créditos principais:

- **HarbourMasters / Ship of Harkinian** — port e infraestrutura principal;
- **Zelda Reverse Engineering Team** — trabalho de decompilação no qual o projeto-base depende;
- **libultraship** — camada de plataforma/renderização utilizada pelo Ship of Harkinian;
- **GhostlyDark e contribuidores — OoT Reloaded**;
- **Djipi — 3DS Experience**;
- **Playas — modelos 3DS de Link**;
- **ElevenLabs** — plataforma TTS usada na produção da dublagem;
- **FFmpeg** — conversão de áudio;
- **GeraldoCruzeiro / Shipwright-PTBR** — integração, tradução, revisão, dublagem e automações PT-BR deste fork.

*Nintendo, The Legend of Zelda, Ocarina of Time e personagens associados são marcas/propriedade de seus respectivos titulares. Este é um projeto de fãs não oficial.*

## Estado do projeto

A branch principal pública representa a versão integrada PT-BR. Para bugs específicos da tradução, dublagem ou integração gráfica, abra uma **Issue** com:

- local/cena;
- `textId`, se conhecido;
- personagem;
- print ou vídeo curto;
- trecho do log quando houver erro.

Para suporte geral do Ship of Harkinian não causado por este fork, consulte o projeto upstream:

- https://github.com/HarbourMasters/Shipwright
- https://www.shipofharkinian.com/
