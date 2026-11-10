"""
MÃOESTRO - Controle apresentações com os gestos das mãos

A webcam enxerga a mão, a IA do MediaPipe encontra 21 pontos nela e o
programa transforma gestos em mouse e teclado. Por isso funciona em
qualquer programa: Canva, PowerPoint, LibreOffice Impress, Paint...

  ☝  Indicador levantado  -> move o cursor
  🤏 Pinça                -> segura o clique (desenha)
  👋 Mão aberta deslizando -> próximo / anterior slide
  ✊ Mão fechada           -> nada acontece (pausa natural)

PARTE 1 (Seções 1 a 7): núcleo, codado junto na aula.
PARTE 2 (Seções 8 e 9): extras, mostrados se der tempo.

Rodar: python maestro.py            Q = sair | P = pausar
Emergência: leve o mouse de verdade até um canto da tela.
"""

# ##########################################################################
#  PARTE 1 - NÚCLEO (codar junto)
# ##########################################################################

# ==========================================================================
# SEÇÃO 1 - Importações e configurações
# ==========================================================================
import ctypes
import math
import os
import sys
import time
import urllib.request
from collections import deque

import cv2                      # OpenCV: câmera, imagens e desenhos
import mediapipe as mp          # MediaPipe: IA que encontra a mão
from mediapipe.tasks.python import BaseOptions, vision
import numpy as np              # NumPy: contas com números
import pyautogui                # PyAutoGUI: controla mouse e teclado

CAMERA = 0                # 0 = webcam padrão (troque para 1 se tiver outra)
MARGEM = 0.15             # borda da câmera ignorada: o dedo alcança os cantos da tela
SUAVIZACAO = 5            # maior = cursor mais suave (e mais lento)
LIMIAR_PINCA = 0.35       # distância polegar-indicador (em "tamanhos de mão") para clicar
DESLIZE_DISTANCIA = 0.15  # quanto a mão anda (fração da imagem) para trocar o slide...
DESLIZE_JANELA = 0.4      # ...em até quantos segundos
DESLIZE_ESPERA = 1.0      # segundos de espera entre um deslize e outro
MIRA_QUADROS = 8          # quadros apontando (~0,25 s) antes de a pinça poder clicar

pyautogui.PAUSE = 0           # sem isso ele espera 0,1 s após cada comando
pyautogui.FAILSAFE = True     # mouse no canto da tela = encerra (segurança)
LARGURA_TELA, ALTURA_TELA = pyautogui.size()


# ==========================================================================
# SEÇÃO 2 - Webcam e loop principal
# As linhas marcadas [Seção N] são digitadas quando chegarmos na Seção N.
# ==========================================================================
def main():
    backend = cv2.CAP_DSHOW if os.name == "nt" else cv2.CAP_ANY  # Windows abre mais rápido
    camera = cv2.VideoCapture(CAMERA, backend)
    detector = carregar_detector()                                   # [Seção 3]
    # Tudo que o programa precisa "lembrar" de um quadro para o outro
    estado = {"cursor": None, "clicando": False, "sem_pinca": 0, "mirando": 0, "pausado": False,
              "historico": deque(), "ultimo_deslize": 0.0, "direcao": None}
    inicio = time.time()

    try:
        while True:
            ok, frame = camera.read()
            if not ok:
                break
            frame = cv2.flip(frame, 1)      # espelha: mão para a direita = direita na tela
            agora = time.time()
            gesto = "NENHUM"

            pontos = detectar_mao(detector, frame, int((agora - inicio) * 1000))  # [Seção 3]
            if pontos is not None:                                            # [Seção 3]
                desenhar_mao(frame, pontos)                                   # [Seção 3]
                gesto = classificar_gesto(pontos)                             # [Seção 4]
                cv2.putText(frame, gesto, (10, 30), 0, 1, (0, 255, 255), 2)   # [Seção 4]
                if not estado["pausado"]:                                     # [Seção 5]
                    if gesto in ("APONTAR", "PINCA"):                         # [Seção 5]
                        mover_cursor(pontos[8], estado)                       # [Seção 5]
                    trocar_slide(pontos, gesto, estado, agora)                # [Seção 7]
            atualizar_clique("NENHUM" if estado["pausado"] else gesto, estado)  # [Seção 6]

            aplicar_extras(frame, pontos, gesto, estado, agora)   # [Parte 2] apague para desligar
            cv2.imshow("Maoestro", frame)
            tecla = cv2.waitKey(1) & 0xFF
            if tecla == ord("q"):
                break
            if tecla == ord("p"):
                estado["pausado"] = not estado["pausado"]
    except pyautogui.FailSafeException:
        print("Saída de emergência: mouse no canto da tela.")
    finally:
        # Haja o que houver: solta o botão do mouse e libera a câmera
        pyautogui.FAILSAFE = False
        if estado["clicando"]:
            pyautogui.mouseUp()
        camera.release()
        cv2.destroyAllWindows()


