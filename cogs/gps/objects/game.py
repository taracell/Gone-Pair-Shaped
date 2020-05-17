import asyncio
import contextlib
import math
import random
import re
import time
import typing
import functools
import emoji
import discord

from utils import pycardcast
from utils.miniutils import minidiscord
from . import player


class Game:
    def __init__(self, context, cog, use_whitelist, blacklist, lang="gb"):
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
        self.section = cog.leaderboard["section"]
        self.cog = cog
        self.listed_players = blacklist
        self.use_whitelist = use_whitelist
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
        self.global_leaderboard_section = None

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
        if len(code) == 5:
            code = code.upper()
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
        setup_message = None  # type: typing.Union[type(None), discord.Message]
        timeout = 300

        settings = {
            "rounds": 0,
            "points": 7,
            "anon": False,
            "blanks": 0,
            "shuffles": 0,
            "time": 15,
            "choose_time": 150,
            "judge_choose_time": 300,
            "hand_size": 10,
            "max_players": 25,
            "blacklist": [],
            "use_whitelist": False,
            "packs": [],
            "ai": True,
            "save": False,
        }

        ## _get_settings()

        def get_clock(_time, _min, _max):
            """
            Place in your time and the maximum and minimum values (inclusive) and get yourself back a nice little clock emote
            """
            diff = _max + 1 - _min
            possible_clocks = (12,) + tuple(range(1, 12))
            possible_clocks = tuple(
                clock for clocks in ((f":clock{_time}:", f":clock{_time}30:") for _time in possible_clocks) for clock in
                clocks)
            section = diff / len(possible_clocks)
            output = (_time - _min) // section
            return possible_clocks[int(output)]

        async def cancel():
            """Cancel a game, before it even begins"""
            self.active = False
            await setup_message.delete()

        async def flip_setting(setting_to_flip, menu_to_show):
            """
            Flip a boolean setting from True to False or vice versa
            """
            settings[setting_to_flip] = not settings[setting_to_flip]
            await show_menu(menu_to_show)

        async def show_menu(menu_to_show="main"):
            """Show the main options menu for CAH games"""
            _menu = minidiscord.Input.Menu(
                bot=self.context.bot,
                callbacks=True,
                timeout_callback=cancel,
                timeout=timeout
            )

            main = {
                "▶": ("Play", show_menu),
                "🛑": (
                    "`Maximum rounds` " +
                    (f"| {settings['rounds']}" if settings['rounds'] != 0 else "| *unlimited rounds*"),
                    show_menu),
                "🏁": (
                    "`Points to win ` " +
                    (f"| {settings['rounds']}" if settings['rounds'] != 0 else "| *you can never win*"),
                    show_menu),
                "🗃": ("`Packs`", show_menu),
                "divider1": ("", "------------------------------"),
                "divider2": ("", "**Additional Categories**"),
                "🃏": ("Card settings", functools.partial(show_menu, "cards")),
                "👨‍💻": ("Player settings", functools.partial(show_menu, "players")),
                "⏰": ("Timing settings", functools.partial(show_menu, "timers")),
                "divider3": ("", "------------------------------"),
                "💾": ("Save these settings for next time", show_menu),
                "⏹": ("Quit", cancel)
            }
            cards = {
                "📝": (
                    f"`Write-your-own-cards` | {settings['blanks']}",
                    show_menu),
                "📁" if settings['hand_size'] < 10 else "📂": (
                    f"`Cards in hand       ` | {settings['hand_size']}",
                    show_menu),
                "🔀" if settings['shuffles'] != 0 else "➡": (
                    f"`Shuffles            ` | {settings['shuffles']}",
                    show_menu),
                "⏪": ("Go back to the main settings", show_menu),
            }
            players = {
                "👥": (
                    f"`Maximum players` | {settings['max_players']}",
                    show_menu),
                "🔲" if settings["use_whitelist"] else "🔳": (
                    f"`Whitelist`" if settings["use_whitelist"] else f"`Blacklist`",
                    show_menu),
                "🌓" if settings["use_whitelist"] else "🌗": (
                    "`Use blacklist`" if settings["use_whitelist"] else "`Use whitelist`",
                    functools.partial(flip_setting, "use_whitelist", "players")),
                "❓" if settings['anon'] else "🗣": (
                    "`Anonymous mode ` | " + ("Enabled" if settings['anon'] else "Disabled"),
                    functools.partial(flip_setting, "anon", "players")),
                "🧠" if settings['ai'] else "💀": (
                    "`Train bots     ` | " + ("Thank you" if settings['ai'] else "Disabled 😢"),
                    functools.partial(flip_setting, "ai", "players")),
                "⏪": ("Go back to the main settings", show_menu),
            }
            timers = {
                "⏱": (
                    f"`Judge choose time ` | {settings['judge_choose_time']}", show_menu),
                emoji.emojize(get_clock(1, 1, 2), use_aliases=True): (
                    f"`Player choose time` | {settings['choose_time']}", show_menu),
                "⏳" if settings["time"] != 0 else "⌛": (
                    f"`Between-round time` | {settings['time']}", show_menu),
                "⏪": ("Go back to the main settings", show_menu),
            }

            options = {
                "main": {
                    "reactions": main,
                    "name": "Game"
                },
                "cards": {
                    "reactions": cards,
                    "name": "Card"
                },
                "players": {
                    "reactions": players,
                    "name": "Player"
                },
                "timers": {
                    "reactions": timers,
                    "name": "Timing"
                }
            }

            menu_settings = options.get(menu_to_show, options["main"])
            reactions = menu_settings["reactions"]

            for reaction, (prompt, callback) in reactions.items():
                if prompt != "":
                    _menu.add(reaction, callback)

            await setup_message.edit(
                content=f"**Change {menu_settings['name']} settings**\n" + "\n".join(f"{reaction} {prompt}" if prompt else callback for reaction, (prompt, callback) in reactions.items())
            )

            await setup_message.clear_reactions()

            await _menu(
                message=setup_message,
                responding=self.context.author
            )

        async def setup_type(chosen):
            """Determine if you want to edit settings (True) or start with the defaults (False)"""
            if not chosen:
                return
            else:
                await show_menu()

        menu = minidiscord.Input.Menu(
            bot=self.context.bot,
            callbacks=True,
            timeout_callback=cancel,
            timeout=300
        )

        menu.add("▶", callback=functools.partial(setup_type, False))
        menu.add("⚙", callback=functools.partial(setup_type, True))

        setup_message = await self.context.send(
            "How do you want to setup your game?\n\n"
            "Press ▶ to start with your guild's default settings\n"
            "Press ⚙ to change some options before starting",
            title="Setup your game"
        )
        await menu(
            message=setup_message,
            responding=self.context.author
        )

    async def begin(self):
        while self.active and (not self.maxRounds or self.completed_rounds < self.maxRounds):
            with contextlib.suppress(asyncio.CancelledError):
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

        try:
            await tsar.member.send(
                f"**The other players are answering:** {question}",
                title=f"{self.context.bot.emotes['tsar']} You're the tsar this round",
                color=self.context.bot.colors["status"]
            )
        except discord.Forbidden:
            await tsar.quit(
                reason="I can't DM them"
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

        if self.ai and self.cog.saving_enabled:
            picked_card_data = []
            for _player in players:
                player_picks = []
                for card in _player.picked:
                    player_picks.append(tuple(self.answer_data.keys())[tuple(self.answer_data.values()).index(card)])
                picked_card_data.append(".".join(sorted(player_picks)))

            this_round_data = (
                tuple(self.question_data.keys())[tuple(self.question_data.values()).index(question)],
                ",".join(picked_card_data),
                ".".join(sorted(tuple(self.answer_data.keys())[
                                    tuple(self.answer_data.values()).index(picked)
                                ] for picked in winner.picked))
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
        if self.cog.leaderboard["section"] == self.section and self.cog.saving_enabled:
            await self.context.send(
                "\n".join(lb),
                title=f"{self.context.bot.emotes['status']} and here's the global leaderboard",
                color=self.context.bot.colors["status"]
            )
