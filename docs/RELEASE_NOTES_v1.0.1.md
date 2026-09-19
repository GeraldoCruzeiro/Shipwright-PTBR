# Shipwright-PTBR v1.0.1

Correção rápida do instalador Windows da versão pública inicial.

## Corrigido

- `INSTALAR_E_JOGAR_PTBR.bat` agora funciona corretamente quando o jogo está em caminhos com espaços, como:
  ```text
  C:\Users\Usuario\OneDrive\Desktop\Nova pasta
  ```
- removida a passagem problemática de um caminho terminado em barra invertida para `powershell.exe`;
- `setup_release.ps1` agora normaliza e valida `AppDir` de forma defensiva antes de usar `Resolve-Path`.

## Mantido

Todo o conteúdo da v1.0.0 permanece:

- legenda PT-BR;
- dublagem PT-BR;
- OoT Reloaded 4K/HD via instalador;
- modelos e backgrounds 3DS;
- preset gráfico PT-BR;
- inicialização simplificada pelo arquivo `INSTALAR_E_JOGAR_PTBR.bat`.

## Importante

A release não inclui ROM, `oot.o2r` ou `oot-mq.o2r`. O usuário deve fornecer localmente uma cópia legal e compatível de Ocarina of Time.
