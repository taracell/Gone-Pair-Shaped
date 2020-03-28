import asyncio
import re
from utils.miniutils import minidiscord
import random
import contextlib
from ..errors import errors
from . import player


class Game:
    def __init__(self, context, advanced_setup, whitelist):
        self.question_cards = []
        self.answer_cards = []

        self.used_question_cards = []
        self.used_answer_cards = []
        self.dealt_answer_cards = []

        self.context = context  # type: minidiscord.Context
        self.owner = context.author

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
        self.skipping = True

        if self.coro:
            self.coro.cancel()

    @contextlib.contextmanager
    def skip_if_skipping(self):
        if self.skipping:
            raise errors.SkippedError
        yield
        if self.skipping:
            raise errors.SkippedError

    async def begin(self):
        self.active = True
        while self.active:
            with contextlib.suppress(errors.SkippedError):
                await self.render_leaderboard()
                await self.round()
        await self.render_leaderboard(
            final=True
        )

    async def add_player(self, member):
        new_player = player.Player(self, member)
        self.players.append(
            new_player
        )
        await self.context.send(
            f"Welcome {member} to the game! "
            f"(There are now {len(self.players)} of a possible {self.maximumPlayers} in the game)",
            title="Someone joined!"
        )
        return new_player

    async def end(self, instantly, reason=True):
        self.active = False
        if instantly:
            self.skip()
        await self.context.send(
            f"The game {'has ended' if instantly else 'will end after this round'}"
            f"{' because' + reason if reason else ''}...",
            title="Your game evaporates into a puff of smoke"
        )

    async def round(self):
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
        for _player in players:
            coros.append(asyncio.create_task(_player.pick_cards(question, tsar)))

        self.coro = asyncio.gather(*coros, return_exceptions=True)
        with self.skip_if_skipping():
            results = await self.coro
        self.coro = None

        to_remove = []
        for position, result in enumerate(results):
            if not result:
                to_remove.append(players[position])
        for _player in to_remove:
            players.remove(_player)

        options = "\n".join(str(position + 1) + "- **" + "** | **".join(_player.picked) + "**"
                            for position, _player in enumerate(players))

        await self.context.send(
            options,
            title="The options are...",
            paginate_by="\n"
        )

        self.coro = asyncio.create_task(tsar.member.input(
            title="Pick a card by typing its number",
            prompt=options,
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

        self.coro = asyncio.sleep(self.round_delay)
        with self.skip_if_skipping():
            await self.coro
        self.coro = None

    async def render_leaderboard(self, final=False):
        players = sorted(self.players, key=lambda _player: _player.points, reverse=True)
        players = (
            ("🏆 " if _player.points == players[0].points else "🃏 ")
            + str(_player)
            + ": "
            + str(_player.points)
            + " " for _player in players
        )
        await self.context.send(
            "\n".join(players),
            title=f"Here's the {'final ' if final else ''}leaderboard{':' if final else ' so far...'}"
        )
