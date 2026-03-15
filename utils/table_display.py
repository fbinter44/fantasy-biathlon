import streamlit as st


def style_results_table(df, highlighter):
    df = df.copy()
    df = df.drop(columns=["id"], errors="ignore")

    return (
        df.style
        .apply(highlighter, axis=1)
        .hide(axis="index")
    )


def display_results_table(df, highlighter, title, past_races, total_races):
    st.subheader(title)
    
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
