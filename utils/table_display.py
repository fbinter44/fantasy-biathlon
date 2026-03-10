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
    styled = style_results_table(df, highlighter)
    st.subheader(title)
    st.dataframe(styled, use_container_width=True)
