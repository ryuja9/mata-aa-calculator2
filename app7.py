# app7.py
import streamlit as st
import os
from collections import Counter

st.set_page_config(page_title="Calculadora Mata AA (mejorada)", layout="wide")

# ----------------------
# Config
# ----------------------
IMAGES_DIR = "images"  # carpeta con e.g. "as.png", "10h.png", "kd.png" (minúsculas)
RANKS = ['A','K','Q','J','10','9','8','7','6','5','4','3','2']   # orden visual
SUITS = ['s','h','d','c']  # spades, hearts, diamonds, clubs
DECK = [r + s for r in RANKS for s in SUITS]  # formato 'Ah','10h','Kd', etc.

# ----------------------
# Utilidades de evaluación (5-cartas)
# ----------------------
RANK_VALUES = {'2':2,'3':3,'4':4,'5':5,'6':6,'7':7,'8':8,'9':9,'10':10,'J':11,'Q':12,'K':13,'A':14}

def evaluate_5cards(cards):
    """Evalúa una mano de 5 cartas. Retorna (category, tiebreak_tuple) — más alto = mejor."""
    ranks = [c[:-1].upper() for c in cards]
    suits = [c[-1] for c in cards]
    vals = [RANK_VALUES[r if r!='T' else '10'] for r in ranks]
    vals_sorted = sorted(vals, reverse=True)
    counts = Counter(vals)
    counts_items = sorted(counts.items(), key=lambda x: (-x[1], -x[0]))  # (value, freq)
    freq = sorted(counts.values(), reverse=True)
    is_flush = len(set(suits)) == 1
    unique_vals = sorted(set(vals), reverse=True)

    # straight detect (incluye rueda A-2-3-4-5)
    is_straight = False
    top_straight = None
    if len(unique_vals) == 5:
        if max(unique_vals) - min(unique_vals) == 4:
            is_straight = True
            top_straight = max(unique_vals)
        elif set(unique_vals) == set([14,5,4,3,2]):
            is_straight = True
            top_straight = 5

    # Categorías (num más alto = mejor)
    # 9 straight flush, 8 four, 7 full, 6 flush, 5 straight, 4 trips, 3 two pair, 2 pair, 1 high
    if is_flush and is_straight:
        return (9,(top_straight,))
    if freq == [4,1]:
        four = counts_items[0][0]; kick = counts_items[1][0]
        return (8,(four,kick))
    if freq == [3,2]:
        t3 = counts_items[0][0]; p = counts_items[1][0]
        return (7,(t3,p))
    if is_flush:
        return (6, tuple(vals_sorted))
    if is_straight:
        return (5,(top_straight,))
    if freq == [3,1,1]:
        t3 = counts_items[0][0]; kicks = sorted([k for k,v in counts.items() if v==1], reverse=True)
        return (4,(t3,)+tuple(kicks))
    if freq == [2,2,1]:
        pairs = sorted([v for v,c in counts.items() if c==2], reverse=True)
        kick = [v for v,c in counts.items() if c==1][0]
        return (3, tuple(pairs)+(kick,))
    if freq == [2,1,1,1]:
        pair = counts_items[0][0]; kicks = sorted([k for k,v in counts.items() if v==1], reverse=True)
        return (2,(pair,)+tuple(kicks))
    return (1, tuple(vals_sorted))

def compare_scores(s1,s2):
    """Compara dos tuplas de score. Retorna 1 si s1>s2, -1 si s1<s2, 0 si empate."""
    if s1[0] != s2[0]:
        return 1 if s1[0] > s2[0] else -1
    t1,t2 = s1[1], s2[1]
    L = max(len(t1), len(t2))
    t1p = tuple(list(t1)+[0]*(L-len(t1)))
    t2p = tuple(list(t2)+[0]*(L-len(t2)))
    if t1p > t2p: return 1
    if t1p < t2p: return -1
    return 0

def best_score_with_optional_help(final5, helps):
    """
    final5: lista de 5 cartas (propias incl. la carta extra).
    helps: lista de 3 ayudas (cada jugador puede elegir 0 o 1 ayuda; la ayuda sustituye 1 carta propia).
    Retorna la mejor puntuación posible (category,tiebreaker).
    """
    best = evaluate_5cards(final5)  # sin ayuda
    for h in helps:
        for i in range(5):
            candidate = final5[:i] + [h] + final5[i+1:]
            sc = evaluate_5cards(candidate)
            if compare_scores(sc,best) == 1:
                best = sc
    return best

def kills_AA(score):
    """Devuelve True si la mano es >= par de Ases (es decir: par de Ases o mejor)."""
    cat = score[0]
    if cat > 2:  # trips o mejor
        return True
    if cat == 2:
        pair_rank = score[1][0]
        return pair_rank == 14
    return False

# ----------------------
# UI: selección con session_state (no borra otras selecciones)
# ----------------------
st.title("Calculadora Mata AA — versión mejorada")
st.markdown("Selecciona **4 cartas** por jugador y **3 ayudas**. (La app evalúa exactamente todas las combinaciones posibles para la última carta de cada jugador).")

# Slot keys
p1_keys = [f"p1_{i}" for i in range(4)]
p2_keys = [f"p2_{i}" for i in range(4)]
h_keys  = [f"h_{i}"  for i in range(3)]
all_keys = p1_keys + p2_keys + h_keys

# Inicializar estado
for k in all_keys:
    if k not in st.session_state:
        st.session_state[k] = ""  # empty default

def options_for_slot(slot_key):
    # cartas ya elegidas en las demás casillas
    chosen_others = {st.session_state[k] for k in all_keys if k != slot_key and st.session_state[k]}
    # incluir carta actual del slot (si existe) para que no desaparezca de opciones
    current = st.session_state.get(slot_key, "")
    opts = [c for c in DECK if c not in chosen_others]
    if current and current not in opts:
        opts = [current] + opts
    return [""] + opts

