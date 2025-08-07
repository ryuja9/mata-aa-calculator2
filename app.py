import streamlit as st
from treys import Card, Evaluator, Deck
import itertools
import os

st.set_page_config(page_title="Mata AA Calculator", layout="centered")

# Cargar imágenes de cartas
def get_card_images():
    cards = []
    suits = ['c', 'd', 'h', 's']  # trébol, diamante, corazón, pica
    ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
    for r in ranks:
        for s in suits:
            filename = f"{r}{s}.png"
            path = os.path.join("images", filename)
            cards.append((f"{r}{s}", path))
    return cards

card_images = get_card_images()
evaluator = Evaluator()

# Mejor mano según reglas de Mata AA
def best_hand(player_cards, helps):
    cards = [Card.new(c) for c in player_cards]
    helps_cards = [Card.new(c) for c in helps]
    best_score = float('inf')

    # Opción sin ayuda
    if len(cards) == 5:
        best_score = evaluator.evaluate(cards, [])

    # Opción con ayuda (4 cartas del jugador + 1 ayuda)
    for help_card in helps_cards:
        for i in range(len(cards)):
            hand = cards[:i] + cards[i+1:] + [help_card]
            score = evaluator.evaluate(hand, [])
            if score < best_score:
                best_score = score

    return best_score

# Calcular equities
def calculate_equities(p1_cards, p2_cards, helps):
    deck = Deck.GetFullDeck()
    used = [Card.new(c) for c in p1_cards + p2_cards + helps]
    remaining = [c for c in deck if c not in used]

    total = win1 = win2 = tie = 0
    for c1, c2 in itertools.permutations(remaining, 2):
        hand1 = p1_cards + [Card.int_to_str(c1)]
        hand2 = p2_cards + [Card.int_to_str(c2)]
        score1 = best_hand(hand1, helps)
        score2 = best_hand(hand2, helps)

        if score1 < score2:
            win1 += 1
        elif score2 < score1:
            win2 += 1
        else:
            tie += 1
        total += 1

    eq1 = (win1 + tie/2) / total * 100
    eq2 = (win2 + tie/2) / total * 100
    return eq1, eq2

# Interfaz
st.title("Calculadora Mata AA")
st.subheader("Selecciona cartas para cada jugador y las ayudas")

cols = st.columns(3)
sections = ["Jugador 1", "Jugador 2", "Ayudas"]
selected_cards = {section: [] for section in sections}

# Selector visual
for idx, section in enumerate(sections):
    with cols[idx]:
        st.markdown(f"### {section}")
        for code, path in card_images:
            if st.button("", key=f"{section}-{code}"):
                if code not in sum(selected_cards.values(), []):
                    selected_cards[section].append(code)
            st.image(path, width=40)

if st.button("Calcular Equities"):
    if len(selected_cards["Jugador 1"]) == 4 and len(selected_cards["Jugador 2"]) == 4 and len(selected_cards["Ayudas"]) == 3:
        eq1, eq2 = calculate_equities(selected_cards["Jugador 1"], selected_cards["Jugador 2"], selected_cards["Ayudas"])
        st.success(f"Equity Jugador 1: {eq1:.2f}%")
        st.success(f"Equity Jugador 2: {eq2:.2f}%")
    else:
        st.error("Debes elegir 4 cartas para cada jugador y 3 ayudas.")
