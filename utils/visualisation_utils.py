"""
Composants visuels réutilisables pour l'application :
- Cartes podium (top 3)
"""

import streamlit as st


# ---------------------------------------------------------
# 1) Constantes visuelles
# ---------------------------------------------------------

PODIUM_COLORS = {
    1: "#FFD700",  # Or
    2: "#C0C0C0",  # Argent
    3: "#CD7F32",  # Bronze
}

PODIUM_EMOJIS = {
    1: "🥇",
    2: "🥈",
    3: "🥉",
}


# ---------------------------------------------------------
# 2) Composants visuels
# ---------------------------------------------------------

def player_podium_card(rank: int, player: str, total_points: int, bonus_points: int):
    """
    Affiche une carte podium pour un joueur.

    Paramètres :
    - rank : position (1, 2 ou 3)
    - player : nom du joueur
    - total_points : total de points
    - bonus_points : points bonus

    Exemple visuel :
        🥇 1er
        Joueur
        123 pts
        +10 bonus
    """
    if rank not in (1, 2, 3):
        st.error(f"Rank invalide : {rank}. Doit être 1, 2 ou 3.")
        return

    bg = PODIUM_COLORS[rank]
    emoji = PODIUM_EMOJIS[rank]

    st.markdown(
        f"""
        <div style="
            background:{bg};
            padding:16px;
            border-radius:12px;
            text-align:center;
            color:black;
            font-weight:600;
            box-shadow:0 2px 6px rgba(0,0,0,0.15);
        ">
            <div style="font-size:32px;">{emoji} {rank}e</div>
            <div style="font-size:22px; margin-top:4px;">{player}</div>
            <div style="font-size:20px; margin-top:6px;">{total_points} pts</div>
            <div style="font-size:14px; opacity:0.8;">+{bonus_points} bonus</div>
        </div>
        """,
        unsafe_allow_html=True
    )
