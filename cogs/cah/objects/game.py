import asyncio
import re
from utils.miniutils import minidiscord
import random
import contextlib
from ..errors import errors


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

        self.maxRounds = 5 * len(self.players)
        self.maxPoints = 7
        self.hand_size = 10

        self.coro = None
        self.skipping = False
        self.active = False

        self.timeout = 150
        self.tsar_timeout = 300
        self.round_delay = 15

    def skip(self):
        if self.coro:
            self.coro.cancel()

        self.skipping = True

    @contextlib.contextmanager
    def skip_if_skipping(self):
        if self.skipping:
            raise errors.SkippedError
        yield
        if self.skipping:
            raise errors.SkippedError

    def round(self):
        self.skipping = False
        players = sorted(self.players, key=lambda _player: (_player.tsar_count, random.random()))

        tsar = players.pop(0)
        tsar.tsar_count += 1

        if not self.question_cards:
            self.question_cards = self.used_question_cards.copy()
            self.used_question_cards.clear()
        question = self.question_cards.pop(random.randint(0, len(self.question_cards) - 1))
        self.used_question_cards.append(question)

        coros = []
        for player in players:
            coros.append(asyncio.create_task(player.pick_cards(question, tsar)))

        self.coro = asyncio.gather(*coros, return_exceptions=True)
        with self.skip_if_skipping():
            results = await self.coro
        self.coro = None

        to_remove = []
        for position, result in enumerate(results):
            if not result:
                to_remove.append(players[position])
        for player in to_remove:
            players.remove(player)

        options = "\n".join(str(position + 1) + "- **" + "** | **".join(player.picked) + "**"
                            for position, player in enumerate(players))

        await self.context.send(
            options,
            title="The options are...",
            paginate_by="\n"
        )

        self.coro = asyncio.create_task(tsar.member.input(
            title="Pick a card by typing its number",
            prompt=options
            required_type=int,
            check=lambda message: 0 < int(message.content) <= len(players), 
            timeout=self.tsar_timeout
        ))
        with self.skip_if_skipping():
            try:
                winner = players[(await self.coro)[0] - 1]
            except asyncio.TimeoutError:
                await tsar.quit()
        self.coro = None

        picked = (re.sub(r'\.$', '', card) for card in winner.picked)
        if r"\_\_" in picked:
            for card in winner.picked:
                question = question.replace(r"\_\_", f"**{card}**")
        else:
            question += f" **{picked.__next__()}**"

        await self.context.send(
            f"**{winner}**: {question}",
            title=f"{self.context.bot.emojis['winner']} We have a winner!"
        )

        await asyncio.sleep(self.round_delay)
