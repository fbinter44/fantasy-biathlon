from scorer.results_scrapping import get_cup_results


class BiathlonStandings:

    def __init__(self, gender):
        self.gender = gender
        self.general = None
        self.sprint = None
        self.pursuit = None
        self.individual = None
        self.mass_start = None

    def load_all(self):
        self.sprint = get_cup_results(self.gender, "Sprint")
        self.pursuit = get_cup_results(self.gender, "Pursuit")
        self.mass_start = get_cup_results(self.gender, "Mass Start")
        self.individual = get_cup_results(self.gender, "Individual")
        self.general = get_cup_results(self.gender, "General")


if __name__ == "__main__":
    men_results = BiathlonStandings("Men")
    men_results.load_all()
