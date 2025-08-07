import streamlit as st
import random
import itertools
from collections import Counter
from PIL import Image
import os

st.set_page_config(layout="wide")

# Cargar imágenes
def load_card_image(card):
    path = f"images/{card}.png"
    if os.path.exists(path):
        return Image.open(path)
    else:
        return None

# Generar todas las cartas
suits = ['c', 'd', 'h', 's']
ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'j', 'q', 'k', 'a']
all_cards = [r + s for r in ranks for s in suits]

# Función para seleccionar cartas sin duplicados
def select_cards(label, selected_cards, num_cards=4):
    cols = st.columns(num_cards)
    picked = []
    for i in range(num_cards):
        with cols[i]:
            options = [c for c in all_cards if c not in selected_cards + picked]
            choice = st.selectbox(f"{label} {i+1}", [""] + options, key=f"{label}_{i}")
            if choice:
                picked.append(choice)
    return picked

# Evaluador de manos simplificado para determinar ganadores
def evaluate_hand(cards, help_cards):
    """
    Devuelve la mejor mano posible con las 5 cartas + una de las ayudas (opcional).
    Si la mejor mano se forma con las 5 cartas propias, también es válida.
    """
    best = None
    for help_card in help_cards + [None]:  # intentamos con cada ayuda o sin usar ayuda
        total = cards.copy()
        if help_card:
            total.append(help_card)
        combos = itertools.combinations(total, 5)
        max_score = max(hand_rank(list(combo)) for combo in combos)
        if best is None or max_score > best:
            best = max_score
    return best

# Asignar valor numérico a manos (simplificado)
def hand_rank(hand):
    """
    Da una puntuación numérica a la mano. Cuanto mayor, mejor.
    No es perfecto pero sirve para comparación rápida.
    """
    values = {'2':2, '3':3, '4':4, '5':5, '6':6, '7':7, '8':8,
              '9':9, '10':10, 'j':11, 'q':12, 'k':13, 'a':14}
    ranks = sorted([values[c[:-1]] for c in hand], reverse=True)
    suits = [c[-1] for c in hand]
    counts = Counter(ranks)
    freq = sorted(counts.values(), reverse=True)
    rank_vals = sorted(((v, k) for k, v in counts.items()), reverse=True)

    # Escalera y color
    is_flush = len(set(suits)) == 1
    is_straight = ranks == list(range(ranks[0], ranks[0]-5, -1))

    if is_flush and is_straight:
        return 800 + ranks[0]
    elif freq == [4,1]:
        return 700 + rank_vals[0][1]
    elif freq == [3,2]:
        return 600 + rank_vals[0][1]
    elif is_flush:
        return 500 + sum(ranks)
    elif is_straight:
        return 400 + ranks[0]
    elif freq == [3,1,1]:
        return 300 + rank_vals[0][1]
    elif freq == [2,2,1]:
        return 200 + max(rank_vals[0][1], rank_vals[1][1])
    elif freq == [2,1,1,1]:
        return 100 + rank_vals[0][1]
    else:
        return sum(ranks)

# Mostrar imágenes
def show_cards(cards):
    cols = st.columns(len(cards))
    for i, card in enumerate(cards):
        img = load_card_image(card)
        if img:
            cols[i].image(img, use_container_width=True)

# UI principal
st.title("Calculadora de Equities - Mata AA")

selected = []

st.header("Cartas del Jugador 1")
player1 = select_cards("J1", selected)
selected += player1

st.header("Cartas del Jugador 2")
player2 = select_cards("J2", selected)
selected += player2

st.header("Cartas de Ayuda")
help_cards = select_cards("Help", selected, num_cards=3)
selected += help_cards

if st.button("Calcular Equities"):
    if len(player1) == 4 and len(player2) == 4 and len(help_cards) == 3:
        used_cards = set(player1 + player2 + help_cards)
        remaining = [c for c in all_cards if c not in used_cards]

        n_simulations = 5000
        wins1 = wins2 = ties = 0

        for _ in range(n_simulations):
            extra = random.sample(remaining, 2)
            hand1 = player1 + [extra[0]]
            hand2 = player2 + [extra[1]]

            score1 = evaluate_hand(hand1, help_cards)
            score2 = evaluate_hand(hand2, help_cards)

            if score1 > score2:
                wins1 += 1
            elif score2 > score1:
                wins2 += 1
            else:
                ties += 1

        total = wins1 + wins2 + ties
        st.subheader("Resultados:")
        st.write(f"Jugador 1: **{wins1 / total * 100:.2f}%**")
        st.write(f"Jugador 2: **{wins2 / total * 100:.2f}%**")
        st.write(f"Empates: **{ties / total * 100:.2f}%**")
    else:
        st.error("Debes elegir 4 cartas para cada jugador y 3 ayudas.")
