from .points_table import POINTS_TABLE

def compute_regular_points(pred_list, df_top10):
    df_top10 = df_top10.copy()
    candidate_ids = df_top10["id"].tolist()

    total = 0
    total_bonus = 0
    details = {}

    for predicted_rank, athlete in enumerate(pred_list, start=1):
        if athlete not in candidate_ids:
            details[athlete] = 0
            continue

        row = df_top10[df_top10["id"] == athlete].iloc[0]
        real_rank = int(row["rank"])

        pts = POINTS_TABLE[real_rank - 1]

        if real_rank == predicted_rank:
            pts += 50
            total_bonus += 50

        details[athlete] = pts
        total += pts

    return total, total_bonus, details


def compute_globe_winner_bonus(pred_winners, df_men, df_women):
    """
    pred_winners = {"Men": "IBU123", "Women": "IBU456"}
    """

    # MEN
    if df_men.empty:
        bonus_men = 0
    else:
        real_men = df_men[df_men["rank"] == "1"].iloc[0]["id"]
        bonus_men = 50 if real_men == pred_winners.winner_men else 0

    # WOMEN
    if df_women.empty:
        bonus_women = 0
    else:
        real_women = df_women[df_women["rank"] == "1"].iloc[0]["id"]
        bonus_women = 50 if real_women == pred_winners.winner_women else 0

    return bonus_men, bonus_women