# ==========================================================================
# SEÇÃO 3 - IA encontra a mão (e desenhamos o esqueleto)
# ==========================================================================
URL_MODELO = ("https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
              "hand_landmarker/float16/latest/hand_landmarker.task")
ARQUIVO_MODELO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hand_landmarker.task")


def carregar_detector():
    if not os.path.exists(ARQUIVO_MODELO):          # baixa o modelo treinado só na 1ª vez
        print("Baixando o modelo de mãos (~8 MB)...")
        urllib.request.urlretrieve(URL_MODELO, ARQUIVO_MODELO)
    with open(ARQUIVO_MODELO, "rb") as arquivo:     # ler em memória evita erro com acentos na pasta
        modelo = arquivo.read()
    opcoes = vision.HandLandmarkerOptions(
        base_options=BaseOptions(model_asset_buffer=modelo),
        running_mode=vision.RunningMode.VIDEO,      # VIDEO: aproveita o quadro anterior
        num_hands=1)
    return vision.HandLandmarker.create_from_options(opcoes)


def detectar_mao(detector, frame, tempo_ms):
    """Retorna os 21 pontos da mão (x e y de 0 a 1) ou None."""
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)    # OpenCV usa BGR, MediaPipe usa RGB
    imagem = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
    resultado = detector.detect_for_video(imagem, tempo_ms)
    return resultado.hand_landmarks[0] if resultado.hand_landmarks else None


def para_pixels(ponto, frame):
    """Converte coordenada de 0 a 1 em pixel da imagem."""
    altura, largura = frame.shape[:2]
    return int(ponto.x * largura), int(ponto.y * altura)


def desenhar_mao(frame, pontos, cor=(0, 255, 0)):
    for conexao in vision.HandLandmarksConnections.HAND_CONNECTIONS:   # pares de pontos a ligar
        cv2.line(frame, para_pixels(pontos[conexao.start], frame),
                 para_pixels(pontos[conexao.end], frame), cor, 2)
    for ponto in pontos:
        cv2.circle(frame, para_pixels(ponto, frame), 5, (255, 255, 255), -1)

# Mapa dos pontos: 0 = pulso | 4 = polegar | 8 = indicador | 12 = médio | 16 = anelar | 20 = mínimo


# ==========================================================================
# SEÇÃO 4 - Quais dedos estão levantados? Que gesto é esse?
# ==========================================================================
def distancia(a, b):
    return math.hypot(a.x - b.x, a.y - b.y)


def dedos_levantados(pontos):
    """[polegar, indicador, médio, anelar, mínimo] -> True se esticado.
    Regra: a PONTA do dedo fica mais longe do pulso que a ARTICULAÇÃO do meio
    (funciona com a mão de pé ou deitada)."""
    polegar = distancia(pontos[4], pontos[17]) > distancia(pontos[3], pontos[17])  # polegar abre para o lado
    outros = [distancia(pontos[ponta], pontos[0]) > distancia(pontos[ponta - 2], pontos[0])
              for ponta in (8, 12, 16, 20)]
    return [polegar] + outros


def classificar_gesto(pontos):
    _, indicador, medio, anelar, minimo = dedos_levantados(pontos)
    tamanho_mao = distancia(pontos[0], pontos[9])   # "régua": vale perto ou longe da câmera

    # Pinça: pontas quase encostando E indicador à frente da base dele
    # (sem essa 2ª condição, fechar a mão viraria um clique falso)
    pinca = distancia(pontos[4], pontos[8]) < LIMIAR_PINCA * tamanho_mao
    if pinca and distancia(pontos[8], pontos[0]) > distancia(pontos[5], pontos[0]):
        return "PINCA"
    if indicador and not (medio or anelar or minimo):
        return "APONTAR"
    if indicador + medio + anelar + minimo >= 3:    # 3 de 4: no deslize algum dedo dobra
        return "MAO_ABERTA"
    if not (indicador or medio or anelar or minimo):
        return "PUNHO"
    return "NENHUM"


