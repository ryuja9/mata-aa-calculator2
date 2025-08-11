# app7.py
import streamlit as st
import os
import random
from collections import Counter
from itertools import permutations

st.set_page_config(page_title="Calculadora Mata AA — UI mejorada", layout="wide")

# ---------- CONFIG ----------
IMAGES_DIR = "images"   # carpeta con 'as.png','10h.png','kd.png', etc (minúsculas)
RANKS = ['A','K','Q','J','10','9','8','7','6','5','4','3','2']
SUITS = ['s','h','d','c']
DECK = [r.lower() + s for r in RANKS for s in SUITS]

# ---------- EVALUADOR (5-cartas) ----------
RANK_VALUES = {'2':2,'3':3,'4':4,'5':5,'6':6,'7':7,'8':8,'9':9,'10':10,'J':11,'Q':12,'K':13,'A':14}

def evaluate_5cards(cards):
    """Evalúa lista de 5 cartas (formato 'ah','10h',...) -> (category, tiebreak_tuple) mayor = mejor."""
    ranks = [c[:-1].upper() for c in cards]
    suits = [c[-1] for c in cards]
    vals = [RANK_VALUES[r if r!='T' else '10'] for r in ranks]
    vals_sorted = sorted(vals, reverse=True)
    counts = Counter(vals)
    counts_items = sorted(counts.items(), key=lambda x: (-x[1], -x[0]))
    freq = sorted(counts.values(), reverse=True)
    is_flush = len(set(suits)) == 1
    unique_vals = sorted(set(vals), reverse=True)

    # straight detect (incl. wheel)
    is_straight = False
    top_straight = None
    if len(unique_vals) == 5:
        if max(unique_vals) - min(unique_vals) == 4:
            is_straight = True
            top_straight = max(unique_vals)
        elif set(unique_vals) == set([14,5,4,3,2]):
            is_straight = True
            top_straight = 5

    # categories: 9 straight flush, 8 four, 7 full, 6 flush, 5 straight, 4 trips, 3 two pair, 2 pair, 1 high
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
    """1 si s1>s2, -1 si s1<s2, 0 empate."""
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
    """Prueba la mano sin ayuda y todas las sustituciones por una sola ayuda; devuelve la mejor."""
    best = evaluate_5cards(final5)
    for h in helps:
        for i in range(5):
            candidate = final5[:i] + [h] + final5[i+1:]
            sc = evaluate_5cards(candidate)
            if compare_scores(sc,best) == 1:
                best = sc
    return best

def qualifies_pair_of_AA_or_better(score):
    """Devuelve True si la mano es >= 'pair of Aces' (pair of Aces O mejor).
       Es decir: if category > pair OR (category==pair and pair_rank == Ace)"""
    cat = score[0]
    if cat > 2:
        return True
    if cat == 2:
        pair_rank = score[1][0]
        return pair_rank == 14
    return False

# ---------- UI: selección por slots y pestañas por palo ----------
st.title("Calculadora Mata AA — UI mejorada")
st.markdown("Selecciona la casilla destino (ej. P1-1), luego el palo y la carta. La carta se moverá si ya estaba en otra casilla. Usa hasta 4 jugadores.")

# jugadores
num_players = st.sidebar.selectbox("Número de jugadores", [2,3,4], index=0)

# generar keys
p_keys = []
for p in range(1, num_players+1):
    p_keys += [f"p{p}_{i}" for i in range(1,5)]
h_keys = [f"h_{i}'" for i in range(1,4)]
# initialize session_state
all_keys = p_keys + h_keys
for k in all_keys:
    if k not in st.session_state:
        st.session_state[k] = ""

# Build slot labels mapping to keys
slot_labels = []
for p in range(1,num_players+1):
    for i in range(1,5):
        slot_labels.append((f"P{p}-{i}", f"p{p}_{i}"))
for i in range(1,4):
    slot_labels.append((f"Help-{i}", f"h_{i}'"))

display_labels = [f"{lab} ({st.session_state[key] or 'vacío'})" for lab,key in slot_labels]
slot_choice = st.selectbox("Asignar a:", display_labels)
active_key = slot_labels[display_labels.index(slot_choice)][1]

# helpers for mapping cards -> slots
def used_card_to_slot_map():
    m = {}
    for k in all_keys:
        v = st.session_state.get(k,"")
        if v:
            m[v] = k
    return m

def assign_card_to_slot(card, target_key):
    mapping = used_card_to_slot_map()
    # if target already has card -> unassign
    if st.session_state.get(target_key,"") == card:
        st.session_state[target_key] = ""
        return
    if card in mapping:
        prev = mapping[card]
        st.session_state[prev] = ""
    st.session_state[target_key] = card

def clear_slot(key):
    st.session_state[key] = ""

def clear_all_slots():
    for k in all_keys:
        st.session_state[k] = ""

col1,col2,col3 = st.columns([1,1,1])
with col1:
    if st.button("Borrar casilla seleccionada"):
        clear_slot(active_key)
with col2:
    if st.button("Borrar todo"):
        clear_all_slots()
with col3:
    if st.button("Autocompletar aleatorio"):
        pool = [c for c in DECK]
        random.shuffle(pool)
        idx=0
        for k in all_keys:
            st.session_state[k] = pool[idx]; idx+=1

st.write("---")

# show selection
def show_selected_grid():
    st.markdown("**Selección actual**")
    for p in range(1,num_players+1):
        cards = [st.session_state[f"p{p}_{i}"] for i in range(1,5)]
        cols = st.columns(4)
        for c,col in zip(cards, cols):
            with col:
                if c:
                    img = os.path.join(IMAGES_DIR, f"{c}.png")
                    if os.path.isfile(img): col.image(img, width=76)
                    else: col.write(c)
                else:
                    col.write("vacío")
    st.markdown("**Ayudas**")
    cols = st.columns(3)
    for i,col in zip(range(1,4), cols):
        v = st.session_state.get(f"h_{i}'","")
        with col:
            if v:
                img = os.path.join(IMAGES_DIR, f"{v}.png")
                if os.path.isfile(img): col.image(img, width=70)
                else: col.write(v)
            else:
                col.write("vacío")