# Render de selectboxes (en 3 columnas)
c1,c2,c3 = st.columns(3)
with c1:
    st.subheader("Jugador 1")
    for idx,k in enumerate(p1_keys):
        st.session_state[k] = st.selectbox(f"P1 carta {idx+1}", options_for_slot(k), index=(0 if st.session_state[k]=="" else options_for_slot(k).index(st.session_state[k])), key=k)
with c2:
    st.subheader("Jugador 2")
    for idx,k in enumerate(p2_keys):
        st.session_state[k] = st.selectbox(f"P2 carta {idx+1}", options_for_slot(k), index=(0 if st.session_state[k]=="" else options_for_slot(k).index(st.session_state[k])), key=k)
with c3:
    st.subheader("Ayudas")
    for idx,k in enumerate(h_keys):
        st.session_state[k] = st.selectbox(f"Ayuda {idx+1}", options_for_slot(k), index=(0 if st.session_state[k]=="" else options_for_slot(k).index(st.session_state[k])), key=k)

# Reunir listas seleccionadas
p1_cards = [st.session_state[k] for k in p1_keys if st.session_state[k]]
p2_cards = [st.session_state[k] for k in p2_keys if st.session_state[k]]
helps    = [st.session_state[k] for k in h_keys if st.session_state[k]]

# Mostrar lo seleccionado con imágenes
def show_row(title, cards):
    if not cards: return
    st.markdown(f"**{title}**")
    cols = st.columns(len(cards))
    for c, col in zip(cards, cols):
        with col:
            img_path = os.path.join(IMAGES_DIR, f"{c}.png")
            if os.path.isfile(img_path):
                col.image(img_path, width=80)
            else:
                col.write(c)

st.write("---")
show_row("Jugador 1", p1_cards)
show_row("Jugador 2", p2_cards)
show_row("Ayudas", helps)
st.write("---")

# ----------------------
# Cálculo: enumerar todas las combinaciones de 1 carta faltante por jugador
# ----------------------
def calculate_exact(p1_cards, p2_cards, helps):
    used = set(p1_cards + p2_cards + helps)
    remaining = [c for c in DECK if c not in used]
    wins1 = wins2 = ties = 0
    wins1_mata = wins2_mata = ties_mata = 0
    kills1 = kills2 = 0
    # total combos ordered (c1,c2) with c1 != c2
    total = 0
    for c1 in remaining:
        for c2 in remaining:
            if c1 == c2: continue
            total += 1
            full1 = p1_cards + [c1]
            full2 = p2_cards + [c2]
            s1 = best_score_with_optional_help(full1, helps)
            s2 = best_score_with_optional_help(full2, helps)
            # record kills
            if kills_AA(s1): kills1 += 1
            if kills_AA(s2): kills2 += 1
            cmp = compare_scores(s1,s2)
            if cmp == 1:
                wins1 += 1
                if kills_AA(s1):
                    wins1_mata += 1
                else:
                    ties_mata += 1
            elif cmp == -1:
                wins2 += 1
                if kills_AA(s2):
                    wins2_mata += 1
                else:
                    ties_mata += 1
            else:
                ties += 1
                ties_mata += 1
    return {
        "total": total,
        "wins1": wins1, "wins2": wins2, "ties": ties,
        "wins1_mata": wins1_mata, "wins2_mata": wins2_mata, "ties_mata": ties_mata,
        "kills1": kills1, "kills2": kills2
    }

# Botón calcular
if st.button("Calcular (exacto)"):
    if len(p1_cards) != 4 or len(p2_cards) != 4 or len(helps) != 3:
        st.error("Selecciona exactamente 4 cartas para cada jugador y 3 ayudas.")
    else:
        with st.spinner("Calculando todas las combinaciones..."):
            res = calculate_exact(p1_cards, p2_cards, helps)
        tot = res["total"]
        st.success("Resultados exactos:")
        st.write(f"Total combinaciones (c1≠c2): {tot}")
        st.write(f"Equity (normal) — Jugador 1: **{res['wins1']/tot*100:.3f}%**, Jugador 2: **{res['wins2']/tot*100:.3f}%**, Empate: **{res['ties']/tot*100:.3f}%**")
        st.write(f"Equity (mata AA) — Jugador 1: **{res['wins1_mata']/tot*100:.3f}%**, Jugador 2: **{res['wins2_mata']/tot*100:.3f}%**, Empate/pozo retenido: **{res['ties_mata']/tot*100:.3f}%**")
        st.write(f"Probabilidad de tener ≥ par de Ases (independiente): Jugador1 **{res['kills1']/tot*100:.3f}%**, Jugador2 **{res['kills2']/tot*100:.3f}%**")

        # Opcional: Top outs para J1 (cartas que más le ayudan)
        # Calculamos rápidamente cuántos c2 pierde por cada c1 seleccionado
        used = set(p1_cards + p2_cards + helps)
        remaining = [c for c in DECK if c not in used]
        per_card = {}
        for c1 in remaining:
            w = 0
            for c2 in remaining:
                if c1 == c2: continue
                s1 = best_score_with_optional_help(p1_cards + [c1], helps)
                s2 = best_score_with_optional_help(p2_cards + [c2], helps)
                if compare_scores(s1,s2) == 1:
                    w += 1
            per_card[c1] = w
        top = sorted(per_card.items(), key=lambda x: -x[1])[:6]
        st.write("Top outs (cartas para J1 que más ganas dan frente a todas las posibles cartas del rival):")
        st.table([{ "carta":t[0], "victorias_vs_todas": t[1]} for t in top])
