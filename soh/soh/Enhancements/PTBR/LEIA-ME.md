# Tradução PT-BR revisada

Revisão de 17/09/2026 para o projeto Ship of Harkinian 9.2.3 fornecido.

## Neste computador

Os arquivos revisados foram instalados em:

`C:\Users\Geraldo\Desktop\Shipwright-PTBR\soh\soh\Enhancements\PTBR`

Após a compilação Release, abra:

`C:\Users\Geraldo\Desktop\Shipwright-PTBR\x64\Release\soh.exe`

O executável Debug, atalhos e outras cópias do jogo não são atualizados por essa compilação.
Os arquivos `soh.o2r` e `oot.o2r` precisam continuar na pasta de execução. Não mova apenas o executável.
Nenhuma ROM, arquivo de jogo, configuração ou save foi incluído no pacote ou substituído pela revisão.

## Instalação em outra cópia do projeto

1. Guarde uma cópia da pasta PTBR anterior.
2. Coloque todos os arquivos `.cpp` e `.h` deste pacote em `soh/soh/Enhancements/PTBR`.
3. Reconfigure e recompile o projeto. Não misture os novos arquivos de dados com o cabeçalho antigo: os dados agora incluem `TYPE_POS`.
4. No Visual Studio, compile as fontes PTBR com `/utf-8`. Essa configuração já existe no projeto deste computador.

Trecho para um projeto MSVC sem essa configuração, dentro de `soh/CMakeLists.txt`:

```cmake
if(MSVC)
    set_source_files_properties(
        soh/Enhancements/PTBR/PTBRMessages.cpp
        soh/Enhancements/PTBR/PTBRData_0000_0FFF.cpp
        soh/Enhancements/PTBR/PTBRData_1000_1FFF.cpp
        soh/Enhancements/PTBR/PTBRData_2000_3FFF.cpp
        soh/Enhancements/PTBR/PTBRData_4000_FFFF.cpp
        PROPERTIES COMPILE_FLAGS "/utf-8"
    )
endif()
```

O projeto usa a descoberta de fontes da pasta Enhancements. Não deixe cópias antigas `.cpp` ativas com as mesmas funções.

## Conteúdo e limites

- 2.163 mensagens conferidas contra o arquivo inglês, incluindo créditos e entradas de depuração existentes.
- IDs, `TYPE_POS` e sequência completa de controles preservados.
- Revisão de concordância, preposições, contexto, gênero dos personagens, nomes de itens e instruções.
- Tabelas ordenadas corretamente para que a busca localize todas as mensagens.
- Fonte PT-BR composta em memória a partir da fonte original do próprio jogo. Nenhum recurso da ROM é distribuído.
- O ajuste de fonte requer texturas originais I4 de 16 x 16. Fontes substituídas por pacotes gráficos incompatíveis são ignoradas com aviso no log.
- Acentos usam apenas bytes abaixo de `0x9F`; `0x9F–0xAB` permanecem reservados para símbolos dos controles.
- A estimativa de largura usa tamanho e espaçamento padrão. Não equivale a uma inspeção de todas as cenas em execução.
- Textos novos de mods, randomizer, menus externos e mensagens ausentes do arquivo inglês estão fora deste conjunto.

Veja `PTBR_VALIDATION_REPORT.md` para resultados e limitações detalhados.
