# app7.py - Calculadora Mata AA (versión final mejorada)
import streamlit as st
import os
import random
from collections import Counter
from itertools import permutations

# ---------------- Config ----------------
st.set_page_config(page_title="Calculadora Mata AA (Final)", layout="wide")
IMAGES_DIR = "images"  # carpeta con cartas en minúscula: 'as.png','10h.png','kc.png', etc.

RANKS = ['A','K','Q','J','10','9','8','7','6','5','4','3','2']
SUITS = ['s','h','d','c']
DECK = [r.lower() + s for r in RANKS for s in SUITS]

# ---------- Evaluador 5-cartas (sin librerías externas) ----------
RANK_VALUES = {'2':2,'3':3,'4':4,'5':5,'6':6,'7':7,'8':8,'9':9,'10':10,'J':11,'Q':12,'K':13,'A':14}

def evaluate_5cards(cards):
    ranks = [c[:-1].upper() for c in cards]
    suits = [c[-1] for c in cards]
    vals = [RANK_VALUES[r if r!='T' else '10'] for r in ranks]
    vals_sorted = sorted(vals, reverse=True)
    counts = Counter(vals)
    counts_items = sorted(counts.items(), key=lambda x: (-x[1], -x[0]))
    freq = sorted(counts.values(), reverse=True)
    is_flush = len(set(suits)) == 1
    unique_vals = sorted(set(vals), reverse=True)

    # straight detect (including wheel)
    is_straight = False
    top_straight = None
    if len(unique_vals) == 5:
        if max(unique_vals) - min(unique_vals) == 4:
            is_straight = True
            top_straight = max(unique_vals)
        elif set(unique_vals) == set([14,5,4,3,2]):
            is_straight = True
            top_straight = 5

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
    best = evaluate_5cards(final5)
    for h in helps:
        for i in range(5):
            candidate = final5[:i] + [h] + final5[i+1:]
            sc = evaluate_5cards(candidate)
            if compare_scores(sc,best) == 1:
                best = sc
    return best

def qualifies_pair_of_AA_or_better(score):
    cat = score[0]
    if cat > 2:
        return True
    if cat == 2:
        pair_rank = score[1][0]
        return pair_rank == 14
    return False

# ---------- UI: slots por jugador (selección por jugador, no dropdowns) ----------
st.title("Calculadora Mata AA — Final")
st.markdown("Interfaz mejorada — selecciona jugador, luego pulsa la carta en la pestaña del palo. Se bloquean duplicados automáticamente. Español.")

# Número de jugadores
num_players = st.sidebar.selectbox("Número de jugadores", options=[2,3,4], index=0)

# Inicializar slots en session_state
slot_keys = []
for p in range(1,num_players+1):
    for i in range(1,5):
        key = f"p{p}_{i}"
        slot_keys.append(key)
for i in range(1,4):
    slot_keys.append(f"h_{i}")

for k in slot_keys:
    if k not in st.session_state:
        st.session_state[k] = ""

# Selector de jugador/slot activo (cíclo por jugador o ayudas)
st.sidebar.markdown("**Asignar cartas a**")
target_player = st.sidebar.radio("Selecciona zona", options=[f"Jugador {i}" for i in range(1,num_players+1)] + ["Ayudas"])
# If player chosen, we'll auto-fill slots in order
assign_mode = st.sidebar.radio("Modo asignación", options=["Rellenar automáticamente", "Elegir posición específica"])

if assign_mode == "Elegir posición específica":
    slot_pos = st.sidebar.selectbox("Selecciona posición", options=[f"P{p}-{i}" for p in range(1,num_players+1) for i in range(1,5)] + [f"Help-{i}" for i in range(1,4)])
else:
    slot_pos = None

# utilidad: cartas ya usadas
def used_map():
    m = {}
    for k in slot_keys:
        v = st.session_state.get(k,"")
        if v:
            m[v] = k
    return m

# función para asignar carta a zona
def assign_card(card):
    used = used_map()
    # if already assigned somewhere else, remove from there
    if card in used:
        prev = used[card]
        st.session_state[prev] = ""
    # determine target slot
    if slot_pos:
        target_key = slot_pos.lower().replace('-','_')
    else:
        if target_player == "Ayudas":
            # find first empty help slot
            for i in range(1,4):
                key = f"h_{i}"
                if st.session_state[key] == "":
                    target_key = key
                    break
            else:
                target_key = None
        else:
            pnum = int(target_player.split()[1])
            # find first empty slot for that player
            for i in range(1,5):
                key = f"p{pnum}_{i}"
                if st.session_state[key] == "":
                    target_key = key
                    break
            else:
                # if none empty, overwrite last
                target_key = f"p{pnum}_4"
    if target_key:
        st.session_state[target_key] = card

# botones acción
col1,col2,col3 = st.columns([1,1,1])
with col1:
    if st.button("Borrar todo"):
        for k in slot_keys:
            st.session_state[k] = ""
with col2:
    if st.button("Autocompletar (aleatorio)"):
        pool = DECK.copy()
        random.shuffle(pool)
        idx = 0
        for k in slot_keys:
            st.session_state[k] = pool[idx]; idx += 1
with col3:
    if st.button("Limpiar asignaciones (mantener ayudas)"):
        for k in slot_keys:
            if k.startswith("p"):
                st.session_state[k] = ""

st.write("---")

