import streamlit as st


def player_podium_card(rank, player, total_points, bonus_points):
    colors = {
        1: "#FFD700",  # or
        2: "#C0C0C0",  # argent
        3: "#CD7F32"   # bronze
    }

    emoji = {1: "🥇", 2: "🥈", 3: "🥉"}[rank]
    bg = colors[rank]

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