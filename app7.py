import streamlit as st
import os
from PIL import Image
from treys import Card, Evaluator
import itertools
import random

st.set_page_config(page_title="Calculadora Mata AA Mejorada", layout="wide")

# Orden natural para mostrar y seleccionar cartas (visual en botones)
ranks_ordered = ['A', 'K', 'Q', 'J', '10', '9', '8', '7', '6', '5', '4', '3', '2']
suits = ['s', 'h', 'd', 'c']  # picas, corazones, diamantes, tréboles

# Mapeo para cargar imágenes (nombres en minúscula)
def card_filename(rank, suit):
    # rank en minúscula para el archivo
    return f"{rank.lower()}{suit}.png"

# Mostrar nombre carta en mayúscula para figuras y as
def card_display_name(rank, suit):
    return rank.upper() + suit

# Convertir carta visual a formato treys (ej: "As" -> "as", "10d"->"10d")
def to_treys(card):
    rank = card[:-1].lower()
    suit = card[-1]
    return rank + suit

# Cargar imagen carta
def load_card_image(rank, suit):
    filename = card_filename(rank, suit)
    path = os.path.join("images", filename)
    if os.path.isfile(path):
        return Image.open(path)
    else:
        return None

# Mostrar selector de cartas con botones ordenados (evitando duplicados)
def card_selector(label, count, excluded_cards):
    st.write(f"Selecciona {count} cartas para **{label}** (sin repetir)")

    selected = []
    # Dividir en filas (4 columnas por fila)
    for _ in range(count):
        cols = st.columns(len(suits))
        card_selected = None
        for idx, suit in enumerate(suits):
            with cols[idx]:
                for rank in ranks_ordered:
                    card = rank + suit
                    if card.lower() in excluded_cards or card.lower() in selected:
                        continue
                    if st.button(card_display_name(rank, suit), key=f"{label}_{len(selected)}_{card}"):
                        card_selected = card.lower()
                        break
                if card_selected:
                    break
        if card_selected:
            selected.append(card_selected)
        else:
            # Si no seleccionan, mostrar texto para mantener espacio
            st.write(" ")
    return selected

# Mostrar cartas seleccionadas con imágenes
def display_cards(cards, title):
    st.write(f"**{title}**")
    cols = st.columns(len(cards))
    for i, card in enumerate(cards):
        with cols[i]:
            rank = card[:-1].upper() if card[:-1] in ['a','k','q','j'] else card[:-1]
            suit = card[-1]
            img = load_card_image(card[:-1], suit)
            if img:
                st.image(img, width=60)
            else:
                st.write(card.upper())

# Evaluar mejor mano con ayuda (o sin ayuda)
def evaluar_mejor_mano(mano, ayudas, evaluator):
    mejor_score = 999999
    mejor_hand = None

    treys_hand = [Card.new(c) for c in mano]
    score = evaluator.evaluate(treys_hand, [])
    if score < mejor_score:
        mejor_score = score
        mejor_hand = treys_hand

    # Probar cada ayuda sustituyendo una carta
    for ayuda in ayudas:
        ayuda_card = Card.new(ayuda)
        for i in range(len(mano)):
            mano_con_ayuda = treys_hand[:i] + treys_hand[i+1:] + [ayuda_card]
            score = evaluator.evaluate(mano_con_ayuda, [])
            if score < mejor_score:
                mejor_score = score
                mejor_hand = mano_con_ayuda
    return mejor_score, mejor_hand

# Calcular equity con Monte Carlo para una carta faltante cada jugador
def calcular_equity(player1, player2, ayudas, num_sim=5000):
    evaluator = Evaluator()
    deck_full = set(Card.new(c) for c in (f"{r}{s}" for r in ranks_ordered for s in suits))
    
    usadas = set(Card.new(c) for c in player1 + player2 + ayudas)
    restantes = list(deck_full - usadas)
    
    wins1, wins2, ties = 0, 0, 0
    
    for _ in range(num_sim):
        random_cards = random.sample(restantes, 2)
        p1_hand = player1 + [random_cards[0]]
        p2_hand = player2 + [random_cards[1]]
        
        score1, _ = evaluar_mejor_mano(p1_hand, ayudas, evaluator)
        score2, _ = evaluar_mejor_mano(p2_hand, ayudas, evaluator)
        
        if score1 < score2:
            wins1 += 1
        elif score2 < score1:
            wins2 += 1
        else:
            ties += 1
    
    total = wins1 + wins2 + ties
    return wins1/total*100, wins2/total*100, ties/total*100

# --- INTERFAZ ---

st.title("Calculadora Mata AA Mejorada")

excluded = []

# Selección de cartas para jugadores y ayudas
player1 = card_selector("Jugador 1 (4 cartas visibles)", 4, excluded)
excluded += player1
player2 = card_selector("Jugador 2 (4 cartas visibles)", 4, excluded)
excluded += player2
ayudas = card_selector("Ayudas (3 cartas)", 3, excluded)
excluded += ayudas

# Convertir a formato treys
def to_treys_list(cards):
    return [to_treys(c) for c in cards]

if len(player1) == 4 and len(player2) == 4 and len(ayudas) == 3:
    st.subheader("Cartas seleccionadas")
    display_cards(player1, "Jugador 1")
    display_cards(player2, "Jugador 2")
    display_cards(ayudas, "Ayudas")
    
    if st.button("Calcular Equities"):
        with st.spinner("Calculando..."):
            p1_treys = [Card.new(c) for c in to_treys_list(player1)]
            p2_treys = [Card.new(c) for c in to_treys_list(player2)]
            ayudas_treys = [Card.new(c) for c in to_treys_list(ayudas)]
            
            eq1, eq2, ties = calcular_equity(p1_treys, p2_treys, ayudas_treys)
            
            st.success(f"Equity Jugador 1: {eq1:.2f}%")
            st.success(f"Equity Jugador 2: {eq2:.2f}%")
            st.info(f"Empates: {ties:.2f}%")
else:
    st.warning("Por favor selecciona las 4 cartas para cada jugador y las 3 ayudas sin repetir.")

