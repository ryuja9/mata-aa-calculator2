import streamlit as st
import os
from itertools import combinations
from PIL import Image
import random

st.set_page_config(layout="wide", page_title="Calculadora Mata AA")

# Función para cargar imagen
def load_card_image(card):
    path = os.path.join("images", f"{card}.png")
    return Image.open(path)

# Lista completa de cartas
suits = ['c', 'd', 'h', 's']
ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'j', 'q', 'k', 'a']
deck = [rank + suit for rank in ranks for suit in suits]

st.title("🃏 Calculadora de Equities – Mata AA")
st.markdown("Selecciona 4 cartas por jugador y 3 ayudas. La app calculará la equity faltando solo una carta por jugador.")

selected_cards = set()

def card_selector(label, count):
    selected = []
    cols = st.columns(count)
    for i in range(count):
        with cols[i]:
            card = st.selectbox(
                f"{label} {i+1}",
                options=[""] + sorted([c for c in deck if c not in selected_cards]),
                key=f"{label}_{i}"
            )
            if card:
                selected.append(card)
                selected_cards.add(card)
    return selected

col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    st.subheader("Jugador 1")
    player1 = card_selector("P1", 4)

with col2:
    st.subheader("Jugador 2")
    player2 = card_selector("P2", 4)

with col3:
    st.subheader("Cartas de ayuda")
    ayudas = card_selector("Ayuda", 3)

# Mostrar imágenes
def display_card_images(cards, title):
    st.markdown(f"**{title}**")
    img_cols = st.columns(len(cards))
    for i, card in enumerate(cards):
        with img_cols[i]:
            st.image(load_card_image(card), width=80)

if len(player1) == 4 and len(player2) == 4 and len(ayudas) == 3:
    st.success("Listo para calcular.")
    display_card_images(player1, "Jugador 1")
    display_card_images(player2, "Jugador 2")
    display_card_images(ayudas, "Ayudas")
else:
    st.warning("Selecciona exactamente 4 cartas por jugador y 3 ayudas.")

# Validación de duplicados
if len(selected_cards) < 11:
    st.error("❌ Hay cartas duplicadas. Corrige tu selección.")
    st.stop()

# Función de ranking simple para comparar manos
def hand_strength(cards, ayuda):
    # Aquí podrías mejorar el ranking, pero por simplicidad usaremos:
    # Orden de fuerza: pares, dobles, trío, full, etc.
    from collections import Counter

    all_cards = cards + ([ayuda] if ayuda else [])
    values = [c[:-1] for c in all_cards]
    counts = Counter(values).values()
    if 3 in counts and 2 in counts:
        return 6  # Full house
    elif 4 in counts:
        return 7  # Poker
    elif 3 in counts:
        return 3  # Trío
    elif list(counts).count(2) == 2:
        return 2  # Doble par
    elif 2 in counts:
        return 1  # Par
    else:
        return 0  # Carta alta

# Simulación Monte Carlo
def calcular_equity(p1, p2, ayudas, num_simulaciones=10000):
    mazo_restante = [c for c in deck if c not in p1 + p2 + ayudas]
    wins_p1 = 0
    wins_p2 = 0
    empates = 0

    for _ in range(num_simulaciones):
        random.shuffle(mazo_restante)
        carta_p1 = mazo_restante[0]
        carta_p2 = mazo_restante[1]

        mano1 = p1 + [carta_p1]
        mano2 = p2 + [carta_p2]

        mejor_ayuda1 = max([hand_strength(mano1, a) for a in ayudas] + [hand_strength(mano1, None)])
        mejor_ayuda2 = max([hand_strength(mano2, a) for a in ayudas] + [hand_strength(mano2, None)])

        if mejor_ayuda1 > mejor_ayuda2:
            wins_p1 += 1
        elif mejor_ayuda2 > mejor_ayuda1:
            wins_p2 += 1
        else:
            empates += 1

    total = wins_p1 + wins_p2 + empates
    equity_p1 = wins_p1 / total * 100
    equity_p2 = wins_p2 / total * 100
    equity_split = empates / total * 100

    return equity_p1, equity_p2, equity_split

# Botón para calcular
if st.button("📊 Calcular Equities"):
    with st.spinner("Calculando..."):
        eq1, eq2, split = calcular_equity(player1, player2, ayudas)
        st.subheader("🔢 Resultados")
        st.markdown(f"**Jugador 1:** {eq1:.2f}%")
        st.markdown(f"**Jugador 2:** {eq2:.2f}%")
        st.markdown(f"**Empate:** {split:.2f}%")
