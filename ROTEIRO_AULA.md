# 🎤 Roteiro da aula: Mãoestro (60 min)

Um arquivo só: `maestro.py`. A turma digita a **Parte 1** (Seções 1 a 7) junto com você,
na ordem do arquivo. A **Parte 2** (Seções 8 e 9) é só para mostrar no final.

**Como funciona a digitação:** a Seção 2 cria o loop principal. Nele, as linhas marcadas
`# [Seção N]` só são digitadas quando chegarmos na Seção N. Assim o programa
**roda ao fim de cada seção**.

| Parte | Linhas de código | Linhas no arquivo (com comentários) |
|---|---|---|
| Parte 1: núcleo (codar junto) | 145 | ~240 |
| Parte 2: extras (só mostrar) | 107 | ~160 |

## ✅ Antes da aula
- [ ] Pedir que a turma instale tudo antes (seção "Instalação" do README)
- [ ] Ubuntu: confirmar a sessão **Xorg** no laboratório (`echo $XDG_SESSION_TYPE`)
- [ ] Rodar uma vez com internet para baixar o `hand_landmarker.task`.
      Leve esse arquivo num pendrive para quem não conseguir baixar
- [ ] Testar na sala, com a luz de lá. Deixar os slides no Canva e o Paint abertos
- [ ] **Para ganhar tempo:** mandar a Seção 1 (imports e configurações) no grupo da
      turma para eles colarem. Economiza uns 4 minutos de digitação

---

## 0–5 min · 🎬 Abertura
Rode o arquivo completo (`python maestro.py canva`) e apresente os primeiros slides
**só com a mão**. Desenhe algo, segure o 👍 → confete 🎉.
> "Em uma hora, vocês vão construir isso."

## 5–10 min · Conceitos
- O computador vê a imagem como uma matriz de números (pixels)
- O **MediaPipe** é um modelo já treinado que acha **21 pontos** na mão. Mostre a imagem numerada
- Fluxo: `câmera → IA acha a mão → qual gesto? → ação (mouse/teclado)`
- A sacada: simulando mouse e teclado, funciona em **qualquer** programa

## 10–14 min · ✍️ Seção 1: importações e configurações (21 linhas)
- Para que serve cada biblioteca
- Configurações no topo: dá para ajustar sem mexer na lógica
- `pyautogui.PAUSE = 0` e o `FAILSAFE` (canto da tela = emergência)

## 14–22 min · ✍️ Seção 2: webcam e loop (28 linhas, **sem** as marcadas `[Seção N]`)
- O loop faz, a cada quadro: `ler → espelhar → mostrar → checar tecla`
- `try/finally`: mesmo que dê erro, o mouse é solto e a câmera é liberada
- A linha `if __name__ == "__main__": main()` vai no **fim** do arquivo e as próximas
  seções entram **acima** dela
- ▶️ **Rodar:** a webcam aparece espelhada

## 22–31 min · ✍️ Seção 3: a IA encontra a mão (32 linhas)
- O modelo é baixado só na 1ª vez e lido em memória (evita erro com acentos no caminho)
- **BGR × RGB:** o OpenCV e o MediaPipe guardam as cores em ordens diferentes
- As coordenadas vêm **de 0 a 1** e é preciso converter para pixels (`para_pixels`)
- No loop: as 3 linhas `[Seção 3]` (detector, detectar, desenhar)
- ▶️ **Rodar:** o esqueleto da mão aparece

## 31–38 min · ✍️ Seção 4: que gesto é esse? (22 linhas). **O coração**
- Dedo esticado = **ponta mais longe do pulso que a articulação**.
  Pergunte: por que distância e não só o `y`? (Resposta: funciona com a mão deitada)
- `tamanho_mao` é a "régua" que faz a pinça funcionar perto ou longe da câmera
- O truque da pinça: sem a 2ª condição, fechar a mão vira um clique falso
- ▶️ **Rodar:** o nome do gesto aparece na tela

## 38–42 min · ✍️ Seção 5: o dedo vira mouse (13 linhas)
- `np.interp`: a área ativa da câmera vira a tela inteira (regra de três)
- **Suavização:** mostre o cursor com `SUAVIZACAO = 1` e depois com `5`
- ▶️ **Rodar:** o cursor segue o dedo 🤯

## 42–46 min · ✍️ Seção 6: a pinça vira clique (12 linhas)
- `mouseDown`/`mouseUp`: segurar o botão é o que permite desenhar
- Tolerância de 3 quadros: se a IA falhar em 1 quadro, o traço não quebra
- ▶️ **Rodar no Paint:** todo mundo desenhando no ar

## 46–51 min · ✍️ Seção 7: deslizar troca o slide (15 linhas)
- `deque` guarda as posições dos últimos 0,4 s
- Andou mais de 25% da imagem nesse tempo = deslize, com 1 s de espera entre deslizes
- ▶️ **Rodar no Canva/PowerPoint:** trocar slides com a mão

## 51–55 min · 👀 Parte 2: extras (só mostrar)
Rode o arquivo completo e mostre:
- **Seção 8:** 👍/✌ segurados por 1 s + perfis por programa (`python maestro.py powerpoint`)
- **Seção 9:** painel com cores por gesto, rastro do dedo, anel de progresso e janela no canto
- Ponto de projeto: tudo se liga com **uma linha** no loop (`aplicar_extras`), sem mexer no núcleo

## 55–60 min · 🎮 Dinâmica e encerramento
- **Desenho às cegas:** um voluntário desenha no Paint só com a mão e a turma adivinha
- Se possível, convide o professor para controlar os seus slides

---

## ⏱️ Se o tempo apertar
| Atraso | Corte |
|---|---|
| ~4 min | Seção 1 colada do grupo, em vez de digitada |
| ~5 min | Seção 7: mostrar pronta e explicar, sem digitar |
| ~5 min | Parte 2: mostrar só o confete |

## 🆘 Se algo der errado ao vivo
| Situação | O que fazer |
|---|---|
| Alguém atrasou | Copiar a função pronta do seu arquivo: cada função é independente |
| Cursor enlouqueceu | ✊ (nada acontece) ou **P** na janela da câmera |
| Clique preso | Mouse até um canto da tela: o programa encerra e solta o clique |
| Internet caiu | Use LibreOffice ou Paint |