# ==========================================================================
# SEÇÃO 5 - O dedo vira mouse
# ==========================================================================
def mover_cursor(ponto, estado):
    # Converte a área ativa da câmera para a tela inteira (uma regra de três)
    alvo_x = np.interp(ponto.x, (MARGEM, 1 - MARGEM), (0, LARGURA_TELA - 1))
    alvo_y = np.interp(ponto.y, (MARGEM, 1 - MARGEM), (0, ALTURA_TELA - 1))
    if estado["cursor"] is None:
        estado["cursor"] = (alvo_x, alvo_y)
    # Suavização: anda só uma fração do caminho a cada quadro (tira a tremedeira)
    x, y = estado["cursor"]
    x += (alvo_x - x) / SUAVIZACAO
    y += (alvo_y - y) / SUAVIZACAO
    estado["cursor"] = (x, y)
    # Fica longe dos cantos exatos: eles são a saída de emergência
    x, y = min(max(x, 2), LARGURA_TELA - 3), min(max(y, 2), ALTURA_TELA - 3)
    if os.name == "nt":     # Windows: o moveTo "teleporta" e o Paint só vê início e fim do traço
        pyautogui.failSafeCheck()
        ctypes.windll.user32.mouse_event(0x8001, int(x * 65535 / (LARGURA_TELA - 1)),
                                         int(y * 65535 / (ALTURA_TELA - 1)), 0, 0)  # movimento real
    else:
        pyautogui.moveTo(x, y)


# ==========================================================================
# SEÇÃO 6 - A pinça vira clique (segurar o clique = desenhar)
# ==========================================================================
def atualizar_clique(gesto, estado):
    # Só clica se a pinça veio de um APONTAR firme: abrir/fechar a mão (ou gesticular)
    # passa por uma "pinça" rápida, e isso virava clique falso (e o slide avançava)
    if gesto == "PINCA" and (estado["clicando"] or estado["mirando"] >= MIRA_QUADROS):
        estado["sem_pinca"] = 0
        if not estado["clicando"]:
            pyautogui.mouseDown()               # aperta e SEGURA o botão
            estado["clicando"] = True
    elif estado["clicando"]:
        estado["sem_pinca"] += 1                # se a IA falhar em 1 quadro, o traço não quebra
        if estado["sem_pinca"] >= 3:
            pyautogui.mouseUp()
            estado["clicando"] = False
    estado["mirando"] = estado["mirando"] + 1 if gesto == "APONTAR" else 0


# ==========================================================================
# SEÇÃO 7 - Deslizar a mão aberta troca o slide
# ==========================================================================
def trocar_slide(pontos, gesto, estado, agora):
    historico = estado["historico"]
    if gesto != "MAO_ABERTA":       # sem apagar: 1 quadro borrado no meio não perde o deslize
        return
    # Guarda (tempo, posição x do centro da mão) só dos últimos DESLIZE_JANELA segundos
    historico.append((agora, pontos[9].x))
    while agora - historico[0][0] > DESLIZE_JANELA:
        historico.popleft()

    deslocamento = historico[-1][1] - historico[0][1]
    if abs(deslocamento) > DESLIZE_DISTANCIA and agora - estado["ultimo_deslize"] > DESLIZE_ESPERA:
        estado["direcao"] = "right" if deslocamento < 0 else "left"  # como no celular: puxar p/ esquerda = próximo
        pyautogui.press(estado["direcao"])     # setas funcionam em todo programa de slides
        estado["ultimo_deslize"] = agora
        historico.clear()


# ##########################################################################
#  PARTE 2 - EXTRAS (mostrar se der tempo; o núcleo funciona sem isto)
#  Para desligar tudo: apague a linha marcada [Parte 2] na Seção 2.
# ##########################################################################

# ==========================================================================
# SEÇÃO 8 - Atalhos: segurar 👍 ou ✌ por 1 s aperta uma tecla (+ confete)
#   python maestro.py canva | powerpoint | libreoffice | paint
# ==========================================================================
import random

