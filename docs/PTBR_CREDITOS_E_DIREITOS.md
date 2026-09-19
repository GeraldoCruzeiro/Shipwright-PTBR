# Créditos, componentes e direitos — Shipwright-PTBR

Este documento registra os principais componentes externos usados pelo projeto e a forma como eles entram na distribuição.

## Projeto-base

### Ship of Harkinian

Base principal do projeto.

- Projeto: https://github.com/HarbourMasters/Shipwright
- Site: https://www.shipofharkinian.com/
- Organização: HarbourMasters

O Ship of Harkinian fornece o port moderno, o runtime, a interface, os recursos de modding e a infraestrutura de extração necessária para executar Ocarina of Time a partir de uma cópia compatível fornecida pelo usuário.

### Zelda Reverse Engineering Team

O Ship of Harkinian depende do trabalho de decompilação/reengenharia do jogo realizado pela comunidade Zelda Reverse Engineering Team.

Os créditos completos do projeto-base permanecem em:

- [CREDITS.md](CREDITS.md)

### libultraship

Camada utilizada pelo Ship of Harkinian para abstração de plataforma, renderização, entrada, janela, áudio e recursos modernos.

Submódulo configurado neste repositório:

- https://github.com/kenix3/libultraship

### ZAPDTR / OTRExporter

Ferramentas usadas pelo pipeline de extração/conversão de recursos do projeto-base.

- https://github.com/harbourmasters/ZAPDTR
- https://github.com/harbourmasters/OTRExporter

## Tradução PT-BR

A integração PT-BR deste fork inclui:

- tabela de mensagens em Português do Brasil;
- preservação dos IDs originais;
- preservação de controles e marcadores de mensagem;
- suporte a caracteres acentuados no runtime;
- revisão de 2.163 mensagens;
- tratamento de contexto, gênero e terminologia;
- arquivos de validação específicos do projeto.

Arquivos principais:

```text
soh/soh/Enhancements/PTBR/
```

Integração e revisão PT-BR:

- **GeraldoCruzeiro / Shipwright-PTBR**

## Dublagem PT-BR

O runtime de dublagem foi adicionado especificamente neste fork.

Componentes:

- `PTBRVoice.cpp` / `PTBRVoice.h`;
- `speaker_map.json`;
- `voice_cast.json`;
- `character_profiles.json`;
- `runtime_voice_variants.json`;
- geradores e validadores Python em `scripts/ptbr_dubbing/`.

### ElevenLabs

A síntese das vozes foi produzida com a plataforma ElevenLabs.

- https://elevenlabs.io/

O repositório não contém chaves de API.

Os usuários que desejarem regenerar as vozes devem usar sua própria conta/chave e observar os termos vigentes da ElevenLabs.

### FFmpeg

Usado no pipeline para converter a saída TTS em WAV compatível com o runtime.

- https://ffmpeg.org/

## OoT Reloaded

Texture pack UHD/4K usado como base visual do perfil gráfico final.

- Autor/projeto: **GhostlyDark e contribuidores**
- Repositório: https://github.com/GhostlyDark/OoT-Reloaded
- Site indicado pelo projeto: https://evilgames.eu/texture-packs/oot-reloaded.htm

Este fork não versiona os arquivos `.o2r` do OoT Reloaded no Git.

O script:

```text
scripts/ptbr_graphics/install_oot_reloaded.ps1
```

baixa a release diretamente da fonte oficial e valida os hashes configurados antes da instalação.

## Djipi's 3DS Experience

Usado de forma seletiva para complementar a apresentação 3D.

- Autor: **Djipi**
- Página: https://gamebanana.com/mods/477979

O instalador seleciona componentes específicos e evita módulos globais que competem com OoT Reloaded.

São usados seletivamente elementos como:

- animais;
- inventário;
- templos;
- NPCs;
- inimigos;
- backgrounds 3DS e texturas pareadas necessárias aos modelos selecionados.

São excluídos do fluxo automático componentes como:

- Main Textures;
- World;
- Scenes;
- Aria;
- Crescent;
- pacotes opcionais conflitantes.

O conteúdo é baixado diretamente do GameBanana no computador do usuário.

## Playas 3DS Adult/Young Link

Usado para os modelos 3DS de Link criança e adulto.

- Autor/página: **Playas**
- https://gamebanana.com/mods/475743

O conteúdo é obtido diretamente do GameBanana pelo instalador do projeto.

## Nintendo / The Legend of Zelda

Nintendo, The Legend of Zelda, Ocarina of Time, personagens, nomes, músicas, áudio, arte, design e demais elementos protegidos pertencem aos seus respectivos titulares.

Este projeto:

- é não oficial;
- não é afiliado à Nintendo;
- não inclui ROM;
- não inclui `oot.o2r`/assets extraídos da ROM;
- exige que o usuário forneça localmente uma cópia legal e compatível.

## Distribuição

O modelo de distribuição adotado pelo Shipwright-PTBR separa:

### Versionado no Git

- código-fonte;
- tradução;
- runtime da dublagem;
- mapeamentos;
- scripts de geração;
- scripts de instalação;
- documentação;
- automações de build.

### Pacote oficial de release

Pode conter:

- binário compilado do fork;
- `soh.o2r` do projeto-base;
- arquivos necessários à execução;
- pacote de vozes PT-BR produzido para este projeto;
- scripts que baixam os mods gráficos das fontes originais.

### Não distribuir neste repositório/release

- ROM;
- `oot.o2r`;
- `oot-mq.o2r`;
- saves pessoais;
- chaves de API;
- caches locais;
- mods gráficos de terceiros já baixados, salvo autorização expressa dos respectivos autores.

## Licenciamento

Este documento é um aviso de atribuição e distribuição, não uma tentativa de relicenciar código ou conteúdo de terceiros.

Antes de redistribuir qualquer componente externo, consulte a licença, os termos e as permissões do projeto original correspondente.
