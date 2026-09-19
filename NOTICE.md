# NOTICE

Este repositório é um fork/projeto derivado do **Ship of Harkinian** com modificações voltadas à tradução, dublagem e apresentação gráfica em Português do Brasil.

## Não afiliação

Este projeto é comunitário e não oficial. Ele não é afiliado, patrocinado ou endossado pela Nintendo, HarbourMasters, ElevenLabs, GhostlyDark, Djipi, Playas ou qualquer outro detentor de direitos citado neste repositório.

**The Legend of Zelda**, **Ocarina of Time**, Nintendo e seus personagens, nomes, marcas, áudio, arte e demais materiais protegidos pertencem aos seus respectivos titulares.

## ROM e assets do jogo

Este repositório não deve conter:

- ROMs de *The Legend of Zelda: Ocarina of Time*;
- `oot.o2r` ou `oot-mq.o2r` gerados a partir de ROM;
- saves pessoais;
- chaves de API;
- outros arquivos proprietários extraídos de uma cópia do jogo.

O usuário deve fornecer localmente uma cópia legal e compatível do jogo. O Ship of Harkinian gera os assets necessários no computador do usuário.

## Código do projeto-base

Grande parte do código deste repositório deriva do projeto Ship of Harkinian e de suas dependências/submódulos.

Este arquivo **não relicencia** código, assets ou componentes de terceiros. Consulte os projetos originais, seus respectivos arquivos de licença, avisos e documentação para conhecer os termos aplicáveis a cada componente.

Projeto upstream:

- https://github.com/HarbourMasters/Shipwright

## Mods gráficos de terceiros

Os scripts deste repositório podem baixar conteúdo de terceiros diretamente das fontes originais. Esses arquivos não são incorporados ao histórico Git deste fork.

Fontes atualmente integradas:

- OoT Reloaded — https://github.com/GhostlyDark/OoT-Reloaded
- Djipi's 3DS Experience — https://gamebanana.com/mods/477979
- Playas 3DS Adult/Young Link — https://gamebanana.com/mods/475743

Cada projeto/mod permanece sujeito aos termos e permissões definidos por seu autor.

## Dublagem PT-BR

O código do pipeline de dublagem está neste repositório. Os áudios finais podem ser distribuídos separadamente em pacotes de release para evitar inflar o histórico Git.

A síntese foi produzida com ferramentas da ElevenLabs e processada com FFmpeg. O uso de serviços, modelos, vozes e conteúdo gerado deve respeitar os termos vigentes de cada provedor.

Nunca publique uma `ELEVENLABS_API_KEY` neste repositório.

## Tradução e integração PT-BR

As modificações específicas deste fork incluem, entre outras:

- integração de mensagens PT-BR;
- revisão textual;
- runtime de dublagem;
- mapeamento de personagens e variantes de voz;
- automação de instalação gráfica;
- preset gráfico;
- scripts de empacotamento e publicação.

Créditos detalhados estão em `docs/PTBR_CREDITOS_E_DIREITOS.md`.
