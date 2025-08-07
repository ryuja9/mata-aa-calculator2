
import streamlit as st
import os
from PIL import Image

# Ruta a la carpeta de imágenes
IMAGE_FOLDER = "images"

# Obtener lista de nombres de archivo de cartas
CARD_IMAGES = sorted([
    img for img in os.listdir(IMAGE_FOLDER) if img.endswith(".png")
])

# Función para mostrar selección de cartas sin permitir duplicados
def card_selector(label, used_cards):
    options = [card for card in CARD_IMAGES if card not in used_cards]
    selected = st.selectbox(label, options)
    used_cards.add(selected)
    return selected

def main():
    st.title("Calculadora Mata AA - Versión Básica")

    used_cards = set()

    st.header("Jugador 1")
    p1_cards = [card_selector(f"Carta {i+1}", used_cards) for i in range(4)]

    st.header("Jugador 2")
    p2_cards = [card_selector(f"Carta {i+1}", used_cards) for i in range(4)]

    st.header("Cartas de ayuda")
    help_cards = [card_selector(f"Ayuda {i+1}", used_cards) for i in range(3)]

    if st.button("Calcular equities"):
        st.write("Cálculo de equities aún no implementado.")
        st.write("Jugador 1:", p1_cards)
        st.write("Jugador 2:", p2_cards)
        st.write("Ayudas:", help_cards)

    # Mostrar imágenes seleccionadas
    st.subheader("Cartas seleccionadas")
    all_selected = p1_cards + p2_cards + help_cards
    cols = st.columns(len(all_selected))
    for col, card in zip(cols, all_selected):
        img = Image.open(os.path.join(IMAGE_FOLDER, card))
        col.image(img, use_column_width=True)

if __name__ == "__main__":
    main()
