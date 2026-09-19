# Publicação do Shipwright-PTBR

Guia para manter o repositório e gerar uma release pública sem incluir ROM, saves, chaves ou mods gráficos de terceiros.

## 1. Validar a branch principal

Antes de publicar uma versão:

```powershell
git switch main
git pull
git submodule update --init --recursive
```

Compile em `Release x64` e execute o jogo.

Valide:

- tradução;
- dublagem;
- troca correta de vozes;
- OoT Reloaded 4K;
- modelos/backgrounds 3DS;
- pelo menos uma sessão de jogo mais longa.

## 2. Conferir a dublagem

O empacotador espera os WAVs em:

```text
x64\Release\voices\ptbr
```

Ele bloqueia a geração se encontrar menos de 2.500 WAVs, como proteção contra publicar um pacote incompleto.

## 3. Gerar o ZIP público

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File ".\scripts\ptbr_release\package_windows.ps1" -Version "v1.0.0"
```

Saída:

```text
dist\Shipwright-PTBR-v1.0.0-Windows-x64.zip
dist\Shipwright-PTBR-v1.0.0-Windows-x64.zip.sha256
```

O script:

- copia o build Release;
- mantém a dublagem;
- remove `oot.o2r` / `oot-mq.o2r`;
- remove ROMs;
- remove saves/configurações pessoais;
- remove `mods\` já baixados;
- inclui os instaladores que baixam os mods gráficos das fontes originais;
- gera SHA-256 do ZIP.

## 4. Publicar a Release

Instale GitHub CLI:

- https://cli.github.com/

Autentique:

```powershell
gh auth login
```

Depois:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File ".\scripts\ptbr_release\publicar_release.ps1" -Version "v1.0.0" -MakePublic
```

O script cria a tag/release apontando para `main`, envia ZIP + SHA-256 e, com `-MakePublic`, muda o repositório para público usando o GitHub CLI.

Se preferir manter o repositório privado, omita `-MakePublic`.

## 5. Tornar o repositório público manualmente

Se não usar `-MakePublic`, faça pelo GitHub:

```text
Repository
→ Settings
→ General
→ Danger Zone
→ Change repository visibility
→ Change visibility
→ Public
```

Confirme o nome do repositório quando solicitado.

Faça isso **somente depois** de:

- confirmar que `.env` nunca foi commitado;
- revisar o histórico recente;
- confirmar que não há ROM ou `oot.o2r`;
- criar/validar a primeira release.

## 6. Depois da publicação

Verifique como visitante/anônimo:

- README abre corretamente;
- links funcionam;
- Release está visível;
- ZIP baixa;
- SHA-256 está presente;
- nenhuma ROM/chave/arquivo pessoal ficou exposto.

## 7. Atualizações futuras

Use tags incrementais, por exemplo:

```text
v1.0.1
v1.1.0
v2.0.0
```

Não substitua silenciosamente um ZIP já publicado. Para correções, crie uma nova versão.
