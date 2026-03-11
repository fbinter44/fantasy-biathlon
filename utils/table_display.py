import streamlit as st


def style_results_table(df, highlighter):
    df = df.copy()
    df = df.drop(columns=["id"], errors="ignore")

    return (
        df.style
        .apply(highlighter, axis=1)
        .hide(axis="index")
    )


def display_results_table(df, highlighter, title):
    st.subheader(title)

    # On applique le style
    styled = (
        df.drop(columns=["id"], errors="ignore")
          .style
          .apply(highlighter, axis=1)
    )

    # On masque l’index ici (le seul endroit où ça marche vraiment)
    st.dataframe(styled, hide_index=True, use_container_width=True)
