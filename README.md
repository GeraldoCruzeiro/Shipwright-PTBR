# The Legend of Zelda: Ocarina of Time — PT-BR para Ship of Harkinian

Projeto comunitário/fan-made baseado no **Ship of Harkinian**, com foco em oferecer uma experiência completa em **Português do Brasil** para *The Legend of Zelda: Ocarina of Time* no PC, incluindo **toda a legenda/textos do jogo em PT-BR** e **dublagem PT-BR**.

> **Importante:** este repositório **não contém ROM do jogo, `oot.o2r` extraído da ROM, nem arquivos proprietários da Nintendo**. Para jogar, você precisa possuir e fornecer uma cópia legal e compatível de *Ocarina of Time*. Este projeto não é afiliado, patrocinado ou endossado pela Nintendo, HarbourMasters, ElevenLabs ou pelos autores dos mods gráficos utilizados.

## Download

### Windows x64

👉 **[Baixar Shipwright-PTBR v1.0.1](https://github.com/GeraldoCruzeiro/Shipwright-PTBR/releases/download/v1.0.1/Shipwright-PTBR-v1.0.1-Windows-x64.zip)**

| Informação | Tamanho aproximado |
|---|---:|
| Download do ZIP | **1,03 GB** |
| Jogo pronto após instalar o pacote gráfico 4K + modelos 3DS | **25–30 GB** |
| Espaço livre recomendado para a primeira instalação | **35 GB ou mais** |

> O tamanho final pode variar um pouco conforme os arquivos gerados a partir da ROM, cache dos downloads e futuras versões dos mods. O perfil 4K é o padrão e é responsável pela maior parte do espaço utilizado.

Depois de baixar, extraia a pasta **fora do OneDrive**. Exemplos recomendados:

```text
C:\Games\Shipwright-PTBR
C:\Users\SeuUsuario\Games\Shipwright-PTBR
```

> **Não execute o jogo dentro de OneDrive, Área de Trabalho/Documentos sincronizados ou outra pasta gerenciada pelo OneDrive.** O Ship of Harkinian bloqueia esse cenário porque a sincronização pode causar problemas com arquivos gerados e configurações.

Depois execute:

```text
INSTALAR_E_JOGAR_PTBR.bat
```

O instalador prepara automaticamente o OoT Reloaded 4K e os modelos 3DS utilizados pelo projeto. Ao terminar, ele tenta iniciar o jogo automaticamente.

### Como abrir o jogo depois da instalação

Após a primeira instalação, **não é necessário executar o `INSTALAR_E_JOGAR_PTBR.bat` toda vez**.

Abra a pasta onde o Shipwright-PTBR foi extraído e dê **duplo clique em**:

```text
soh.exe
```

No Explorador de Arquivos do Windows ele normalmente aparece apenas como:

```text
soh
Tipo: Aplicativo
```

Esse é o executável usado para jogar normalmente.

Fluxo resumido:

```text
Primeira vez:
ROM compatível na pasta
        ↓
INSTALAR_E_JOGAR_PTBR.bat
        ↓
instala/prepara os gráficos
        ↓
o jogo abre

Próximas vezes:
soh.exe
        ↓
jogar
```

Se o instalador terminar e o jogo não abrir automaticamente, basta dar duplo clique em `soh.exe`.

Você pode executar `INSTALAR_E_JOGAR_PTBR.bat` novamente no futuro se precisar refazer/verificar a preparação dos mods gráficos. Isso não é necessário para iniciar o jogo no uso normal.

### Trocar o pacote gráfico entre 4K e HD

O perfil padrão do projeto usa **OoT Reloaded 4K**. Se o computador do usuário não rodar o 4K de forma satisfatória, é possível trocar somente o texture pack para **HD**, mantendo a tradução, dublagem, modelos 3DS e demais melhorias.

Os comandos abaixo devem ser executados **na pasta principal do jogo**, a mesma pasta onde estão:

```text
soh.exe
INSTALAR_E_JOGAR_PTBR.bat
scripts\
voices\
mods\
```

Exemplo de pasta:

```text
C:\Games\Shipwright-PTBR
```

#### Como abrir o PowerShell na pasta correta

1. Abra a pasta do Shipwright-PTBR no Explorador de Arquivos.
2. Clique na barra de endereço da janela.
3. Digite:

```text
powershell
```

4. Pressione **Enter**.

O PowerShell será aberto já apontando para a pasta do jogo.

#### Trocar de 4K para HD

Com o jogo fechado, execute:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File ".\scripts\ptbr_graphics\install_oot_reloaded.ps1" -OutputDir "." -Quality HD
```

Depois abra normalmente:

```text
soh.exe
```

#### Voltar de HD para 4K

Com o jogo fechado, execute na mesma pasta:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File ".\scripts\ptbr_graphics\install_oot_reloaded.ps1" -OutputDir "." -Quality 4K
```

Depois abra novamente:

```text
soh.exe
```

> **Importante:** depois de escolher o modo HD, use `soh.exe` para jogar normalmente. O `INSTALAR_E_JOGAR_PTBR.bat` usa o perfil 4K como padrão e pode reinstalar o 4K se for executado novamente.

> O pacote não inclui ROM. Você precisa fornecer localmente uma cópia legal e compatível de *The Legend of Zelda: Ocarina of Time*.

## O que esta versão adiciona

- **legenda/textos do jogo em Português do Brasil**, integrada diretamente ao código do Ship of Harkinian;
- tradução e revisão de **2.163 mensagens**, incluindo diálogos, caixas de texto, instruções, créditos e demais mensagens do jogo cobertas pelo projeto;
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

## Legenda e tradução PT-BR

O projeto inclui a **tradução completa para Português do Brasil das mensagens cobertas pelo jogo-base nesta versão**, com **2.163 mensagens revisadas** e integradas diretamente ao runtime do Ship of Harkinian.

Isso inclui, entre outros:

- diálogos de personagens e NPCs;
- falas de Navi e personagens principais;
- textos de história e cutscenes;
- instruções e mensagens de gameplay;
- textos de itens e interações;
- créditos e mensagens internas existentes no conjunto traduzido.

A tradução preserva os IDs, controles e marcadores do sistema original de mensagens para manter compatibilidade com o jogo.

Arquivos principais:

```text
soh/soh/Enhancements/PTBR/
```

Para detalhes técnicos e validação, consulte:

- [soh/soh/Enhancements/PTBR/LEIA-ME.md](soh/soh/Enhancements/PTBR/LEIA-ME.md)
- [soh/soh/Enhancements/PTBR/PTBR_VALIDATION_REPORT.md](soh/soh/Enhancements/PTBR/PTBR_VALIDATION_REPORT.md)

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

## Verificação e versões anteriores

Para verificar a integridade do download ou acessar outras versões:

- [SHA-256 da versão v1.0.1](https://github.com/GeraldoCruzeiro/Shipwright-PTBR/releases/download/v1.0.1/Shipwright-PTBR-v1.0.1-Windows-x64.zip.sha256)
- [Todas as Releases](https://github.com/GeraldoCruzeiro/Shipwright-PTBR/releases)

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
