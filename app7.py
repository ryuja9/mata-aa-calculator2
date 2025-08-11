import streamlit as st
import eval7
import os
import random

# Configuración
st.set_page_config(page_title="Calculadora Mata AA", layout="wide")
CARD_IMAGES_DIR = "images"

# Orden de cartas al estilo póker
RANKS = ["a", "k", "q", "j", "10", "9", "8", "7", "6", "5", "4", "3", "2"]
SUITS = ["s", "h", "d", "c"]  # picas, corazones, diamantes, tréboles

# Generar lista de cartas
DECK = [rank + suit for rank in RANKS for suit in SUITS]

# Estado inicial
if "selected_cards" not in st.session_state:
    st.session_state.selected_cards = []
if "board" not in st.session_state:
    st.session_state.board = []

# Función para mostrar cartas como botones
def select_card(label):
    st.write(label)
    cols = st.columns(13)  # 13 columnas = 13 rangos
    for i, rank in enumerate(RANKS):
        for suit in SUITS:
            card = rank + suit
            img_path = os.path.join(CARD_IMAGES_DIR, f"{card}.png")
            if card not in st.session_state.selected_cards:
                if cols[i].button("", key=f"{label}_{card}"):
                    st.session_state.selected_cards.append(card)
                    return card
                cols[i].image(img_path, width=50)
    return None

# Función para calcular equity
def calculate_equity(p1_cards, p2_cards, board_cards, num_simulations=5000):
    deck = eval7.Deck()
    # Remover cartas usadas
    used = p1_cards + p2_cards + board_cards
    for card in used:
        deck.cards.remove(eval7.Card(card.upper()))

    p1_score = 0
    p2_score = 0
    ties = 0

    for _ in range(num_simulations):
        deck.shuffle()
        remaining = board_cards + [str(c).lower() for c in deck.peek(5 - len(board_cards))]

        p1_hand = [eval7.Card(c.upper()) for c in p1_cards + remaining]
        p2_hand = [eval7.Card(c.upper()) for c in p2_cards + remaining]

        p1_val = eval7.evaluate(p1_hand)
        p2_val = eval7.evaluate(p2_hand)

        if p1_val > p2_val:
            p1_score += 1
        elif p2_val > p1_val:
            p2_score += 1
        else:
            ties += 1

    total = p1_score + p2_score + ties
    return p1_score / total, p2_score / total, ties / total

# Interfaz principal
st.title("Calculadora Mata AA - Optimizada")
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("Jugador 1")
    p1_cards = []
    while len(p1_cards) < 2:
        card = select_card(f"Carta {len(p1_cards)+1}")
        if card:
            p1_cards.append(card)

with col2:
    st.subheader("Jugador 2")
    p2_cards = []
    while len(p2_cards) < 2:
        card = select_card(f"Carta {len(p2_cards)+1}")
        if card:
            p2_cards.append(card)

with col3:
    st.subheader("Cartas comunitarias")
    while len(st.session_state.board) < 5:
        card = select_card(f"Comunitaria {len(st.session_state.board)+1}")
        if card:
            st.session_state.board.append(card)

# Calcular y mostrar equity
if len(p1_cards) == 2 and len(p2_cards) == 2:
    p1_eq, p2_eq, tie_eq = calculate_equity(p1_cards, p2_cards, st.session_state.board)
    st.write(f"**Equity Jugador 1:** {p1_eq*100:.1f}%")
    st.write(f"**Equity Jugador 2:** {p2_eq*100:.1f}%")
    st.write(f"**Empate:** {tie_eq*100:.1f}%")
