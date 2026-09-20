# Shipwright-PTBR v1.0.2

Correção do instalador gráfico para computadores de usuários finais que não possuem CMake ou 7-Zip instalados.

## Corrigido

- o instalador do OoT Reloaded não depende mais de CMake/Visual Studio/7-Zip previamente instalados;
- se o Windows `tar.exe` não suportar o codec LZMA/7z, o instalador baixa automaticamente o executável oficial portátil `7zr.exe`;
- o `7zr.exe` é obtido da release oficial do projeto 7-Zip e validado por SHA-256 antes do uso;
- o arquivo fica em cache local e não precisa ser baixado novamente nas próximas instalações;
- mantidas as correções anteriores para caminhos com espaços e detecção de execução dentro do OneDrive.

## Mantido

- legenda PT-BR;
- dublagem PT-BR;
- OoT Reloaded 4K/HD;
- modelos e backgrounds 3DS;
- preset gráfico PT-BR;
- inicialização simplificada por `INSTALAR_E_JOGAR_PTBR.bat`.

## Importante

A release não inclui ROM, `oot.o2r` ou `oot-mq.o2r`. O usuário deve fornecer localmente uma cópia legal e compatível de Ocarina of Time.
