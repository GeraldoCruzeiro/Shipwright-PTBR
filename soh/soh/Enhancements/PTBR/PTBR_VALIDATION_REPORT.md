# Relatório da revisão PT-BR

Data: 17/09/2026. Base: `PTBR_MESSAGES_EN.txt` do projeto Shipwright-PTBR fornecido.

## Resultado

- Entradas de origem: **2.163**.
- Entradas conferidas individualmente contra o inglês: **2.163**.
- Entradas com alterações de texto em relação à versão anterior: **1.903**.
- Entradas conferidas e mantidas: **260**.
- Controles/tokens: **18.197**, na mesma ordem e com os mesmos argumentos por mensagem.
- IDs ausentes, extras ou duplicados: **0**.
- Diferenças em `TYPE_POS`: **0**, inclusive nos créditos.
- Mensagens com controles divergentes: **0**.
- Caracteres usados no texto sem conversão para a fonte: **0**.
- Resíduos conhecidos da tradução automática (`ZPP`, `ZZP`, `ZSP`, `recebeuu`, `recebeur`): **0**.
- Alertas finais da estimativa de largura: **0**. Foram ajustadas 43 linhas sinalizadas na primeira verificação.

Esta é uma revisão contextual assistida por IA. A validação estrutural não é uma garantia de ausência absoluta de problemas editoriais.

## Testes executados

- Compilação e execução de um teste C++ com o compilador de mensagens real e os quatro arquivos finais de dados.
- Busca por todos os 65.536 IDs possíveis: **2.163 mensagens encontradas**, sem duplicações.
- Comparação de `TYPE_POS` de cada entrada C++ com o arquivo inglês.
- Conversão de todas as mensagens em bytes do jogo: **2.163 aprovadas**.
- Maior mensagem codificada: **943 bytes**, abaixo do buffer de 1.280 bytes.
- Maior estimativa conservadora de página decodificada: **184 bytes**, abaixo do buffer de 200 bytes, incluindo expansão de nome e números.
- Teste das 24 letras acentuadas do conjunto PT-BR: **24 códigos distintos**, todos abaixo de `0x9F`.
- Teste de passagem literal dos 13 bytes `0x9F–0xAB`: **aprovado**.
- Teste da composição das 11 letras que faltavam: preservação do corpo original, resultado estável ao reaplicar e nenhuma alteração nos slots de botões.
- Prévia ampliada dos desenhos das letras inspecionada. Os glifos nativos dos botões `0x9F–0xAA` foram comparados byte a byte; `0xAB`, ausente no arquivo de recursos fornecido, foi protegido por teste com sentinela.
- Estimativa de largura baseada em `sFontWidths`, escala, `SHIFT`, ícone de item, recuo de escolhas e nome latino de até oito caracteres. Limite conservador usado: coordenada horizontal 283.
- Compilação Release completa do alvo `soh`: concluída nesta revisão.

Saída do teste C++: `messages=2163 max_raw_bytes=943 max_decoded_page=184 failures=0`.

## Correções do sistema

A tabela anterior não estava inteiramente ordenada, embora usasse busca binária. O teste inicial encontrou apenas 2.069 das 2.163 mensagens. A ordenação foi corrigida e todas são agora localizáveis.

O tipo e a posição da caixa passaram a vir explicitamente de `TYPE_POS`, evitando a consulta incorreta à tabela de diálogos comuns para mensagens de créditos.

A conversão anterior compartilhava alguns códigos de acentos e usava desenhos de letras europeias como substitutos. Foram separados, entre outros, `á/â` e `Á/Â`; os desenhos de `ã, õ, í, ó, ú` e das maiúsculas correspondentes são compostos em memória a partir da fonte original. Os bytes de controle e de botões não foram remapeados. A fonte nos arquivos do jogo não foi modificada.

## Revisão editorial

Foram corrigidos plurais, artigos, preposições, frases truncadas, traduções literais, inversões de sentido, gênero dos personagens e instruções dos itens. Exemplos:

- `0x7081`: restauração de “Porta do Tempo” e “Reino Sagrado”.
- `0x70CE`: Ganondorf foi **derrotado pelo garoto**, em vez de ter batido nele.
- `0x70DB`: restauração das maldições dirigidas a Zelda e aos Sábios.
- `0x7176`: Keaton está **na moda**, e não “muito gostoso”.
- `0x70F0–0x70F3`: preços de compra e condição de não desfazer a venda escritos naturalmente.
- Créditos `0x0500–0x0521`: nomes de pessoas e organizações restaurados exatamente a partir do original; apenas funções e títulos traduzidos.

Nomes como Hyrule, Kokiri, Goron, Zora, Saria, Link, Zelda, Ganondorf e outros personagens foram preservados. Itens, títulos e locais descritivos foram padronizados em português. Números, preços, ordem das escolhas e marcações originais foram mantidos na revisão contextual; a comparação automática estrita cobre controles, IDs e `TYPE_POS`.

## Pendências e limites

- **Entradas com erro estrutural detectado: nenhuma.**
- Não foi feita uma passagem completa pelo jogo nem inspeção visual de todas as 2.163 mensagens. Tempo de leitura em cenas com fechamento automático, paginação visual, nomes em alfabetos não latinos e configurações de espaçamento alteradas ainda precisam de teste em execução.
- A fonte composta exige as texturas originais I4 de 16 x 16. Um pacote gráfico que substitua essas texturas por outro formato é ignorado com aviso no log, podendo manter acentos incorretos naquele pacote.
- O conjunto traduzido é exatamente o do arquivo inglês fornecido. Menus externos, mensagens adicionais de mods/randomizer e strings ausentes dessa base não foram acrescentados.
- Esta compilação atualiza `x64/Release/soh.exe`, não cópias do jogo em outras pastas nem o executável Debug.

## Tokens por tipo

| Tipo | Quantidade |
| --- | ---: |
| `BACKGROUND` | 2 |
| `BOX_BREAK` | 1254 |
| `BOX_BREAK_DELAYED` | 52 |
| `BYTE` | 309 |
| `COLOR` | 3664 |
| `END` | 2036 |
| `EVENT` | 217 |
| `FADE` | 87 |
| `FADE2` | 48 |
| `FISH_INFO` | 11 |
| `HIGHSCORE` | 11 |
| `ITEM_ICON` | 143 |
| `MARATHON_TIME` | 1 |
| `NAME` | 163 |
| `NEWLINE` | 6034 |
| `OCARINA` | 16 |
| `PERSISTENT` | 54 |
| `POINTS` | 2 |
| `QUICKTEXT_DISABLE` | 730 |
| `QUICKTEXT_ENABLE` | 730 |
| `RACE_TIME` | 4 |
| `SFX` | 72 |
| `SHIFT` | 859 |
| `TEXTID` | 127 |
| `TEXT_SPEED` | 71 |
| `THREE_CHOICE` | 5 |
| `TIME` | 10 |
| `TOKENS` | 4 |
| `TWO_CHOICE` | 138 |
| `UNSKIPPABLE` | 1343 |
| **Total** | **18197** |