# Tecla de cada gesto em cada programa. None = não envia nada (só festeja na tela),
# assim nenhum gesto aperta uma tecla com outro significado naquele programa.
PERFIS = {
    "canva":       {"JOINHA": "c",  "PAZ": "d"},   # confete / rufar de tambores
    "powerpoint":  {"JOINHA": None, "PAZ": "b"},   # b = tela preta (de novo = volta)
    "libreoffice": {"JOINHA": None, "PAZ": "b"},
    "paint":       {"JOINHA": None, "PAZ": None},
}
NOME_PERFIL = sys.argv[1].lower() if len(sys.argv) > 1 else "canva"
if NOME_PERFIL not in PERFIS:
    sys.exit(f"Perfil desconhecido. Use um destes: {', '.join(PERFIS)}")
TEMPO_SEGURAR = 1.0

if os.environ.get("XDG_SESSION_TYPE") == "wayland":
    print("AVISO: no Wayland o Python não controla o mouse. Na tela de login, "
          "clique na engrenagem e escolha 'Ubuntu on Xorg'.")


def gesto_especial(pontos):
    """Reconhece 👍 e ✌ (o núcleo os trata como PUNHO e NENHUM)."""
    polegar, indicador, medio, anelar, minimo = dedos_levantados(pontos)
    if polegar and not (indicador or medio or anelar or minimo) and pontos[4].y < pontos[5].y:
        return "JOINHA"                         # só o polegar, apontando para cima
    if indicador and medio and not (anelar or minimo):
        return "PAZ"
    return None


def checar_atalho(especial, estado, frame, agora):
    """Retorna o progresso (0 a 1) de quanto tempo o gesto está sendo segurado."""
    if especial is None:
        estado["segurando"] = None
        return 0.0
    if especial != estado["segurando"]:         # começou a segurar agora
        estado.update(segurando=especial, inicio_segurar=agora, disparou=False)
    progresso = min((agora - estado["inicio_segurar"]) / TEMPO_SEGURAR, 1.0)
    if progresso >= 1.0 and not estado["disparou"]:
        estado["disparou"] = True               # dispara uma vez só por gesto
        tecla = PERFIS[NOME_PERFIL][especial]
        if tecla:
            pyautogui.press(tecla)
        soltar_confete(estado, frame)
        estado["aviso"] = ("MANDOU BEM!" if especial == "JOINHA" else "PAZ E AMOR!", agora + 1.0)
    return progresso


def soltar_confete(estado, frame):
    """150 papeizinhos saindo de baixo, com velocidades aleatórias."""
    altura, largura = frame.shape[:2]
    for _ in range(150):
        estado["confetes"].append([largura / 2, altura, random.uniform(-9, 9), random.uniform(-22, -10),
                                   (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))])


def desenhar_confete(frame, estado):
    vivos = []
    for c in estado["confetes"]:                # c = [x, y, velocidade_x, velocidade_y, cor]
        c[0] += c[2]
        c[1] += c[3]
        c[3] += 0.6                             # gravidade
        if c[1] < frame.shape[0] + 10:
            cv2.rectangle(frame, (int(c[0]), int(c[1])), (int(c[0]) + 6, int(c[1]) + 10), c[4], -1)
            vivos.append(c)
    estado["confetes"] = vivos                  # quem caiu da tela é descartado


# ==========================================================================
# SEÇÃO 9 - Painel visual (HUD) e janela flutuante
# ==========================================================================
# Cores em BGR (Azul, Verde, Vermelho). O cv2.putText não escreve acentos.
VISUAL = {
    "APONTAR":    ("MOVENDO O CURSOR",            (255, 200, 0)),
    "PINCA":      ("DESENHANDO",                  (80, 80, 255)),
    "MAO_ABERTA": ("DESLIZE PARA TROCAR O SLIDE", (0, 220, 120)),
    "JOINHA":     ("SEGURE O JOINHA...",          (0, 215, 255)),
    "PAZ":        ("SEGURE O PAZ...",             (255, 120, 220)),
    "PUNHO":      ("PAUSA",                       (150, 150, 150)),
    "NENHUM":     ("---",                         (150, 150, 150)),
}


