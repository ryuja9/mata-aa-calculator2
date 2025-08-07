import streamlit as st
from PIL import Image
import pandas as pd
import random
import os

# Ruta a la carpeta de imágenes
CARD_IMAGES_DIR = "images"

# Listas ordenadas correctamente
RANK_ORDER = ['a', 'k', 'q', 'j', 't', '9', '8', '7', '6', '5', '4', '3', '2']
SUIT_ORDER = ['s', 'h', 'd', 'c']

# Generar nombres de cartas
CARD_LIST = [rank + suit for rank in RANK_ORDER for suit in SUIT_ORDER]

# Mostrar imagen de carta
def show_card(card_code, width=80):
    try:
        img = Image.open(os.path.join(CARD_IMAGES_DIR, f"{card_code}.png"))
        st.image(img, width=width)
    except:
        st.write(card_code.upper())

# Selector visual de cartas
def select_card(label, excluded_cards):
    cols = st.columns(13)
    selected = None
    for i, rank in enumerate(RANK_ORDER):
        with cols[i]:
            for suit in SUIT_ORDER:
                card = rank + suit
                if card in excluded_cards:
                    st.image(os.path.join(CARD_IMAGES_DIR, f"{card}.png"), width=50)
                else:
                    if st.button("", key=f"{label}_{card}"):
                        selected = card
                    st.image(os.path.join(CARD_IMAGES_DIR, f"{card}.png"), width=50)
    return selected

# Evaluador muy simple (para mostrar estructura)
def evaluate_hand(player_hand, help_cards, remaining_card):
    all_combinations = []
    for help_card in help_cards + [None]:
        if help_card:
            full_hand = player_hand + [help_card] + [remaining_card]
        else:
            full_hand = player_hand + [remaining_card]
        full_hand_sorted = sorted(full_hand)
        all_combinations.append(full_hand_sorted)
    # Simulación: elegimos la mejor combinación por orden alfabético
    return min(all_combinations)

# Cálculo de equities simulando una carta restante para cada jugador
def calculate_equities(p1, p2, help_cards, board_cards):
    used = set(p1 + p2 + help_cards + board_cards)
    deck = [card for card in CARD_LIST if card not in used]

    p1_wins = 0
    p2_wins = 0
    ties = 0

    for c1 in deck:
        for c2 in deck:
            if c1 == c2:
                continue

            hand1 = evaluate_hand(p1, help_cards, c1)
            hand2 = evaluate_hand(p2, help_cards, c2)

            if hand1 < hand2:
                p1_wins += 1
            elif hand2 < hand1:
                p2_wins += 1
            else:
                ties += 1

    total = p1_wins + p2_wins + ties
    return {
        "Jugador 1": f"{100 * p1_wins / total:.2f}%",
        "Jugador 2": f"{100 * p2_wins / total:.2f}%",
        "Empate": f"{100 * ties / total:.2f}%"
    }

# Streamlit UI
st.title("Calculadora de Equities - Mata AA")

st.header("Selecciona las cartas")

selected_cards = []

st.subheader("Jugador 1")
p1 = []
while len(p1) < 2:
    card = select_card("p1", selected_cards)
    if card and card not in selected_cards:
        p1.append(card)
        selected_cards.append(card)

st.subheader("Jugador 2")
p2 = []
while len(p2) < 2:
    card = select_card("p2", selected_cards)
    if card and card not in selected_cards:
        p2.append(card)
        selected_cards.append(card)

st.subheader("Cartas de ayuda (elige hasta 3)")
help_cards = []
while len(help_cards) < 3:
    card = select_card("help", selected_cards)
    if card and card not in selected_cards:
        help_cards.append(card)
        selected_cards.append(card)

st.subheader("Cartas del board (3 ya descubiertas)")
board_cards = []
while len(board_cards) < 3:
    card = select_card("board", selected_cards)
    if card and card not in selected_cards:
        board_cards.append(card)
        selected_cards.append(card)

if st.button("Calcular Equities"):
    if len(p1) == 2 and len(p2) == 2 and len(help_cards) >= 0 and len(board_cards) == 3:
        with st.spinner("Calculando..."):
            results = calculate_equities(p1, p2, help_cards, board_cards)
        st.success("Resultados:")
        st.write(results)
    else:
        st.error("Faltan cartas por seleccionar.")
