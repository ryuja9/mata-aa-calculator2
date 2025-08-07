import streamlit as st
import random
import itertools
from collections import Counter
from PIL import Image

# Rutas de las imágenes
def get_card_image(card):
    return f"images/{card}.png"

# Formato visual de carta
def format_card(card):
    rank_map = {'a': 'A', 'k': 'K', 'q': 'Q', 'j': 'J', 't': '10'}
    rank = rank_map.get(card[0], card[0].upper())
    suit = card[1]
    return f"{rank}{suit}"

# Orden personalizado de cartas
def card_sort_key(card):
    order = {'a': 14, 'k': 13, 'q': 12, 'j': 11, 't': 10,
             '9': 9, '8': 8, '7': 7, '6': 6,
             '5': 5, '4': 4, '3': 3, '2': 2}
    return order[card[0]]

# Generar baraja
suits = ['c', 'd', 'h', 's']
ranks = ['a', 'k', 'q', 'j', 't', '9', '8', '7', '6', '5', '4', '3', '2']
deck = [r + s for r in ranks for s in suits]

# Título
st.title("Calculadora de Equities - Mata AA")

# Selección de cartas
st.header("Selecciona las cartas")

columns = st.columns(2)
players = {}
used_cards = []

for i in range(2):
    with columns[i]:
        st.subheader(f"Jugador {i + 1}")
        card1 = st.selectbox(f"Carta 1 (Jugador {i + 1})", sorted([c for c in deck if c not in used_cards], key=card_sort_key), key=f"p{i+1}c1")
        used_cards.append(card1)
        card2 = st.selectbox(f"Carta 2 (Jugador {i + 1})", sorted([c for c in deck if c not in used_cards], key=card_sort_key), key=f"p{i+1}c2")
        used_cards.append(card2)
        players[f"Jugador {i + 1}"] = [card1, card2]
        st.image([get_card_image(card1), get_card_image(card2)], width=80)

# Selección de ayudas
st.header("Cartas de ayuda")
help_cards = []
cols = st.columns(3)
for i in range(3):
    with cols[i]:
        help_card = st.selectbox(f"Ayuda {i + 1}", sorted([c for c in deck if c not in used_cards], key=card_sort_key), key=f"help{i+1}")
        used_cards.append(help_card)
        help_cards.append(help_card)
        st.image(get_card_image(help_card), width=80)

# Función para evaluar manos
hand_ranks = {
    "
