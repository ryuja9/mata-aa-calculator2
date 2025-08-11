# app7.py
import streamlit as st
import os
from collections import Counter

st.set_page_config(page_title="Calculadora Mata AA — UI mejorada", layout="wide")

# ---------- CONFIG ----------
IMAGES_DIR = "images"   # carpeta con e.g. "as.png", "10h.png", "kd.png", todo en minúsculas
RANKS = ['A','K','Q','J','10','9','8','7','6','5','4','3','2']   # orden visual
SUITS = ['s','h','d','c']  # spades, hearts, diamonds, clubs
DECK = [r.lower() + s for r in RANKS for s in SUITS]  # 'ah','kh','qh',...

# ---------- EVALUADOR (5-cartas) ----------
RANK_VALUES = {'2':2,'3':3,'4':4,'5':5,'6':6,'7':7,'8':8,'9':9,'10':10,'J':11,'Q':12,'K':13,'A':14}

def evaluate_5cards(cards):
    """Evaluador de manos de 5 cartas -> (category, tiebreak tuple). Más alto = mejor."""
    ranks = [c[:-1].upper() for c in cards]
    suits = [c[-1] for c in cards]
    vals = [RANK_VALUES[r if r!='T' else '10'] for r in ranks]
    vals_sorted = sorted(vals, reverse=True)
    counts = Counter(vals)
    counts_items = sorted(counts.items(), key=lambda x: (-x[1], -x[0]))
    freq = sorted(counts.values(), reverse=True)
    is_flush = len(set(suits)) == 1
    unique_vals = sorted(set(vals), reverse=True)

    # straight detect incl. wheel A-2-3-4-5
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
    """Compara dos scores (s1,s2). Retorna 1 si s1> s2, -1 si s1<s2, 0 si empate."""
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
    final5: lista de 5 cartas propias (ej. ['ah','jh','jc','10h','?'])
    helps: lista de 3 ayudas (ej. ['6c','qh','2d'])
    Cada jugador puede usar 0 o 1 ayuda (reemplazando una de sus 5 cartas).
    Devuelve la mejor puntuación posible (más alta = mejor).
    """
    best = evaluate_5cards(final5)
    for h in helps:
        for i in range(5):
            candidate = final5[:i] + [h] + final5[i+1:]
            sc = evaluate_5cards(candidate)
            if compare_scores(sc,best) == 1:
                best = sc
    return best

def kills_AA(score):
    """
    Devuelve True si la mano 'score' supera un par de Ases.
    Entendido como: si la mano es > pair (category 2) OR
    es category == 2 (pair) con par de As (pair_rank == 14).
    Es decir, 'calificar' significa tener mano estrictamente mejor que 1-pair-other-than-As? 
    (Interpretación: qualifies if pair of Aces or any stronger hand).
    """
    cat = score[0]
    if cat > 2:
        return True
    if cat == 2:
        pair_rank = score[1][0]
        return pair_rank == 14
    return False

# ---------- UI / SLOTS ----------
st.title("Calculadora Mata AA — Interfaz mejorada")
st.markdown("Selecciona la casilla destino (por ejemplo P1-1) y luego elige una carta en la pestaña del palo. \
La carta se moverá automáticamente si ya estaba en otra casilla. Puedes limpiar slots o todo.")

# Cantidad de jugadores (2 a 4)
num_players = st.sidebar.selectbox("Número de jugadores", [2,3,4], index=0)
# Generar keys dinamicamente según num_players
p_keys = []
for p in range(1, num_players+1):
    p_keys += [f"p{p}_{i}" for i in range(1,5)]  # 4 cartas por jugador
h_keys = [f"h_{i}" for i in range(1,4)]  # 3 ayudas
all_keys = p_keys + h_keys

# inicializar session_state slots si no existen
for k in all_keys:
    if k not in st.session_state:
        st.session_state[k] = ""  # empty

# selector de slot activo
slot_labels = []
for p in range(1, num_players+1):
    for i in range(1,5):
        slot_labels.append((f"P{p}-{i}", f"p{p}_{i}"))
for i in range(1,4):
    slot_labels.append((f"Help-{i}", f"h_{i}"))

display_labels = [f"{lab} ({st.session_state[key] or 'vacío'})" for lab,key in slot_labels]
slot_choice = st.selectbox("Asignar a:", display_labels)
# obtener key del slot seleccionado
active_key = slot_labels[display_labels.index(slot_choice)][1]

# util: obtener las cartas usadas y el slot donde está cada carta
def used_card_to_slot_map():
    m = {}
    for k in all_keys:
        v = st.session_state.get(k,"")
        if v:
            m[v] = k
    return m

# funciones asignar/limpiar
def assign_card_to_slot(card, target_key):
    mapping = used_card_to_slot_map()
    # si la carta ya está en el target, deseleccionamos
    if st.session_state.get(target_key,"") == card:
        st.session_state[target_key] = ""
        return
    # si está en otro slot, moverla (limpiando la antigua)
    if card in mapping:
        prev = mapping[card]
        st.session_state[prev] = ""
    # asignar
    st.session_state[target_key] = card

def clear_slot(key):
    st.session_state[key] = ""

def clear_all_slots():
    for k in all_keys:
        st.session_state[k] = ""

# botones de acción
col_action_1, col_action_2, col_action_3 = st.columns([1,1,1])
with col_action_1:
    if st.button("Borrar casilla seleccionada"):
        clear_slot(active_key)
with col_action_2:
    if st.button("Borrar todo"):
        clear_all_slots()
with col_action_3:
    if st.button("Autocompletar aleatorio (rápido)"):
        # solo para pruebas: llenar slots con cartas aleatorias no repetidas
        import random
        pool = [c for c in DECK]
        random.shuffle(pool)
        idx = 0
        for k in all_keys:
            st.session_state[k] = pool[idx]
            idx += 1

st.write("---")

# mostrar selección actual (visual)
def show_selected_grid():
    st.markdown("**Selección actual:**")
    rows = []
    for p in range(1, num_players+1):
        cards = [st.session_state[f"p{p}_{i}"] for i in range(1,5)]
        cols = st.columns(4)
        for c, col in zip(cards, cols):
            with col:
                if c:
                    img = os.path.join(IMAGES_DIR, f"{c}.png")
                    if os.path.isfile(img):
                        col.image(img, width=80)
                    else:
                        col.write(c)
                else:
                    col.write("vacío")
    # ayudas
    st.markdown("**Ayudas:**")
    cols = st.columns(3)
    for i,col in zip(range(1,4), cols):
        k = f"h_{i}"
        v = st.session_state[k]
        with col:
            if v:
                img = os.path.join(IMAGES_DIR, f"{v}.png")
                if os.path.isfile(img):
                    col.image(img, width=70)
                else:
                    col.write(v)
            else:
                col.write("vacío")

show_selected_grid()
st.write("---")

# ---------- GRID POR PALOS (pestañas) ----------
tabs = st.tabs(["♠ Picas","♥ Corazones","♦ Diamantes","♣ Tréboles"])
suit_map = {'♠ Picas':'s','♥ Corazones':'h','♦ Diamantes':'d','♣ Tréboles':'c'}
for tab in tabs:
    suit_char = suit_map[tab.title()]
    with tab:
        st.write(f"Palo: {suit_char}")
        # 13 columnas (una por rango)
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
                # boton seleccion
                if col.button("Seleccionar", key=f"btn_{card}"):
                    assign_card_to_slot(card, active_key)

st.write("---")
st.markdown("**Nota:** selecciona el slot destino (ej. P1-1) arriba y luego presiona 'Seleccionar' en la carta deseada.")

# ---------- CÁLCULO EXACTO (1 carta faltante por jugador) ----------
def calculate_exact(p_cards, helps):
    used = set(p_cards_all := [c for lst in p_cards for c in lst] + helps)
    remaining = [c for c in DECK if c not in used]
    wins = [0]*len(p_cards)
    ties = 0
    wins_mata = [0]*len(p_cards)
    kills = [0]*len(p_cards)
    total = 0
    # casos ordenados: cada jugador recibe una carta distinta
    # si queremos que sea simétrico (player i gets card xi), hacemos nested loops
    # límite: remaining size n -> n*(n-1)*... for #players; here default 2-4 players; we assume 1 card per player
    # Para k jugadores, we need product over picks without replacement.
    import itertools
    k = len(p_cards)
    # For 2 players we do double loop for speed; for k>2 use permutations
    if k == 2:
        for c1 in remaining:
            for c2 in remaining:
                if c1 == c2: continue
                total += 1
                fulls = []
                fulls.append(p_cards[0] + [c1])
                fulls.append(p_cards[1] + [c2])
                scores = [best_score_with_optional_help(f, helps) for f in fulls]
                for i, sc in enumerate(scores):
                    if kills_AA(sc):
                        kills[i] += 1
                # compare all pairwise: find best
                # we will just find max
                best_i = 0
                tieflag = False
                for i in range(1,len(scores)):
                    cmp = compare_scores(scores[i], scores[best_i])
                    if cmp == 1:
                        best_i = i
                        tieflag = False
                    elif cmp == 0:
                        tieflag = True
                if tieflag:
                    ties += 1
                else:
                    wins[best_i] += 1
                    # mata check:
                    if kills[best_i] and kills[best_i] > 0:
                        # above we already counted kills per player; but we need to check for this particular combo
                        # recompute: if winner's score kills AA -> count as mata win else count as tie_mata (pozo retenido)
                        winner_score = scores[best_i]
                        if kills_AA(winner_score):
                            wins_mata[best_i] += 1
                        else:
                            ties += 1
    else:
        # general permutations for k players
        from itertools import permutations
        for cards_tuple in permutations(remaining, k):
            total += 1
            fulls = [p_cards[i] + [cards_tuple[i]] for i in range(k)]
            scores = [best_score_with_optional_help(f, helps) for f in fulls]
            for i, sc in enumerate(scores):
                if kills_AA(sc):
                    kills[i] += 1
            # determine winner
            best_i = 0
            tieflag = False
            for i in range(1,len(scores)):
                cmp = compare_scores(scores[i], scores[best_i])
                if cmp == 1:
                    best_i = i
                    tieflag = False
                elif cmp == 0:
                    tieflag = True
            if tieflag:
                ties += 1
            else:
                wins[best_i] += 1
                winner_score = scores[best_i]
                if kills_AA(winner_score):
                    wins_mata[best_i] += 1
                else:
                    ties += 1
    return {
        "total": total,
        "wins": wins,
        "ties": ties,
        "wins_mata": wins_mata,
        "kills": kills
    }

# boton calcular
if st.button("Calcular exacto (1 carta faltante por jugador)"):
    # reunir datos
    p_cards = []
    for p in range(1, num_players+1):
        lst = [st.session_state[f"p{p}_{i}"] for i in range(1,5) if st.session_state[f"p{p}_{i}"]]
        if len(lst) != 4:
            st.error(f"Jugador {p}: faltan cartas (4 requeridas).")
            st.stop()
        p_cards.append(lst)
    helps = [st.session_state[f"h_{i}"] for i in range(1,4) if st.session_state[f"h_{i}"]]
    if len(helps) != 3:
        st.error("Faltan ayudas (3 requeridas).")
        st.stop()
    with st.spinner("Calculando todas las combinaciones posibles..."):
        res = calculate_exact(p_cards, helps)
    tot = res["total"]
    st.success("Resultados exactos:")
    for i in range(len(p_cards)):
        st.write(f"Jugador {i+1}: wins = {res['wins'][i]} ({res['wins'][i]/tot*100:.3f}%), wins_mata = {res['wins_mata'][i]} ({res['wins_mata'][i]/tot*100:.3f}%), kills = {res['kills'][i]} ({res['kills'][i]/tot*100:.3f}%)")
    st.write(f"Empates (normal o pozo retenido): {res['ties']} ({res['ties']/tot*100:.3f}%)")
    st.write(f"Total combinaciones: {tot}")
