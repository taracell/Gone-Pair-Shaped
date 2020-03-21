from utils.miniutils import minidiscord

class Game:
    def __init__(self):
        self.question_cards = []
        self.answer_cards = []

        self.used_question_cards = []
        self.used_answer_cards = []
        self.dealt_answer_cards = []

        self.context = None  # type: minidiscord.Context

        self.players = []
        self.minimumPlayers = 3
        self.maximumPlayers = 25

        self.maxRounds = 5*len(self.players)
        self.maxPoints = 7
        self.hand_size = 10

    def end(self):
        return
