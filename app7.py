import streamlit as st
from treys import Card, Evaluator
import os

# Ruta a la carpeta donde están las imágenes de cartas
CARD_IMAGES_DIR = "images"

# Todas las cartas disponibles
SUITS = ["c", "d", "h", "s"]
RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "t", "j", "q", "k", "a"]
ALL_CARDS = [rank + suit for rank in RANKS for suit in SUITS]

# Cargar imágenes
def load_card_image(card_name):
    path = os.path.join(CARD_IMAGES_DIR, f"{card_name}.png")
    return path

# Selector de cartas con imágenes
def select_card(label, excluded_cards):
    options = [card for card in ALL_CARDS if card not in excluded_cards]
    selected = st.selectbox(f"{label}", options, key=label)
    st.image(load_card_image(selected), width=60)
    return selected

st.title("Calculadora Mata AA (Versión Básica)")
st.markdown("Selecciona las **2 cartas iniciales** para cada jugador.")

# Jugador 1
st.subheader("Jugador 1")
selected_cards = []
p1_card1 = select_card("p1_card1", selected_cards)
selected_cards.append(p1_card1)
p1_card2 = select_card("p1_card2", selected_cards)
selected_cards.append(p1_card2)

# Jugador 2
st.subheader("Jugador 2")
p2_card1 = select_card("p2_card1", selected_cards)
selected_cards.append(p2_card1)
p2_card2 = select_card("p2_card2", selected_cards)
selected_cards.append(p2_card2)

# Calcular quién gana (con una carta comunitaria dummy)
if st.button("Evaluar mano"):
    evaluator = Evaluator()

    board = [Card.new("2h")]  # Carta comunitaria ficticia por ahora

    p1_hand = [Card.new(p1_card1), Card.new(p1_card2)]
    p2_hand = [Card.new(p2_card1), Card.new(p2_card2)]

    p1_score = evaluator.evaluate(board, p1_hand)
    p2_score = evaluator.evaluate(board, p2_hand)

    st.markdown("### Resultado:")
    if p1_score < p2_score:
        st.success("Gana Jugador 1")
    elif p2_score < p1_score:
        st.success("Gana Jugador 2")
    else:
        st.info("Empate")

