# 🖐️ Mãoestro: controle apresentações com as mãos

Projeto de visão computacional em Python. A webcam enxerga a sua mão, a IA do
MediaPipe encontra 21 pontos nela e o programa transforma gestos em ações de
mouse e teclado. Funciona no **Canva, PowerPoint, LibreOffice Impress e Paint**.

| Gesto | Ação |
|---|---|
| ☝️ Só o indicador levantado | Move o cursor |
| 🤏 Pinça (polegar + indicador) | Segura o clique, ou seja, **desenha** |
| 👋 Mão aberta: pare um instante e deslize | ← próximo / → anterior slide |
| 👍 Joinha (segure 1 s) | Canva: confete 🎉 |
| ✌️ Paz (segure 1 s) | Canva: rufar de tambores · PowerPoint/LibreOffice: tela preta (repita para voltar) |
| ✊ Mão fechada | Nada acontece (pausa natural) |

## Arquivos

| Arquivo | O que é |
|---|---|
| `maestro.py` | O projeto inteiro. **Parte 1** (Seções 1–7): núcleo, codado junto na aula. **Parte 2** (Seções 8–9): extras |
| `ROTEIRO_AULA.md` | Roteiro do apresentador, com o tempo de cada seção |

## Instalação

> **Por que não usar Docker?** O programa precisa da webcam, de abrir janelas e
> de controlar o mouse **do seu computador**. Um container isola justamente isso.
> Com o Docker Desktop no Windows a webcam nem chega ao container. Um ambiente
> virtual (`venv`) resolve com 3 comandos e sem esses problemas.

### Ubuntu
```bash
sudo apt install python3-venv python3-tk
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

⚠️ **Importante no Ubuntu:** o Python só consegue controlar o mouse na sessão
**Xorg**. Confira com `echo $XDG_SESSION_TYPE`. Se aparecer `wayland`, saia da
sessão e, na tela de login, clique na engrenagem ⚙️ e escolha **"Ubuntu on Xorg"**.

### Windows
```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Como rodar
```bash
python maestro.py              # perfil Canva (padrão)
python maestro.py powerpoint
python maestro.py libreoffice
python maestro.py paint        # só mouse e desenho: nenhuma tecla é enviada
```
Na primeira execução o modelo da IA (~8 MB) é baixado automaticamente.

Depois de iniciar, **clique na apresentação** para ela receber o foco: é para
lá que vão as teclas. Na janela da câmera, **Q** sai e **P** pausa.
**Saída de emergência:** leve o mouse de verdade até um canto da tela.

## Dicas por programa

- **Canva:** apresente em tela cheia. Os efeitos (confete, tambores) só funcionam
  no modo apresentação pelo computador. Para desenhar, use o **editor**, com a ferramenta
  "Desenhar" na barra lateral.
- **PowerPoint:** antes de usar a pinça no modo apresentação, aperte **Ctrl+P** para
  ativar a caneta. Sem isso, o clique **avança o slide**. Use **Ctrl+A** para voltar à seta
  e **E** para apagar os desenhos.
- **LibreOffice Impress:** em *Apresentação de slides → Configurações da apresentação de
  slides*, marque **"Ponteiro do mouse como caneta"**. Sem isso, o clique avança o slide.
- **Paint:** é só pinçar e desenhar.

## Problemas comuns

| Problema | Solução |
|---|---|
| "Não consegui abrir a webcam" | Mude `CAMERA = 0` para `1` na Seção 1 |
| Cursor tremendo | Aumente `SUAVIZACAO` na Seção 1 |
| Cursor não alcança as bordas | Aumente `MARGEM` na Seção 1 |
| Clique dispara sozinho | Diminua `LIMIAR_PINCA` na Seção 1 |
| Ubuntu: o mouse não se mexe | Sessão Wayland: veja a instalação acima |
| Teclas não fazem nada | A apresentação não está em foco: clique nela |
| Com 2 monitores o cursor fica só em um | Use o datashow em modo **duplicar** tela |
