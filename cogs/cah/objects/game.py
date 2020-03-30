import asyncio
import re
from utils.miniutils import minidiscord
import random
from . import player
import contextlib
import time
import discord


class Game:
    def __init__(self, context, advanced_setup, whitelist, lang="gb"):
        self.question_cards = []
        self.answer_cards = []

        self.used_question_cards = []
        self.used_answer_cards = []
        self.dealt_answer_cards = []

        self.context = context  # type: minidiscord.Context
        self.owner = context.author
        self.advanced = advanced_setup
        self.whitelisted_players = whitelist
        self.lang = lang

        self.players = []
        self.minimumPlayers = 3
        self.maximumPlayers = 25

        self.maxRounds = 0
        self.maxPoints = 7
        self.hand_size = 10
        self.anon = False

        self.coro = None
        self.skipping = False
        self.active = False

        self.timeout = 150
        self.tsar_timeout = 300
        self.round_delay = 15

        self.completed_rounds = 0

    def skip(self):
        self.skipping = True
        if self.coro:
            self.coro.cancel()

    async def setup(self):
        setting_timeout = 30
        all_packs = self.context.bot.cah_packs.copy()
        with contextlib.suppress(asyncio.TimeoutError):
            self.maxPoints = (await self.context.input(
                title="How do you win?",
                prompt="How many points should someone need to win? Select a number from `0`-`100` (`0` is infinite). "
                       f"If you don't pick within {setting_timeout} seconds we'll pick the default of 7 rounds.",
                required_type=int,
                timeout=setting_timeout,
                check=lambda message: 0 <= int(message.content) <= 100,
                error="That's not a number from `0` to `100`... Try again"
            ))[0]
        with contextlib.suppress(asyncio.TimeoutError):
            packs = (await self.context.input(
                title="What packs would you like?",
                prompt=f"Run `{self.context.bot.get_main_custom_prefix(self.context)}packs` after this game to choose "
                       f"your language and see available packs. "
                       f"Separate individual packs with spaces, say `all` for every pack or put a `-` before a pack to "
                       f"ensure it doesn't show up. We recommend the `base` pack for beginners. "
                       f"If you don't pick within {setting_timeout * 2} seconds we'll give you the `base` pack.",
                timeout=setting_timeout * 2,
            ))[0].lower().split(" ")
            if not all_packs.get(self.lang, None):
                self.lang = "gb"
            lang_packs = all_packs.get(self.lang, None)
            for pack in packs:
                if not "-" + pack in packs:
                    question_cards_in_pack = lang_packs.get(pack + "b", [])
                    answer_cards_in_pack = lang_packs.get(pack + "w", [])
                    self.question_cards += question_cards_in_pack
                    self.answer_cards += answer_cards_in_pack
            if "all" in packs:
                for pack, cards in lang_packs.items():
                    if not "-" + pack[:-1] in packs:
                        if pack[-1:] == "w":
                            self.answer_cards += cards
                        else:
                            self.question_cards += cards

        if self.advanced:
            with contextlib.suppress(asyncio.TimeoutError):
                self.anon = (await self.context.input(
                    title="Want to be anonymous?",
                    prompt=f"If you choose `yes`, we won't let you know who's winning throughout the game, and we won't"
                           f" show you the leaderboard. If you don't answer within {setting_timeout} seconds we'll "
                           f"let other players know who you are.",
                    required_type=bool,
                    timeout=setting_timeout,
                    error="Pick either `yes` or `no`"
                ))[0]
            with contextlib.suppress(asyncio.TimeoutError):
                self.hand_size = (await self.context.input(
                    title="How big should your hand be?",
                    prompt=f"Pick anywhere from 1 to 25 cards. If you don't answer within {setting_timeout} seconds "
                           f"we'll select the default of 10.",
                    required_type=bool,
                    timeout=setting_timeout,
                    check=lambda message: 1 <= int(message.content) <= 25,
                    error="That's not a number from 1 to 25"
                ))[0]
            with contextlib.suppress(asyncio.TimeoutError):
                self.maxPoints = (await self.context.input(
                    title="How many rounds should I end after?",
                    prompt=f"After this many rounds, the game will stop. Just like that. This number must be between "
                           f"0 and 200 Press `0` to have unlimited rounds. If you don't select within {setting_timeout}"
                           f" seconds we'll let you continue forever.",
                    required_type=int,
                    timeout=setting_timeout,
                    check=lambda message: 0 <= int(message.content) <= 200,
                    error="That's not a number from `0` to `200`... Try again"
                ))[0]
            with contextlib.suppress(asyncio.TimeoutError):
                self.timeout = (await self.context.input(
                    title="How long should you get to pick your cards?",
                    prompt=f"Pick a number of seconds from 10 to 600. You will get this amount of time for __each__ "
                           f"card you need to pick on your turn. If you don't decide within {setting_timeout} seconds "
                           f"we'll give you 150 seconds.",
                    required_type=int,
                    timeout=setting_timeout,
                    check=lambda message: 10 <= int(message.content) <= 600,
                    error="That's not a number from `10` to `600`... Try again"
                ))[0]
            with contextlib.suppress(asyncio.TimeoutError):
                self.tsar_timeout = (await self.context.input(
                    title="How long should the tsar get to pick the best card?",
                    prompt=f"Pick a number of seconds from 10 to 600.  If you don't decide within {setting_timeout} "
                           f"seconds we'll give you 300 seconds.",
                    required_type=int,
                    timeout=setting_timeout,
                    check=lambda message: 10 <= int(message.content) <= 600,
                    error="That's not a number from `10` to `600`... Try again"
                ))[0]
            with contextlib.suppress(asyncio.TimeoutError):
                self.round_delay = (await self.context.input(
                    title="How long should we wait between rounds?",
                    prompt=f"Pick a number of seconds from 0 to 150.  If you don't decide within {setting_timeout} "
                           f"seconds we'll give you 15 seconds.",
                    required_type=int,
                    timeout=setting_timeout,
                    check=lambda message: 0 <= int(message.content) <= 150,
                    error="That's not a number from `0` to `150`... Try again"
                ))[0]

        basew = all_packs.get("gb", {}).get("basew", ["???"])
        baseb = all_packs.get("gb", {}).get("baseb", ["???"])
        while len(self.question_cards) < 1 or len(self.answer_cards) < self.hand_size * self.maximumPlayers:
            self.answer_cards.append(basew)
            self.question_cards.append(baseb)

        self.question_cards = [card for card in self.question_cards if card.count(r"\_\_") <= self.hand_size]
        await self.add_player(
            self.context.author
        )
        asyncio.create_task(self.context.send(
            "We've created your game, now let's get some players! "
            f"Type `{self.context.bot.get_main_custom_prefix(self.context)}join` to join this game." + (
                " Only whitelisted players can join." if self.whitelisted_players else ""
            ) +
            f" Once {self.minimumPlayers} have joined, you can begin by typing "
            f"`{self.context.bot.get_main_custom_prefix(self.context)}begin`, alternatively we'll start in 1 minute"
            f" or when there are {self.maximumPlayers} players.",
            title="Great!"
        ))
        expiry = time.time() + 60
        with contextlib.suppress(asyncio.TimeoutError):
            begin_messages = [
                self.context.bot.get_main_custom_prefix(self.context) + "begin",
                self.context.bot.get_main_custom_prefix(self.context) + "start",
                "juststartalready"
            ]
            while expiry >= time.time() and len(self.players) < self.maximumPlayers:
                response = await self.context.bot.wait_for(
                    "message",
                    check=lambda message: (
                            (
                                    message.content.lower().replace(" ", "") in
                                    [
                                        "imin",
                                        "iamin",
                                        "i'min",
                                        self.context.bot.get_main_custom_prefix(self.context) + "join"
                                    ]
                                    and not any(_player == message.author for _player in self.players)
                                    and (not self.whitelisted_players or message.author in self.whitelisted_players)
                            ) or (
                                    message.content.lower().replace(" ", "") in begin_messages
                                    and len(self.players) >= self.minimumPlayers
                                    and message.author == self.context.author
                            )
                    ),
                    timeout=expiry - time.time()
                )
                if response.content.lower().replace(" ", "") in begin_messages:
                    break
                else:
                    await self.add_player(
                        response.author
                    )
        if len(self.players) >= self.minimumPlayers:
            await self.context.send(
                "Your setup is complete, hold tight while we press the start button...",
                title="You're good to go"
            )
            return True

        await self.context.send(
            "Not enough players joined to start the game. ",
            title="Awwwwww, guess we can't play now..."
        )
        return False

    async def begin(self):
        self.active = True
        while self.active and (not self.maxRounds or self.completed_rounds < self.maxRounds):
            with contextlib.suppress(asyncio.CancelledError, discord.HTTPException):
                if not self.anon and not self.skipping:
                    await self.render_leaderboard()
                if not self.skipping:
                    self.coro = asyncio.create_task(self.round())
                    await self.coro
            self.completed_rounds += 1
            self.skipping = False
            if (
                    self.players and
                    sorted(self.players, key=lambda _player: _player.points, reverse=True)[0].points >= self.maxPoints
            ):
                break
        await self.render_leaderboard(
            final=True
        )

    async def add_player(self, member):
        new_player = player.Player(self, member)
        await new_player.advanced_init()
        if self.players:
            new_player.tsar_count = sorted(self.players, key=lambda _player: _player.tsar_count)[0].tsar_count
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
            f"The game {'ended' if instantly else 'will end after this round'}"
            f"{' because ' + reason if reason else ''}...",
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
            coros.append(_player.pick_cards(question, tsar))

        await tsar.member.send(
            f"**The other players are answering** {question}",
            title=f"You're the tsar this round"
        )

        await self.context.send(
            f"**The question is**{question}\n**The tsar is** {tsar.user}",
            title=f"Round {self.completed_rounds + 1}" +
                  (f" of {self.maxRounds}" if self.maxRounds else "") +
                  (f" ({self.maxPoints} points to win)" if self.maxPoints else "")
        )

        results = await asyncio.gather(*coros, return_exceptions=True)

        to_remove = []
        for position, result in enumerate(results):
            if not result:
                to_remove.append(players[position])
            elif isinstance(result, Exception):
                to_remove.append(players[position])
                raise result
        for _player in to_remove:
            players.remove(_player)
        if not players:
            raise asyncio.CancelledError

        options = "\n".join(str(position + 1) + "- **" + "** | **".join(_player.picked) + "**"
                            for position, _player in enumerate(players))

        await self.context.send(
            options,
            title="The options are...",
            paginate_by="\n"
        )

        try:
            winner = players[(await tsar.member.input(
                title="Pick a card by typing its number",
                prompt=options,
                required_type=int,
                check=lambda message: 0 < int(message.content) <= len(players),
                timeout=self.tsar_timeout
            ))[0] - 1]
        except asyncio.TimeoutError:
            await tsar.quit(timed_out=True)
            return await self.skip()

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

    async def render_leaderboard(self, final=False):
        players = sorted(self.players, key=lambda _player: _player.points, reverse=True)
        lb = (
            ("🏆 " if _player.points == players[0].points else "🃏 ")
            + str(_player)
            + ": "
            + str(_player.points)
            + " " for _player in players
        )
        await self.context.send(
            "\n".join(lb),
            title=f"{'The game has ended! ' if final else ''}"
                  f"Here's the {'final ' if final else ''}leaderboard{':' if final else ' so far...'}"
        )
