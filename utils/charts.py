import altair as alt


def make_points_chart(df, color):
    df = df.copy()
    df["rank"] = df["rank"].astype(int)
    rank_order = df["rank"].sort_values().unique().tolist()

    bars = alt.Chart(df).mark_bar(size=20).encode(
        y=alt.Y("rank:N", sort=rank_order, axis=alt.Axis(title="Rang", labelAngle=0)),
        x=alt.X("points:Q", title="Points"),
        color=alt.value(color)
    )

    labels = alt.Chart(df).mark_text(
        align="left",
        baseline="middle",
        dx=5,
        color="black",
        fontSize=11
    ).encode(
        y=alt.Y("rank:N", sort=rank_order),
        x="points:Q",
        text="name:N"
    )

    return bars + labels
