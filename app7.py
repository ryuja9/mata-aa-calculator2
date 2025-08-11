# app7.py
import streamlit as st
import os
import itertools
from treys import Card, Evaluator

st.set_page_config(page_title="Calculadora Mata AA (exacta - 1 carta faltante)", layout="wide")
st.title("Calculadora Mata AA — Exacta (1 carta faltante)")

# ----------------------------
# Configuración de cartas / imágenes
# ----------------------------
RANKS = ['a', 'k', 'q', 'j', '10', '9', '8', '7', '6', '5', '4', '3', '2']  # orden póker visual
SUITS = ['s', 'h', 'd', 'c']  # picas, corazones, diamantes, tréboles
DECK = [r + s for r in RANKS for s in SUITS]  # formato 'as', '10h', 'kd', etc.

IMAGES_DIR = "images"

def image_path(card):
    """Devuelve path a la imagen (ej. images/10h.png)."""
    return os.path.join(IMAGES_DIR, f"{card}.png")

def card_for_treys(card):
    """Convierte '10h' -> 'Th', 'as' -> 'As' para treys.Card.new."""
    rank = card[:-1]
    suit = card[-1]
    if rank == '10':
        r = 'T'
    else:
        r = rank.upper()
    return f"{r}{suit}"

# ----------------------------
# Interfaz: selectboxes (evita duplicados) y mostrar imágenes
# ----------------------------
def select_n_cards(label, n, used):
    """Selector secuencial de n cartas, bloqueando 'used'."""
    picked = []
    for i in range(n):
        options = [""] + [c for c in DECK if c not in used and c not in picked]
        sel = st.selectbox(f"{label} #{i+1}", options, key=f"{label}_{i}")
        if sel and sel != "":
            picked.append(sel)
    return picked

st.markdown("**Instrucciones:** selecciona 4 cartas para Jugador 1, 4 para Jugador 2, y las 3 ayudas. \
(La simulación calculará exactamente la equity suponiendo que falta 1 carta por repartir a cada jugador).")

# Recolectar selecciones, evitando duplicados globales
used_global = []

col1, col2, col3 = st.columns([1,1,1])

with col1:
    st.subheader("Jugador 1 (4 cartas actuales)")
    p1 = select_n_cards("J1", 4, used_global)
    used_global += p1

with col2:
    st.subheader("Jugador 2 (4 cartas actuales)")
    p2 = select_n_cards("J2", 4, used_global)
    used_global += p2

with col3:
    st.subheader("Ayudas (elige 3)")
    helps = select_n_cards("Help", 3, used_global)
    used_global += helps

# Mostrar imágenes de lo seleccionado (si ya elegido)
def show_selected_section(title, cards):
    if not cards: 
        return
    st.markdown(f"**{title}**")
    cols = st.columns(len(cards))
    for c, col in zip(cards, cols):
        with col:
            img_path = image_path(c)
            if os.path.isfile(img_path):
                st.image(img_path, width=90)
            else:
                st.write(c.upper())

st.write("---")
show_selected_section("Jugador 1", p1)
show_selected_section("Jugador 2", p2)
show_selected_section("Ayudas", helps)
st.write("---")

# ----------------------------
# Lógica: evaluar mejor mano de 5 cartas para un jugador, con opción de usar 0 o 1 ayuda
# ----------------------------
evaluator = Evaluator()

def best_score_for_player(five_cards, helps_list):
    """
    five_cards: lista de 5 cartas en formato 'as','10h',...
    helps_list: lista de 3 ayudas en mismo formato
    Devuelve el score mínimo (treys: menor => mejor).
    La lógica probada: 
      - probar la mano sin ayuda (las 5 propias),
      - probar cada ayuda substituyendo una de las 5 cartas (4 propias + 1 ayuda).
    """
    best = 10**9
    # Convertir la lista de 5 cartas a enteros treys
    treys_hand_base = [Card.new(card_for_treys(c)) for c in five_cards]
    # Opciones: sin ayuda
    try:
        score = evaluator.evaluate(treys_hand_base, [])  # funciona para 5-cartas
    except Exception:
        # fallback: evaluar pasando mano como board si la API varía
        score = evaluator.evaluate([], treys_hand_base)
    if score < best:
        best = score
    # Con cada ayuda (reemplazando una carta propia)
    for h in helps_list:
        h_card = Card.new(card_for_treys(h))
        for i in range(len(treys_hand_base)):
            mano_mod = treys_hand_base[:i] + treys_hand_base[i+1:] + [h_card]
            try:
                sc = evaluator.evaluate(mano_mod, [])
            except Exception:
                sc = evaluator.evaluate([], mano_mod)
            if sc < best:
                best = sc
    return best

# ----------------------------
# Cálculo exacto de equity (todas las combinaciones de 1 carta para J1 y 1 para J2)
# ----------------------------
def calculate_exact_equity(p1_cards_4, p2_cards_4, helps_3):
    # cartas usadas
    used = set(p1_cards_4 + p2_cards_4 + helps_3)
    remaining = [c for c in DECK if c not in used]
    wins1 = wins2 = ties = 0
    total = 0

    # Recorremos todas las cartas posibles para J1 y J2 (ordenadas, sin repetición)
    for c1 in remaining:
        for c2 in remaining:
            if c1 == c2:
                continue
            full1 = p1_cards_4 + [c1]  # 5 cartas finales J1
            full2 = p2_cards_4 + [c2]  # 5 cartas finales J2

            score1 = best_score_for_player(full1, helps_3)
            score2 = best_score_for_player(full2, helps_3)

            if score1 < score2:
                wins1 += 1
            elif score2 < score1:
                wins2 += 1
            else:
                ties += 1
            total += 1

    # evitar división por cero (no debería pasar)
    if total == 0:
        return 0.0, 0.0, 0.0
    return wins1 / total * 100.0, wins2 / total * 100.0, ties / total * 100.0

# ----------------------------
# Botón y despliegue de resultados
# ----------------------------
if st.button("Calcular equity exacta"):
    if len(p1) != 4 or len(p2) != 4 or len(helps) != 3:
        st.error("Debes seleccionar exactamente 4 cartas para cada jugador y 3 ayudas.")
    else:
        with st.spinner("Calculando (recorremos todas las combinaciones posibles)..."):
            eq1, eq2, tie = calculate_exact_equity(p1, p2, helps)
        st.success("Resultado (exacto):")
        st.write(f"Jugador 1: **{eq1:.3f}%**")
        st.write(f"Jugador 2: **{eq2:.3f}%**")
        st.write(f"Empate: **{tie:.3f}%**")
