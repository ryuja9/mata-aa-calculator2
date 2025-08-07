import streamlit as st
import os
from PIL import Image
from treys import Card, Evaluator

# Configurar la página
st.set_page_config(page_title="Mata AA Equity Calculator", layout="wide")
st.title("Calculadora de Equities - Mata AA")

# Cargar cartas disponibles
def load_card_images():
    card_images = {}
    suits = {'c': 'clubs', 'd': 'diamonds', 'h': 'hearts', 's': 'spades'}
    ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'j', 'q', 'k', 'a']
    for suit in suits:
        for rank in ranks:
            filename = f"{rank}{suit}.png"
            filepath = os.path.join("images", filename)
            if os.path.exists(filepath):
                card_images[f"{rank}{suit}"] = filepath
    return card_images

card_images = load_card_images()
card_keys = list(card_images.keys())

# Función para mostrar selección de cartas
def select_cards(label, num_cards):
    selected = st.multiselect(label, options=card_keys, default=[], max_selections=num_cards)
    cols = st.columns(len(selected))
    for i, card in enumerate(selected):
        with cols[i]:
            st.image(card_images[card], width=80)
    return selected

# Selección de cartas por jugador y ayudas
p1_cards = select_cards("Cartas del Jugador 1 (elige 4)", 4)
p2_cards = select_cards("Cartas del Jugador 2 (elige 4)", 4)
help_cards = select_cards("Cartas de ayuda (elige 3)", 3)

# Botón para calcular equity
if st.button("Calcular Equity"):
    if len(p1_cards) != 4 or len(p2_cards) != 4 or len(help_cards) != 3:
        st.error("Debes elegir 4 cartas para cada jugador y 3 ayudas.")
    else:
        # Aquí iría la lógica de cálculo
        st.success("Cartas seleccionadas correctamente. Pronto añadiremos el cálculo de equity.")