# Dublagem PT-BR — primeiro teste

A dublagem usa o mesmo `textId` das legendas PT-BR.

## Estrutura dos arquivos

Coloque os arquivos de voz na pasta abaixo, relativa ao diretório do executável do Ship of Harkinian:

```text
voices/
└── ptbr/
    ├── 1000_00.wav
    └── 1000_01.wav
```

O padrão de nome é:

```text
TEXTID_PAGINA.wav
```

Exemplos:

- `1000_00.wav` = mensagem 0x1000, primeira página.
- `1000_01.wav` = mensagem 0x1000, segunda página.

## Primeiro diálogo de teste — Navi (0x1000)

### 1000_00.wav

Texto falado:

> Você finalmente acordou! Sou Navi, a fada!

### 1000_01.wav

Texto falado:

> A Grande Árvore Deku pediu que eu fosse sua companheira de agora em diante! Muito prazer!

## Formato recomendado nesta primeira fase

Use WAV PCM.

O player converte automaticamente taxa de amostragem, formato e número de canais para o dispositivo de áudio do jogo, mas para manter os arquivos simples recomendamos:

- PCM 16-bit
- 44.1 kHz
- mono ou estéreo
- sem música de fundo
- sem silêncio longo no início ou no fim

## Comportamento esperado

1. A mensagem 0x1000 abre.
2. O jogo começa `1000_00.wav`.
3. Ao chegar ao `BOX_BREAK`, o áudio não avança sozinho.
4. Quando o jogador avança para a segunda caixa, começa `1000_01.wav`.
5. Se o diálogo for fechado ou substituído, a fala atual é interrompida.

## Próxima etapa

Depois que 0x1000 estiver validado no jogo:

1. criar o catálogo de personagens;
2. associar mensagens a personagem/voz;
3. gerar os WAVs em lote;
4. revisar pronúncia e interpretação;
5. comprimir para um formato menor quando o sistema estiver estável.
