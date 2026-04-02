import streamlit as st


def style_results_table(df, highlighter):
    df = df.copy()
    df = df.drop(columns=["id"], errors="ignore")

    return (
        df.style
        .apply(highlighter, axis=1)
        .hide(axis="index")
    )


def is_finalized(df, past_races, total_races):
        remaining = total_races - past_races
        max_points = remaining * 90

        leader = int(df.iloc[0]["points"])
        runner_up = int(df.iloc[1]["points"])
        gap = leader - runner_up

        return past_races == total_races, gap > max_points



def display_results_table(df, highlighter, title, past_races, total_races, disc):
    st.subheader(title)

    finalized, awarded = is_finalized(df, past_races, total_races)

    if finalized:
        st.markdown("""
            <div style="
                background:#e8ffe8;
                color:#2e7d32;
                padding:6px 14px;
                border-radius:12px;
                font-weight:600;
                margin-bottom:10px;
                border:1px solid #a5d6a7;
            ">
                ✔️ Classement entériné
            </div>
        """, unsafe_allow_html=True)
    elif awarded:
         if disc != "general":
            st.markdown("""
                <div style="
                    background:#e8ffe8;
                    color:#2e7d32;
                    padding:6px 14px;
                    border-radius:12px;
                    font-weight:600;
                    margin-bottom:10px;
                    border:1px solid #a5d6a7;
                ">
                    🏆 Petit Globe décerné
                </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <div style="
                background:#fff8e1;
                color:#f9a825;
                padding:6px 14px;
                border-radius:12px;
                font-weight:600;
                margin-bottom:10px;
                border:1px solid #ffe082;
            ">
                ⏳ Classement encore ouvert
            </div>
        """, unsafe_allow_html=True)

    
    st.html(f"""
        <div style="display:flex; align-items:center; gap:12px; margin-bottom:10px;">

            <div style="
                background:#e8f4ff;
                color:#1e88e5;
                padding:4px 12px;
                border-radius:12px;
                font-weight:600;
                white-space:nowrap;
            ">
                {past_races} / {total_races} courses
            </div>

            <div style="flex-grow:1;">
                <div style="
                    width:100%;
                    height:6px;
                    background:#e0e0e0;
                    border-radius:3px;
                    overflow:hidden;
                ">
                    <div style="
                        width:{(past_races/total_races)*100}%;
                        height:100%;
                        background:#1e88e5;
                        border-radius:3px;
                    "></div>
                </div>
            </div>

            <div style="font-size:13px; font-weight:600; color:#1e88e5;">
                {int((past_races/total_races)*100)}%
            </div>

        </div>
        """)

    # On applique le style
    styled = (
        df.drop(columns=["id"], errors="ignore")
          .style
          .apply(highlighter, axis=1)
    )

    # On masque l’index ici (le seul endroit où ça marche vraiment)
    st.dataframe(styled, hide_index=True, use_container_width=True)


def df_to_html_old(df):
    html = df.to_html(
        index=False,
        escape=False,   # important pour afficher HTML dans les cellules
        classes="styled-table"
    )
    return html


def df_to_html(df, connected_user):
    # Ajout d'un attribut data-user sur chaque ligne
    rows = []
    for _, row in df.iterrows():
        user = row["Joueur"]
        attr = f'data-user="{user}"'
        html_row = "<tr " + attr + ">" + "".join(
            f"<td>{row[col]}</td>" for col in df.columns
        ) + "</tr>"
        rows.append(html_row)

    header = "".join(f"<th>{col}</th>" for col in df.columns)

    html = f"""
    <table class="styled-table">
        <thead><tr>{header}</tr></thead>
        <tbody>
            {''.join(rows)}
        </tbody>
    </table>
    """
    return html

def table_all_pronos_style(user):
    return f"""
    <style>

    /* Style général du tableau */
    .styled-table {{
        width: 100%;
        border-collapse: collapse;
        font-size: 15px;
        border-radius: 8px;
        overflow: hidden;
    }}

    /* Header */
    .styled-table thead tr {{
        background-color: #f3f4f6;
        border-bottom: 2px solid #d0d0d5;
    }}

    .styled-table th {{
        padding: 10px 12px;
        text-align: center;   /* centrage */
        font-weight: 700;
        color: #333;
    }}

    /* Cellules */
    .styled-table td {{
        padding: 8px 12px;
        text-align: center;   /* centrage */
        border-bottom: 1px solid #e5e7eb;
    }}

    /* Zebra striping */
    .styled-table tbody tr:nth-child(even) {{
        background-color: #fafafa;
    }}

    /* Hover */
    .styled-table tbody tr:hover {{
        background-color: #eef2ff;
    }}

    /* Highlight du joueur connecté */
    .styled-table tbody tr[data-user="{user}"] {{
        background-color: #fff7d6 !important;
        font-weight: 600;
    }}

    </style>
    """
