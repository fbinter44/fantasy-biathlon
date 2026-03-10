# dev_runner.py

import sys
from core.ibu.client import IBUClient
from core.scoring.scoring_service import load_players_data, compute_all_players_points


def test_standings():
    """Test de la page Résultats Officiels."""
    print("=== TEST STANDINGS ===")

    ibu = IBUClient("2526")

    men = ibu.current_men_standings
    men.load_all()

    print("\n--- HOMMES ---")
    print("Général :")
    print(men.general)

    print("\nSprint :")
    print(men.sprint)

    print("\nPoursuite :")
    print(men.pursuit)

    print("\nIndividuel :")
    print(men.individual)

    print("\nMass Start :")
    print(men.mass_start)

    women = ibu.current_women_standings
    women.load_all()

    print("\n--- FEMMES ---")
    print("Général :")
    print(women.general)

    print("\nSprint :")
    print(women.sprint)

    print("\nPoursuite :")
    print(women.pursuit)

    print("\nIndividuel :")
    print(women.individual)

    print("\nMass Start :")
    print(women.mass_start)


def test_races():
    """Test de la page Résultats par course."""
    print("=== TEST RACES ===")

    ibu = IBUClient("2526")
    ibu.competitions.load_venues_results()
    for v in ibu.competitions.venues:
        v.load_all_results()

    for v in ibu.competitions.venues:
        print(f"\n=== {v.event_id} ===")
        for ep in v.epreuves:
            ep.load_results(force_refresh=False)
            print(f"\nCourse : {ep.short_desc} ({ep.race_id})")
            print(ep.top40())


def test_scoring():
    """Test du scoring complet."""
    print("=== TEST SCORING ===")

    ibu = IBUClient("2526")

    men = ibu.current_men_standings
    men.load_all()

    women = ibu.current_women_standings
    women.load_all()

    players = load_players_data()

    summary = compute_all_players_points(players, men, women)

    print("\n--- POINTS FANTASY ---")
    for p in summary.values():
        print(f"{p.player}: {p.total_points} points")


def test_all():
    """Test global."""
    test_standings()
    test_races()
    test_scoring()


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("Usage : python dev_runner.py [standings|races|scoring|all]")
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "standings":
        test_standings()
    elif cmd == "races":
        test_races()
    elif cmd == "scoring":
        test_scoring()
    elif cmd == "all":
        test_all()
    else:
        print("Commande inconnue :", cmd)
