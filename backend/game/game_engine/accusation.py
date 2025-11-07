class AccusationEngine:
    """
    Handles checking player accusations.
    """

    def __init__(self, solution):
        self.solution = solution

    def check_accusation(self, character, weapon, room):
        match = (
            self.solution["character"] == character
            and self.solution["weapon"] == weapon
            and self.solution["room"] == room
        )
        return match