show_selected_grid()
st.write("---")

# tabs por palo (fixed: zip suit chars con tab objetos)
tabs = st.tabs(["♠ Picas","♥ Corazones","♦ Diamantes","♣ Tréboles"])
suit_chars = ['s','h','d','c']
for suit_char, tab in zip(suit_chars, tabs):
    with tab:
        st.write(f"Palo: {suit_char}")
        cols = st.columns(13)
        for i, rank in enumerate(RANKS):
            card = rank.lower() + suit_char
            col = cols[i]
            with col:
                img_path = os.path.join(IMAGES_DIR, f"{card}.png")
                if os.path.isfile(img_path):
                    col.image(img_path, width=70)
                else:
                    col.write(card)
                if col.button("Seleccionar", key=f"btn_{card}"):
                    assign_card_to_slot(card, active_key)

st.write("---")
st.markdown("Selecciona la casilla destino arriba y luego pulsa 'Seleccionar' en la carta deseada.")

# ---------- CÁLCULO ----------
def calculate_stats(p_cards, helps, exact_threshold=300000):
    """Si el número de combinaciones es <= exact_threshold hace exacto, si no usa MonteCarlo."""
    used = set([c for lst in p_cards for c in lst] + helps)
    remaining = [c for c in DECK if c not in used]
    k = len(p_cards)
    # permutations count P(n,k)
    n = len(remaining)
    # compute permutations count
    perm_count = 1
    for i in range(k):
        perm_count *= (n - i)
    # if small -> exact
    if perm_count <= exact_threshold:
        wins = [0]*k; wins_mata=[0]*k; ties=0; kills=[0]*k; total=0
        for tup in permutations(remaining, k):
            total += 1
            fulls = [p_cards[i] + [tup[i]] for i in range(k)]
            scores = [best_score_with_optional_help(f, helps) for f in fulls]
            # count kills
            for i,sc in enumerate(scores):
                if qualifies_pair_of_AA_or_better(sc): kills[i]+=1
            # determine winner / tie
            best_idx = 0; tieflag=False
            for i in range(1,k):
                c = compare_scores(scores[i], scores[best_idx])
                if c == 1:
                    best_idx = i; tieflag=False
                elif c == 0:
                    tieflag = True
            if tieflag:
                ties += 1
            else:
                wins[best_idx] += 1
                if qualifies_pair_of_AA_or_better(scores[best_idx]):
                    wins_mata[best_idx] += 1
                else:
                    # winner didn't qualify -> pot retained (count as tie for mata)
                    ties += 1
        return {"mode":"exact","total":total,"wins":wins,"wins_mata":wins_mata,"ties":ties,"kills":kills}
    else:
        # Monte Carlo fallback
        iters = 50000  # ajuste razonable; puedes cambiar
        wins = [0]*k; wins_mata=[0]*k; ties=0; kills=[0]*k; total=0
        for _ in range(iters):
            tup = random.sample(remaining, k)
            total += 1
            fulls = [p_cards[i] + [tup[i]] for i in range(k)]
            scores = [best_score_with_optional_help(f, helps) for f in fulls]
            for i,sc in enumerate(scores):
                if qualifies_pair_of_AA_or_better(sc): kills[i]+=1
            best_idx = 0; tieflag=False
            for i in range(1,k):
                c = compare_scores(scores[i], scores[best_idx])
                if c == 1:
                    best_idx = i; tieflag=False
                elif c == 0:
                    tieflag = True
            if tieflag:
                ties += 1
            else:
                wins[best_idx] += 1
                if qualifies_pair_of_AA_or_better(scores[best_idx]):
                    wins_mata[best_idx] += 1
                else:
                    ties += 1
        return {"mode":"montecarlo","total":total,"iters":iters,"wins":wins,"wins_mata":wins_mata,"ties":ties,"kills":kills}

# botón calcular
if st.button("Calcular (1 carta faltante por jugador)"):
    # recoger cartas
    p_cards = []
    for p in range(1,num_players+1):
        lst = [st.session_state[f"p{p}_{i}"] for i in range(1,5) if st.session_state[f"p{p}_{i}"]]
        if len(lst) != 4:
            st.error(f"Jugador {p}: faltan cartas (4 requeridas).")
            st.stop()
        p_cards.append(lst)
    helps = [st.session_state[f"h_{i}'"] for i in range(1,4) if st.session_state[f"h_{i}'"]]
    if len(helps) != 3:
        st.error("Faltan ayudas (3 requiridas).")
        st.stop()
    with st.spinner("Calculando combinaciones..."):
        res = calculate_stats(p_cards, helps)
    tot = res["total"]
    st.success(f"Modo: {res['mode']} — total combinaciones: {tot}")
    for i in range(len(p_cards)):
        st.write(f"Jugador {i+1}: wins = {res['wins'][i]} ({res['wins'][i]/tot*100:.3f}%), wins_mata = {res['wins_mata'][i]} ({res['wins_mata'][i]/tot*100:.3f}%), kills = {res['kills'][i]} ({res['kills'][i]/tot*100:.3f}%)")
    st.write(f"Empates (o pozo retenido en mataAA): {res['ties']} ({res['ties']/tot*100:.3f}%)")
    if res["mode"] == "montecarlo":
        st.info(f"Monte Carlo usado: iteraciones = {res['iters']}. Resultado aproximado.")
