
import streamlit as st
from st_clickable_images import clickable_images
from treys import Card, Evaluator

st.set_page_config(layout="wide")
st.title("Calculadora Mata AA")

# Cargar cartas
suits = ['c', 'd', 'h', 's']
ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'j', 'q', 'k', 'a']
all_cards = [f"{rank}{suit}" for rank in ranks for suit in suits]

def select_cards(label, card_list):
    st.subheader(label)
    images = [f"images/{c}.png" for c in card_list]
    clicked_idx = clickable_images(images, titles=card_list, div_style={"display":"flex","flex-wrap":"wrap"}, img_style={"margin":"5px","height":"80px"}, key=label)
    selected = st.session_state.get(label, [])
    if clicked_idx is not None and clicked_idx >= 0:
        card = card_list[clicked_idx]
        if card in selected:
            selected.remove(card)
        elif len(selected) < (4 if 'Jugador' in label else 3):
            selected.append(card)
        st.session_state[label] = selected
    st.write("Seleccionadas:", selected)

def card_str_to_int(card_str):
    return Card.new(card_str.upper())

def calculate_equities(j1_cards, j2_cards, ayudas):
    evalr = Evaluator()
    j1_hand = [card_str_to_int(c) for c in j1_cards]
    j2_hand = [card_str_to_int(c) for c in j2_cards]
    board = [card_str_to_int(c) for c in ayudas]
    j1_score = evalr.evaluate(board, j1_hand[:2])
    j2_score = evalr.evaluate(board, j2_hand[:2])
    if j1_score < j2_score:
        return 100.0, 0.0
    elif j2_score < j1_score:
        return 0.0, 100.0
    else:
        return 50.0, 50.0

col1, col2, col3 = st.columns(3)
with col1:
    select_cards("Jugador 1", all_cards)
with col2:
    select_cards("Jugador 2", all_cards)
with col3:
    select_cards("Ayudas", all_cards)

if st.button("Calcular Equities"):
    j1 = st.session_state.get("Jugador 1", [])
    j2 = st.session_state.get("Jugador 2", [])
    h = st.session_state.get("Ayudas", [])
    if len(j1)==4 and len(j2)==4 and len(h)==3:
        eq1, eq2 = calculate_equities(j1, j2, h)
        st.success(f"Equity J1: {eq1:.2f}% — J2: {eq2:.2f}%")
    else:
        st.error("Selecciona 4 cartas para J1, 4 para J2 y 3 ayudas.")
