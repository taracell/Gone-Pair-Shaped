import asyncio
import contextlib
import math
import random
import re
import time

import discord

from utils import pycardcast
from utils.miniutils import minidiscord
from . import player


class Game:
    def __init__(self, context, advanced_setup, whitelist, lang="gb"):
        self.cardcast = pycardcast.CardCast()
        self.question_data = context.bot.cah_question_data
        self.answer_data = context.bot.cah_answer_data
        self.all_packs = context.bot.cah_packs

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
        self.shuffles = 0
        self.ai = self.lang == "gb"

        self.coro = None
        self.skipping = False
        self.active = True
        self.joined = False
        self.chosen_options = False

        self.timeout = 150
        self.tsar_timeout = 300
        self.round_delay = 15

        self.completed_rounds = 0

    def skip(self):
        self.skipping = True
        if self.coro:
            self.coro.cancel()

    async def get_custom_pack(self, code):
        if len(code) == 5 and code.upper() == code:
            await self.context.send(
                f"Attempting to load custom deck {code}",
                title=f"{self.context.bot.emotes['settings']} Please Wait",
                color=self.context.bot.colors["status"],
            )
            try:
                response = await self.cardcast.get_deck(code)
                if response.success:
                    deck = response.response
                    response = await deck.get_cards()
                    if response.success:
                        cards = response.response
                        name = deck.name[:20] + '...' if len(deck.name) >= 24 else deck.name
                        author_name = deck.author.username[:20] + '...' if \
                            len(deck.author.username) >= 24 else deck.author.username
                        await self.context.send(
                            f"I've loaded the {name} custom deck "
                            f"(Last updated: {deck.last_update.strftime('%d/%m/%Y %l:%M%P UTC')})\n"
                            f"It's play code is {code}, for if you want to use it again\n"
                            f"(Full credits to {author_name} and CardCast)",
                            title=f"{self.context.bot.emotes['success']} Loaded custom deck {code}",
                            color=self.context.bot.colors["info"],
                        )
                        return cards
                    else:
                        name = deck.name[:20] + '...' if len(deck.name) >= 24 else deck.name
                        await self.context.send(
                            f"I couldn't load the {name} custom deck\n"
                            f"Try again later, perhaps next game?\n",
                            title=f"Couldn't load custom deck {code}",
                        )
                else:
                    await self.context.send_exception(
                        f"I couldn't find the {code} custom deck. Go make sure it's valid on "
                        "https://www.cardcastgame.com/",
                        title=f"Couldn't load custom deck {code}",
                    )
            except Exception as e:
                await self.context.send_exception(
                    f"Go tell my developers {e} and they might be able to fix the problem "
                    f"(support server invite in help)",
                    title=f"I couldn't load the {code} custom deck"
                )
        else:
            name = code[:20] + '...' if len(code) >= 24 else code
            await self.context.send_exception(
                f"The deck {name} doesn't appear to be a valid deck in your language or a valid custom deck. If it's "
                "meant to be a custom deck, check that you have capitalized all letters and it is a valid 5-character "
                "code from https://www.cardcastgame.com/#. If it's meant to be an included deck check your spelling "
                "and ensure that it exists in your language.",
                title=f"Couldn't load {name} deck",
            )
        return {
            "white": [],
            "black": []
        }

    async def setup(self):
        setting_timeout = 30
        with contextlib.suppress(asyncio.TimeoutError):
            self.maxPoints = (await self.context.input(
                title=f"{self.context.bot.emotes['settings']} How do you win?",
                prompt="How many points should someone need to win? Select a number from `0`-`100` (`0` is infinite). "
                       f"If you don't pick within {setting_timeout} seconds we'll pick the default of 7 rounds.",
                required_type=int,
                timeout=setting_timeout,
                check=lambda message: 0 <= int(message.content) <= 100,
                error=f"{self.context.bot.emotes['valueerror']} That's not a number from `0` to `100`... Try again",
                color=self.context.bot.colors['status']
            ))[0]
        with contextlib.suppress(asyncio.TimeoutError):
            packs = (await self.context.input(
                title=f"{self.context.bot.emotes['settings']} What packs would you like?",
                prompt=f"Run `{self.context.bot.get_main_custom_prefix(self.context)}packs` after this game to choose "
                       f"your language and see available packs. You can also choose a custom deck by putting a code "
                       f"from https://www.cardcastgame.com/#. We recommend `63EX5` for horrible people like yourself "
                       f"or `6VVUN` for a wholesome and family-friendly game.\n\n"
                       f"Separate individual packs with spaces, say `all` for every pack or put a `-` before a pack to "
                       f"ensure it doesn't show up. We recommend the `base` pack for beginners. "
                       f"If you don't pick within {setting_timeout * 5} seconds we'll give you the `base` pack.",
                timeout=setting_timeout * 5,
                color=self.context.bot.colors['status']
            ))[0].split(" ")
            lang_packs = self.all_packs.get(self.lang, None)["packs"]
            if not lang_packs:
                self.lang = "gb"
                lang_packs = self.all_packs.get(self.lang, None)["packs"]
            for pack in packs:
                if pack == "all":
                    continue
                if not "-" + pack in packs:
                    question_cards_in_pack = lang_packs.get(pack.lower() + "b", [])
                    answer_cards_in_pack = lang_packs.get(pack.lower() + "w", [])
                    if question_cards_in_pack == [] and answer_cards_in_pack == []:
                        try:
                            custom_pack = await self.get_custom_pack(pack)
                        except Exception as e:
                            print(e)
                            continue
                        if custom_pack["black"] or custom_pack["white"]:
                            self.ai = False
                        self.question_cards += custom_pack["black"]
                        self.answer_cards += custom_pack["white"]
                        continue
                    self.question_cards += question_cards_in_pack
                    self.answer_cards += answer_cards_in_pack
                    await self.context.send(
                        f"I've successfully loaded the {pack.lower()} deck!",
                        title=f"{self.context.bot.emotes['success']} Loaded deck {pack.lower()}",
                        color=self.context.bot.colors["info"],
                    )
            if "all" in packs:
                for pack, cards in lang_packs.items():
                    if not "-" + pack[:-1] in packs:
                        if pack[-1:] == "w":
                            self.answer_cards += cards
                        else:
                            self.question_cards += cards

        if self.advanced:
            with contextlib.suppress(asyncio.TimeoutError):
                if self.ai:
                    self.ai = (await self.context.input(
                        title=f"{self.context.bot.emotes['settings']} Can we train our bot?",
                        prompt=f"If you choose `yes`, we'll use anonymous information about what cards you pick to "
                               f"help us add bots into the game. Please say yes... *Note: This option is not available "
                               f"on games with custom packs and will be required to later add bots to your game. We "
                               f"won't store any data about who you are, what server this game was played in, any of "
                               f"your chat messages, or what other settings your game was created with*",
                        required_type=bool,
                        timeout=setting_timeout,
                        error=f"{self.context.bot.emotes['valueerror']} Pick either `yes` or `no`",
                        color=self.context.bot.colors['status']
                    ))[0]
            with contextlib.suppress(asyncio.TimeoutError):
                self.anon = (await self.context.input(
                    title=f"{self.context.bot.emotes['settings']} Want to be anonymous?",
                    prompt=f"If you choose `yes`, we won't let you know who's winning throughout the game, and we won't"
                           f" show you the leaderboard. If you don't answer within {setting_timeout} seconds we'll "
                           f"let other players know who you are.",
                    required_type=bool,
                    timeout=setting_timeout,
                    error=f"{self.context.bot.emotes['valueerror']} Pick either `yes` or `no`",
                    color=self.context.bot.colors['status']
                ))[0]
            with contextlib.suppress(asyncio.TimeoutError):
                self.hand_size = (await self.context.input(
                    title=f"{self.context.bot.emotes['settings']} How big should your hand be?",
                    prompt=f"Pick anywhere from 1 to 25 cards. If you don't answer within {setting_timeout} seconds "
                           f"we'll select the default of 10.",
                    required_type=int,
                    timeout=setting_timeout,
                    check=lambda message: 1 <= int(message.content) <= 25,
                    error=f"{self.context.bot.emotes['valueerror']} That's not a number from 1 to 25",
                    color=self.context.bot.colors['status']
                ))[0]
            with contextlib.suppress(asyncio.TimeoutError):
                self.maxRounds = (await self.context.input(
                    title=f"{self.context.bot.emotes['settings']} How many rounds should I end after?",
                    prompt=f"After this many rounds, the game will stop. Just like that. This number must be between "
                           f"0 and 200 Press `0` to have unlimited rounds. If you don't select within {setting_timeout}"
                           f" seconds we'll let you continue forever.",
                    required_type=int,
                    timeout=setting_timeout,
                    check=lambda message: 0 <= int(message.content) <= 200,
                    color=self.context.bot.colors['status'],
                    error=f"{self.context.bot.emotes['valueerror']}  That's not a number from `0` to `200`... Try again"
                ))[0]
            with contextlib.suppress(asyncio.TimeoutError):
                self.shuffles = (await self.context.input(
                    title=f"{self.context.bot.emotes['settings']} How many times would you like to be able to shuffle?",
                    prompt=f"How many times do you want to be able to shuffle inside of the game? Normally this option "
                           f"would be set to `0`, but we've been asked to add a mulligan command. If you don't choose "
                           f"within {setting_timeout} seconds we won't allow you to shuffle at all. This number must be"
                           f" between 0 and 50",
                    required_type=int,
                    timeout=setting_timeout,
                    check=lambda message: 0 <= int(message.content) <= 50,
                    color=self.context.bot.colors['status'],
                    error=f"{self.context.bot.emotes['valueerror']}  That's not a number from `0` to `50`... Try again"
                ))[0]
            with contextlib.suppress(asyncio.TimeoutError):
                self.timeout = (await self.context.input(
                    title=f"{self.context.bot.emotes['settings']} How long should you get to pick your cards?",
                    prompt=f"Pick a number of seconds from 10 to 600. You will get this amount of time for __each__ "
                           f"card you need to pick on your turn. If you don't decide within {setting_timeout} seconds "
                           f"we'll give you 150 seconds.",
                    required_type=int,
                    timeout=setting_timeout,
                    color=self.context.bot.colors['status'],
                    check=lambda message: 10 <= int(message.content) <= 600,
                    error=f"{self.context.bot.emotes['valueerror']} That's not a number from `10` to `600`... Try again"
                ))[0]
            with contextlib.suppress(asyncio.TimeoutError):
                self.tsar_timeout = (await self.context.input(
                    title=f"{self.context.bot.emotes['settings']} How long should the tsar get to pick the best card?",
                    prompt=f"Pick a number of seconds from 10 to 600.  If you don't decide within {setting_timeout} "
                           f"seconds we'll give you 300 seconds.",
                    required_type=int,
                    timeout=setting_timeout,
                    check=lambda message: 10 <= int(message.content) <= 600,
                    color=self.context.bot.colors['status'],
                    error=f"{self.context.bot.emotes['valueerror']} That's not a number from `10` to `600`... Try again"
                ))[0]
            with contextlib.suppress(asyncio.TimeoutError):
                self.round_delay = (await self.context.input(
                    title=f"{self.context.bot.emotes['settings']} How long should we wait between rounds?",
                    prompt=f"Pick a number of seconds from 0 to 150.  If you don't decide within {setting_timeout} "
                           f"seconds we'll give you 15 seconds.",
                    required_type=int,
                    timeout=setting_timeout,
                    check=lambda message: 0 <= int(message.content) <= 150,
                    color=self.context.bot.colors['status'],
                    error=f"{self.context.bot.emotes['valueerror']} That's not a number from `0` to `150`... Try again"
                ))[0]
        elif self.ai:
            await self.context.send(
                f"Don't have friends to play with? Don't worry, we don't either! We're currently working on adding "
                f"bots to our game to allow you to play by yourself and still have a great time. As part of that we're "
                f"collecting anonymous information on what answers you pick. If that's not ok with you, you can run "
                f"`{self.context.bot.get_main_custom_prefix(self.context)}end true` to end this game and "
                f"`{self.context.bot.get_main_custom_prefix(self.context)}play true` to start your next game in "
                f"advanced mode and get the option to turn this off.\n\n"
                f"*Note: We won't ever take data on games with custom packs. This option will also be required to "
                f"later add bots to your game. We won't store any data about who you are, what server this game was "
                f"played in, any of your chat messages, or what settings your game was created with*",
                title=f"{self.context.bot.emotes['settings']} We're making bots!",
                color=self.context.bot.colors['status'],
            )

        self.question_cards = [card for card in self.question_cards if card.count(r"\_\_") <= self.hand_size]

        if len(self.question_cards) < 1 or len(self.answer_cards) < 1:
            basew = self.all_packs.get("gb", {})["packs"].get("basew", ["???"])
            baseb = self.all_packs.get("gb", {})["packs"].get("baseb", ["???"])
            self.answer_cards += basew
            self.question_cards += baseb

        if len(self.answer_cards) < self.hand_size * (self.maximumPlayers * (self.shuffles + 1)):
            self.answer_cards *= math.ceil((self.maximumPlayers * self.hand_size) / len(self.answer_cards))

        self.question_cards = [card for card in self.question_cards if card.count(r"\_\_") <= self.hand_size]

        await self.add_player(
            self.context.author
        )
        self.chosen_options = True
        asyncio.create_task(
            self.context.send(
                f"We've created your game, now let's get some players! "
                f"Type `{self.context.bot.get_main_custom_prefix(self.context)}join` to join this game." + (
                    " Only whitelisted players can join." if self.whitelisted_players else ""
                ) +
                f" Once {self.minimumPlayers} have joined, you can begin by typing "
                f"`{self.context.bot.get_main_custom_prefix(self.context)}begin`, alternatively we'll start in 1 minute"
                f" or when there are {self.maximumPlayers} players.",
                title=f"{self.context.bot.emotes['success']} Great!",
                color=self.context.bot.colors["status"]
            )
        )
        expiry = time.time() + 60
        with contextlib.suppress(asyncio.TimeoutError):
            begin_messages = [
                self.context.bot.get_main_custom_prefix(self.context) + "begin",
                "juststartalready",
                "justfuckingstart",
                "justfuckinstart",
                "justfuckingstartalready",
                "justfuckinstartalready"
            ]
            while expiry >= time.time() and len(self.players) < self.maximumPlayers:
                response = await self.context.bot.wait_for(
                    "message",
                    check=lambda message: (
                            (
                                    (
                                            message.content.lower().replace(" ", "") in
                                            [
                                                "imin",
                                                "iamin",
                                                "i'min",
                                                self.context.bot.get_main_custom_prefix(self.context) + "join"
                                            ]
                                            and not any(_player == message.author for _player in self.players)
                                            and (
                                                    not self.whitelisted_players
                                                    or message.author in self.whitelisted_players
                                            )
                                    ) or (
                                            message.content.lower().replace(" ", "") in begin_messages
                                            and len(self.players) >= self.minimumPlayers
                                            and message.author == self.context.author
                                    )
                            )
                            and message.channel == self.context.channel
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
            self.joined = True
            await self.context.send(
                f"Your setup is complete, hold tight while we press the start button...",
                title=f"{self.context.bot.emotes['settings']} You're good to go",
                color=self.context.bot.colors["status"]
            )
            return True

        await self.context.send(
            f"Not enough players joined to start the game. ",
            title=f"{self.context.bot.emotes['uhoh']} Awwwwww, guess we can't play now...",
            color=self.context.bot.colors["error"]
        )
        return False

    async def begin(self):
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
                    sorted(
                        self.players, key=lambda _player: _player.points, reverse=True
                    )[0].points >= self.maxPoints != 0
            ):
                break
        await self.render_leaderboard(
            final=True
        )
        await self.context.send(
            "If you did, please upvote our bot (https://top.gg/bot/679361555732627476/vote#). We decided to put this "
            "message here instead of locking down features, so just... please? **It's free for you and would mean a "
            "lot to us**",
            title=f"{self.context.bot.emotes['success']} Enjoyed your game?",
            color=self.context.bot.colors['info']
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
            title=f"{self.context.bot.emotes['enter']} Someone joined!",
            color=self.context.bot.colors["success"]
        )
        return new_player

    async def end(self, instantly, reason=""):
        if not self.active:
            return
        self.active = False
        if instantly:
            self.skip()
        print("Ended the game")
        await self.context.send(
            f"The game {'ended' if instantly else 'will end after this round'} " +
            f"{' because ' + reason if reason else ''}...",
            title=f"{self.context.bot.emotes['uhoh']} Your game evaporates into a puff of smoke",
            color=self.context.bot.colors["status"]
        )

    async def round(self):
        self.skipping = False
        players = sorted(self.players, key=lambda _player: (_player.tsar_count, random.random()))

        for _player in players:
            _player.picked = []

        tsar = players.pop(0)
        tsar.tsar_count += 1

        if not self.question_cards:
            self.question_cards = self.used_question_cards
            self.used_question_cards = []
        question = self.question_cards.pop(random.randint(0, len(self.question_cards) - 1))
        self.used_question_cards.append(question)

        await tsar.member.send(
            f"**The other players are answering:** {question}",
            title=f"{self.context.bot.emotes['tsar']} You're the tsar this round",
            color=self.context.bot.colors["status"]
        )

        await self.context.send(
            f"**The question is:** {question}\n**The tsar is:** {tsar.user}",
            title=f"{self.context.bot.emotes['status']}  Round {self.completed_rounds + 1}" +
                  (f" of {self.maxRounds}" if self.maxRounds else "") +
                  (f" ({self.maxPoints} points to win)" if self.maxPoints else ""),
            color=self.context.bot.colors["info"]
        )

        coros = []
        for _player in players:
            coros.append(_player.pick_cards(question, tsar))

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

        random.shuffle(players)
        options = question + "\n\n" + "\n".join(str(position + 1) + "- **" + "** | **".join(_player.picked) + "**"
                                                for position, _player in enumerate(players))

        await self.context.send(
            options,
            title=f"{self.context.bot.emotes['choice']} The options are... (Tsar, pick in your DM)",
            paginate_by="\n",
            color=self.context.bot.colors["info"]
        )

        try:
            winner = players[(await tsar.member.input(
                title=f"{self.context.bot.emotes['choice']} Pick a winner by typing their number",
                prompt=options,
                required_type=int,
                check=lambda message: 0 < int(message.content) <= len(players),
                timeout=self.tsar_timeout,
                paginate_by="\n",
                color=self.context.bot.colors["status"],
                error=f"{self.context.bot.emotes['valueerror']} That isn't a valid card"
            ))[0] - 1]
            await tsar.member.send(
                f"The winner has been chosen, the crowning will commence instantly in {self.context.channel.mention}",
                title=f"{self.context.bot.emotes['status']} Eyyyyyyyyyyyyyyyyyy!",
                color=self.context.bot.colors["success"]
            )
        except asyncio.TimeoutError:
            await tsar.quit(
                reason="they took too long to answer"
            )
            return self.skip()
        except discord.Forbidden:
            await tsar.quit(
                reason="I can't DM them"
            )
            return self.skip()

        if self.ai:
            picked_card_data = []
            for _player in players:
                player_picks = []
                for card in _player.picked:
                    player_picks.append(tuple(self.answer_data.keys())[tuple(self.answer_data.values()).index(card)])
                picked_card_data.append(".".join(player_picks))

            this_round_data = (
                tuple(self.question_data.keys())[tuple(self.question_data.values()).index(question)],
                ",".join(sorted(picked_card_data)),
                ".".join(tuple(self.answer_data.keys())[
                                tuple(self.answer_data.values()).index(picked)
                            ] for picked in winner.picked)
            )

            old_data = self.context.bot.AIDataStore.load_data()
            old_question = old_data.get(this_round_data[0], None)
            if old_question is None:
                old_data[this_round_data[0]] = {}
                old_question = {}
            old_options = old_question.get(this_round_data[1], None)
            if old_options is None:
                old_data[this_round_data[0]][this_round_data[1]] = {}
                old_options = {}
            if old_options.get(this_round_data[2], None) is None:
                old_data[this_round_data[0]][this_round_data[1]][this_round_data[2]] = 0

            old_data[this_round_data[0]][this_round_data[1]][this_round_data[2]] += 1

            self.context.bot.AIDataStore.save_data(old_data)

        picked = (re.sub(r'\.$', '', card) for card in winner.picked)
        if r"\_\_" in question:
            for card in winner.picked:
                card = re.sub(r'\.$', '', card)
                question = question.replace(r"\_\_", f"**{card}**", 1)
        else:
            question += f" **{next(picked)}**"

        await self.context.send(
            f"**{winner}**: {question}",
            title=f"{self.context.bot.emotes['winner']} We have a winner!",
            color=self.context.bot.colors["status"]
        )
        winner.points += 1

        await asyncio.sleep(self.round_delay)

    async def render_leaderboard(self, final=False):
        players = sorted(self.players, key=lambda _player: _player.points, reverse=True)
        lb = (
            (self.context.bot.emotes["trophy"] + " " if _player.points == players[0].points else "")
            + str(_player.user)
            + ": "
            + str(_player.points)
            + " " for _player in players
        )
        await self.context.send(
            "\n".join(lb),
            title=f"{self.context.bot.emotes['status']} {'The game has ended! ' if final else ''}"
                  f"Here's the {'final ' if final else ''}leaderboard{':' if final else ' so far...'}",
            color=self.context.bot.colors["status"]
        )