def preparar_janela():
    """Janela pequena no canto e sempre na frente, para não cobrir a apresentação."""
    cv2.namedWindow("Maoestro", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Maoestro", 480, 360)
    cv2.moveWindow("Maoestro", LARGURA_TELA - 500, ALTURA_TELA - 440)
    try:
        cv2.setWindowProperty("Maoestro", cv2.WND_PROP_TOPMOST, 1)
    except (AttributeError, cv2.error):
        pass                                    # nem todo sistema suporta; não é essencial


def escrever_centralizado(frame, texto, y):
    (largura_texto, _), _ = cv2.getTextSize(texto, cv2.FONT_HERSHEY_DUPLEX, 1.5, 3)
    x = (frame.shape[1] - largura_texto) // 2
    cv2.putText(frame, texto, (x, y), cv2.FONT_HERSHEY_DUPLEX, 1.5, (0, 0, 0), 7, cv2.LINE_AA)  # contorno
    cv2.putText(frame, texto, (x, y), cv2.FONT_HERSHEY_DUPLEX, 1.5, (255, 255, 255), 3, cv2.LINE_AA)


def aplicar_extras(frame, pontos, gesto, estado, agora):
    if "confetes" not in estado:                # 1ª vez: prepara janela e memória dos extras
        preparar_janela()
        estado.update(confetes=[], rastro=deque(maxlen=15), segurando=None, aviso=None,
                      fps=0.0, ultimo_quadro=agora)
    altura, largura = frame.shape[:2]

    # Atalhos (Seção 8) e cor do gesto atual
    especial = gesto_especial(pontos) if pontos is not None else None
    progresso = 0.0 if estado["pausado"] else checar_atalho(especial, estado, frame, agora)
    rotulo, cor = VISUAL[especial or gesto]

    # Área ativa: o que está dentro deste retângulo cobre a tela inteira
    cv2.rectangle(frame, (int(MARGEM * largura), int(MARGEM * altura)),
                  (int((1 - MARGEM) * largura), int((1 - MARGEM) * altura)), (90, 90, 90), 1)

    # Mão redesenhada na cor do gesto + rastro do indicador + anel de "segurando"
    if pontos is not None:
        desenhar_mao(frame, pontos, cor)
        estado["rastro"].append(para_pixels(pontos[8], frame))
        if progresso > 0:
            cv2.ellipse(frame, para_pixels(pontos[9], frame), (45, 45), -90, 0, 360 * progresso, cor, 6, cv2.LINE_AA)
    else:
        estado["rastro"].clear()
    for i in range(1, len(estado["rastro"])):
        cv2.line(frame, estado["rastro"][i - 1], estado["rastro"][i], cor, 1 + i // 3, cv2.LINE_AA)

    # Barra superior (cobre o texto simples da Seção 4)
    cv2.rectangle(frame, (0, 0), (largura, 50), (30, 30, 30), -1)
    cv2.circle(frame, (25, 25), 10, cor, -1, cv2.LINE_AA)
    status = "PAUSADO (aperte P)" if estado["pausado"] else rotulo
    cv2.putText(frame, status, (45, 33), cv2.FONT_HERSHEY_DUPLEX, 0.7, cor, 1, cv2.LINE_AA)
    estado["fps"] = 0.9 * estado["fps"] + 0.1 / max(agora - estado["ultimo_quadro"], 1e-6)
    estado["ultimo_quadro"] = agora
    cv2.putText(frame, f"{NOME_PERFIL.upper()} | {estado['fps']:.0f} FPS", (largura - 190, 32),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1, cv2.LINE_AA)

    # Avisos grandes no meio: troca de slide (Seção 7) e atalhos (Seção 8)
    if agora - estado["ultimo_deslize"] < 1.0:
        escrever_centralizado(frame, "PROXIMO >>" if estado["direcao"] == "right" else "<< ANTERIOR", altura // 2)
    elif estado["aviso"] and agora < estado["aviso"][1]:
        escrever_centralizado(frame, estado["aviso"][0], altura // 2)
    desenhar_confete(frame, estado)


# ==========================================================================
# SEMPRE A ÚLTIMA LINHA DO ARQUIVO: inicia o programa.
# (Digite na Seção 2 e escreva as próximas seções ACIMA dela.)
# ==========================================================================
if __name__ == "__main__":
    main()
