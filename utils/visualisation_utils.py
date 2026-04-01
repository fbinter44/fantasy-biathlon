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

DISC_EMOJIS = {
    "Sprint": "⚡",
    "Poursuite": "🐺",
    "Individuel": "🥵",
    "Mass Start": "🏁",
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


def make_highlighter(favs, highlight_leader=False):
    def highlight(row):
        styles = [""] * len(row)

        name = row["name"]
        rank = row["rank"]

        # Règle 1 : Favoris
        if name in favs:
            styles = ["background-color: #fff2a8"] * len(row)  # jaune clair

        # Règle 2 : Top 10 général
        if int(rank) <= 10:
            styles = [s + "; font-weight: 600" for s in styles]  # gras léger

        # Règle 3 : Places 11 à 20 → transparence
        if 11 <= int(rank) <= 20:
            styles = [s + "; color: #999999" for s in styles]

        # Règle 4 : Leader finalisé → mise en évidence
        if highlight_leader and int(rank) == 1:
            row["name"] = "🥇 " + row["name"] + " 🎉🎉🎉"
            styles = [
                s + "; font-weight:700; border-left:4px solid #4caf50"
                for s in styles
            ]

        return styles

    return highlight


def percentage_color(p):
    if p < 20:
        return "#d9534f"  # rouge
    elif p < 40:
        return "#f0ad4e"  # orange
    else:
        return "#5cb85c"  # vert


def progress_bar(p):
    color = percentage_color(p)
    return f"""
    <div style="background:#eee; border-radius:6px; height:10px; width:100%; margin-top:6px;">
        <div style="
            width:{p}%;
            background:{color};
            height:10px;
            border-radius:6px;
        "></div>
    </div>
    """


def globe_card(title, percentage, included):
    color = percentage_color(percentage)
    emoji = DISC_EMOJIS.get(title, "🏆")

    # Badge moi inclus/exclu
    badge_color = "#d4edda" if included else "#f8d7da"
    badge_border = "#a3d7a5" if included else "#e5a3a3"
    badge_text = "MOI INCLUS" if included else "MOI EXCLU"
    badge_text_color = "#155724" if included else "#721c24"

    st.markdown(
        f"""
        <div style="
            padding: 18px 22px;
            border-radius: 12px;
            border: 1px solid #e2e2e8;
            background: white;
            margin-bottom: 16px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.06);
        ">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
        <div style="font-size:22px; font-weight:600;">
            {emoji} {title}
        </div>

        <div style="
            padding: 4px 10px;
            border-radius: 8px;
            background:{badge_color};
            border:1px solid {badge_border};
            color:{badge_text_color};
            font-size:12px;
            font-weight:600;
        ">
            {badge_text}
        </div>
        </div>

        <div style="font-size:16px; line-height:1.4; margin-bottom:6px;">
            Choisi(e) par 
            <b style="color:{color}; font-size:17px;">{percentage}%</b> 
            des joueurs
        </div>

        <div style="background:#f0f0f5; border-radius:6px; height:8px; width:100%; margin-top:8px;">
            <div style="
                width:{percentage}%;
                background:{color};
                height:8px;
                border-radius:6px;
                transition: width 0.4s ease;
            "></div>
        </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def top5_card(title, stats):
    # stats = dict comme celui que tu m'as donné
    top_stats = stats.top_stats
    my_place = stats.my_place
    if my_place == 1:
        my_place_str = "1er"
    elif my_place > 1:
        my_place_str = str(my_place) + "ème"
    total_players = top_stats["nb_total_players"]
    total_selected = top_stats["total"]

    # % global
    global_pct = round((total_selected / total_players) * 100) if total_players else 0

    # couleurs
    color = percentage_color(global_pct)

    # badge
    badge_color = "#e8eaff"
    badge_border = "#c7cdfc"
    badge_text_color = "#3b3f99"
    badge_text = "Pas dans mon top 5" if my_place == 0 else f"Mon prono : {my_place_str}"

    st.markdown(
        f"""
        <div style="
            padding: 18px 22px;
            border-radius: 12px;
            border: 1px solid #e2e2e8;
            background: white;
            margin-bottom: 16px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.06);
        ">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
        <div style="font-size:22px; font-weight:600;">
            🏅 {title}
        </div>

        <div style="
            padding: 4px 10px;
            border-radius: 8px;
            background:{badge_color};
            border:1px solid {badge_border};
            color:{badge_text_color};
            font-size:16px;
            font-weight:600;
        ">
            {badge_text}
        </div>
        </div>

        <div style="font-size:16px; line-height:1.4; margin-bottom:6px;">
            Sélectionné par 
            <b style="color:{color}; font-size:17px;">{global_pct}%</b> 
            des joueurs
        </div>

        <div style="background:#f0f0f5; border-radius:6px; height:8px; width:100%; margin-top:8px; margin-bottom:14px;">
            <div style="
                width:{global_pct}%;
                background:{color};
                height:8px;
                border-radius:6px;
                transition: width 0.4s ease;
            "></div>
        </div>

        <div style="font-size:15px; opacity:0.85;">
            <b>Détail par position :</b><br>
            1ère place : {top_stats['1er']} ({round(top_stats['1er']/total_players*100)}%)<br>
            2ème place : {top_stats['2ème']} ({round(top_stats['2ème']/total_players*100)}%)<br>
            3ème place : {top_stats['3ème']} ({round(top_stats['3ème']/total_players*100)}%)<br>
            4ème place : {top_stats['4ème']} ({round(top_stats['4ème']/total_players*100)}%)<br>
            5ème place : {top_stats['5ème']} ({round(top_stats['5ème']/total_players*100)}%)<br>
        </div>
        </div>
        """,
        unsafe_allow_html=True
    )