# Mostrar selección actual
st.markdown("### Selección actual")
for p in range(1,num_players+1):
    cols = st.columns(4)
    for i in range(1,5):
        key = f"p{p}_{i}"
        with cols[i-1]:
            v = st.session_state[key]
            if v:
                img_path = os.path.join(IMAGES_DIR, f"{v}.png")
                if os.path.isfile(img_path):
                    st.image(img_path, width=90)
                else:
                    st.write(v)
            else:
                st.write("vacío")

st.markdown("**Ayudas**")
cols = st.columns(3)
for i in range(1,4):
    key = f"h_{i}"
    with cols[i-1]:
        v = st.session_state[key]
        if v:
            img_path = os.path.join(IMAGES_DIR, f"{v}.png")
            if os.path.isfile(img_path): st.image(img_path, width=80)
            else: st.write(v)
        else:
            st.write("vacío")

st.write("---")

# Tabs por palo, selección de cartas
tabs = st.tabs(["♠ Picas","♥ Corazones","♦ Diamantes","♣ Tréboles"])
suit_chars = ['s','h','d','c']
for suit_char, tab in zip(suit_chars, tabs):
    with tab:
        cols = st.columns(13)
        for i, rank in enumerate(RANKS):
            card = rank.lower() + suit_char
            with cols[i]:
                img_path = os.path.join(IMAGES_DIR, f"{card}.png")
                if os.path.isfile(img_path):
                    st.image(img_path, width=72)
                else:
                    st.write(card)
                # disable button if card used
                used = used_map()
                disabled = card in used
                if st.button("Seleccionar", key=f"btn_{card}", disabled=disabled):
                    assign_card(card)
                    st.experimental_rerun()

st.write("---")

# ---------- Cálculo ----------
def calculate_exact_or_monte(p_cards, helps, exact_threshold=300000):
    used = set([c for lst in p_cards for c in lst] + helps)
    remaining = [c for c in DECK if c not in used]
    k = len(p_cards)
    n = len(remaining)
    # count permutations P(n,k)
    perm_count = 1
    for i in range(k):
        perm_count *= (n - i)
    if perm_count <= exact_threshold:
        # exact
        wins = [0]*k; wins_mata=[0]*k; ties=0; kills=[0]*k; total=0
        for tup in permutations(remaining, k):
            total += 1
            fulls = [p_cards[i] + [tup[i]] for i in range(k)]
            scores = [best_score_with_optional_help(f, helps) for f in fulls]
            for i,sc in enumerate(scores):
                if qualifies_pair_of_AA_or_better(sc): kills[i]+=1
            # determine winner
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
        return {"mode":"exact","total":total,"wins":wins,"wins_mata":wins_mata,"ties":ties,"kills":kills}
    else:
        # Monte Carlo
        iters = st.sidebar.number_input("Iteraciones MC", value=40000, min_value=1000, max_value=200000, step=1000)
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

if st.button("Calcular equities (1 carta faltante por jugador)"):
    # collect player cards
    p_cards = []
    for p in range(1,num_players+1):
        lst = [st.session_state[f"p{p}_{i}"] for i in range(1,5)]
        if "" in lst:
            st.error(f"Jugador {p}: faltan 4 cartas")
            st.stop()
        p_cards.append(lst)
    helps = [st.session_state[f"h_{i}"] for i in range(1,4)]
    if "" in helps:
        st.error("Faltan 3 ayudas seleccionadas")
        st.stop()
    with st.spinner("Calculando..."):
        res = calculate_exact_or_monte(p_cards, helps)
    tot = res["total"]
    st.success(f"Modo: {res['mode']} — total combinaciones: {tot}")
    for i in range(len(p_cards)):
        st.write(f"Jugador {i+1} — Victorias: {res['wins'][i]} ({res['wins'][i]/tot*100:.3f}%), Victorias que matan AA: {res['wins_mata'][i]} ({res['wins_mata'][i]/tot*100:.3f}%), Prob tener ≥AA: {res['kills'][i]} ({res['kills'][i]/tot*100:.3f}%)")
    st.write(f"Empates/pozo retenido: {res['ties']} ({res['ties']/tot*100:.3f}%)")

    # outs table for player1 (top)
    st.write("---")
    st.write("Outs útiles (top cartas para Jugador 1 que más victorias dan):")
    used = set([c for lst in p_cards for c in lst] + helps)
    remaining = [c for c in DECK if c not in used]
    per_card = {}
    for c1 in remaining:
        w = 0
        for others in permutations(remaining, len(p_cards)-1):
            # build tuple where p1 gets c1 and others assigned in order to p2..pk
            tup = (c1,) + others
            fulls = [p_cards[0] + [tup[0]]] + [p_cards[i] + [tup[i]] for i in range(1,len(p_cards))]
            scores = [best_score_with_optional_help(f, helps) for f in fulls]
            # winner?
            best_idx = 0; tieflag=False
            for i in range(1,len(scores)):
                c = compare_scores(scores[i], scores[best_idx])
                if c == 1:
                    best_idx = i; tieflag=False
                elif c == 0:
                    tieflag = True
            if not tieflag and best_idx == 0:
                w += 1
        per_card[c1] = w
    top = sorted(per_card.items(), key=lambda x: -x[1])[:6]
    st.table([{"Carta":t[0], "Victorias_vs_todos": t[1]} for t in top])
