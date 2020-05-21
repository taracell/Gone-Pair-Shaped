"""Code to setup a game, returns a dictionary of settings"""
import asyncio
import functools

import emoji

from utils.miniutils import minidiscord
from utils.miniutils import data

import typing
import discord


class SetupManager:
    """
    The setup manager for new games
    """
    settings_save = data.Json("default_game_settings")
    timeout = 300

    def __init__(self, context):
        self.setup_message = None

        read_data = self.settings_save.read_key(self.context.guild.id)

        self.settings = {
            "rounds": read_data.get("rounds", 0),
            "points": read_data.get("points", 7),
            "anon": read_data.get("anon", False),
            "blanks": read_data.get("blanks", 0),
            "shuffles": read_data.get("shuffles", 0),
            "time": read_data.get("time", 15),
            "choose_time": read_data.get("choose_time", 150),
            "judge_choose_time": read_data.get("judge_choose_time", 300),
            "hand_size": read_data.get("hand_size", 10),
            "max_players": read_data.get("max_players", 25),
            "use_whitelist": False,
            "packs": read_data.get("packs", []),
            "ai": True,
        }

        self.context = context

    def __await__(self):
        """
        Setup a game based on current guild defaults
        """

        # _get_settings()
        menu = minidiscord.Input.Menu(
            bot=self.context.bot,
            callbacks=True,
            timeout_callback=self.cancel,
            timeout=300
        )

        menu.add("▶️️", callback=functools.partial(self.setup_type, False))
        menu.add("⚙️", callback=functools.partial(self.setup_type, True))

        setup_message = await self.context.send(
            "How do you want to setup your game?\n\n"
            "Press ▶️ to start with your guild's default settings\n"
            "Press ⚙ to change some options before starting",
            title="Setup your game"
        )
        return await menu(
            message=setup_message,
            responding=self.context.author
        )

    @staticmethod
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

    @staticmethod
    def cancellable_int(number):
        """
        Entering cancel will cause this integer to be -42069
        """
        if number.lower() == "cancel":
            return -42069
        elif number.lower() == "all":
            return -69420
        else:
            return int(number)

    async def cancel(self):
        """Cancel a game, before it even begins"""
        await self.setup_message.delete()
        return None

    async def flip_setting(self, setting_to_flip, menu_to_show):
        """
        Flip a boolean setting from True to False or vice versa
        """
        self.settings[setting_to_flip] = not self.settings[setting_to_flip]
        return await self.show_menu(menu_to_show)

    async def get_int_setting(self, setting_to_change, _min, _max, embed_title, embed_description, menu_to_show,
                              allow_all=False):
        """
        Sets a variable to the input by the user
        """
        try:
            await self.setup_message.clear_reactions()
            number = (await self.context.input(
                title=embed_title,
                prompt=f"Pick a number from {_min} to {_max}" + (
                    "\n" if embed_description != "" else "") + embed_description + "\nSay `cancel` to cancel",
                required_type=self.cancellable_int,
                timeout=self.timeout,
                edit=self.setup_message,
                error=f"That's not a number between {_min} and {_max}",
                check=lambda message: (
                                              (message.content.lower() in ["cancel", "-42069"])
                                              or (message.content.lower() in ["all", "-69420"] and allow_all)
                                              or (_min <= int(message.content) <= _max)
                                      ) and self.context.bot.loop.create_task(message.delete())
            ))[0]
        except asyncio.TimeoutError:
            await self.context.send(
                "Setting timed out, returning back to menu. Your settings are unchanged",
                title=embed_title,
                color=self.context.bot.colors["error"],
                delete_after=10
            )
        except Exception as e:
            print(f"Captured exception {e} while attempting to get int settings for {setting_to_change}")
        else:
            if number != -42069:
                self.settings[setting_to_change] = number
        finally:
            return await self.show_menu(menu_to_show)

    async def show_menu(self, menu_to_show="main"):
        """Show the main options menu for GPS games"""
        _menu = minidiscord.Input.Menu(
            bot=self.context.bot,
            callbacks=True,
            timeout_callback=self.cancel,
            timeout=self.timeout,
        )

        main = {
            "▶️️": ("Play", self.show_menu),
            "⏭️" if self.settings["rounds"] != 0 else "🔁": (
                "`Maximum rounds` " +
                (f"| {self.settings['rounds']}" if self.settings['rounds'] != 0 else "| Endless"),
                functools.partial(
                    self.get_int_setting,
                    "rounds",
                    0,
                    25000,
                    "How many rounds should there be per game?",
                    "Enter 0 for unlimited",
                    "main",
                )
            ),
            "🏁" if self.settings["points"] != 0 else "♾️": (
                "`Points to win ` " +
                (f"| {self.settings['points']}" if self.settings['points'] != 0 else "| No winner"),
                functools.partial(
                    self.get_int_setting,
                    "points",
                    0,
                    1000,
                    "How many points should you need to win a game?",
                    "Enter 0 for unlimited",
                    "main",
                )
            ),
            "🗂": ("`Packs`", self.show_menu),
            "divider1": ("", "------------------------------"),
            "divider2": ("", "**Additional Categories**"),
            "🃏": ("Card settings", functools.partial(self.show_menu, "cards")),
            "👨‍💻": ("Player settings", functools.partial(self.show_menu, "players")),
            "⏰": ("Timing settings", functools.partial(self.show_menu, "timers")),
            "divider3": ("", "------------------------------"),
            "💾": ("Save these settings for next time", self.show_menu),
            "⏹": ("Quit", self.cancel)
        }
        cards = {
            "📝": (
                f"`Write-your-own-cards` | {self.settings['blanks'] if self.settings['blanks'] != -69420 else 'ALL THE CARDS!!!'}",
                functools.partial(
                    self.get_int_setting,
                    "blanks",
                    0,
                    1000,
                    "How many write-your-own cards should there be?",
                    "You can type all to have a game with just blank cards",
                    "cards",
                    True
                )
            ),
            "📂" if self.settings['hand_size'] < 10 else "📁": (
                f"`Cards in hand       ` | {self.settings['hand_size']}",
                functools.partial(
                    self.get_int_setting,
                    "hand_size",
                    0,
                    50,
                    "How big should your hand be?",
                    "",
                    "cards",
                )
            ),
            "🔀" if self.settings['shuffles'] != 0 else "➡": (
                f"`Shuffles            ` | {self.settings['shuffles']}",
                functools.partial(
                    self.get_int_setting,
                    "shuffles",
                    0,
                    50,
                    "How many times should each player be allowed to shuffle?",
                    "",
                    "cards",
                )
            ),
            "⏪": ("Go back to the main settings", self.show_menu),
        }
        players = {
            "👥": (
                f"`Maximum players` | {self.settings['max_players']}",
                functools.partial(
                    self.get_int_setting,
                    "max_players",
                    3,
                    25,
                    "How many players should be able to join at once",
                    "",
                    "players",
                )
            ),
            "🔲" if self.settings["use_whitelist"] else "🔳": (
                f"`Whitelist`" if self.settings["use_whitelist"] else f"`Blacklist`",
                self.show_menu),
            "🌓" if self.settings["use_whitelist"] else "🌗": (
                "`Use blacklist`" if self.settings["use_whitelist"] else "`Use whitelist`",
                functools.partial(self.flip_setting, "use_whitelist", "players")),
            "❓" if self.settings['anon'] else "🗣": (
                "`Anonymous mode ` | " + ("Enabled" if self.settings['anon'] else "Disabled"),
                functools.partial(self.flip_setting, "anon", "players")),
            "🧠" if self.settings['ai'] else "💀": (
                "`Train bots     ` | " + ("Enabled -Thanks" if self.settings['ai'] else "Disabled"),
                functools.partial(self.flip_setting, "ai", "players")),
            "⏪": ("Go back to the main settings", self.show_menu),
        }
        timers = {
            "⏱": (
                f"`Judge choose time ` | {self.settings['judge_choose_time']}",
                functools.partial(
                    self.get_int_setting,
                    "judge_choose_time",
                    20,
                    600,
                    "How long should the judge get to choose?",
                    "(Enter in seconds)",
                    "timers",
                )
            ),
            emoji.emojize(self.get_clock(self.settings['choose_time'], 10, 300), use_aliases=True): (
                f"`Player choose time` | {self.settings['choose_time']}",
                functools.partial(
                    self.get_int_setting,
                    "choose_time",
                    10,
                    300,
                    "How long should players get to choose?",
                    "(Enter in seconds)",
                    "timers",
                )
            ),
            "⏳" if self.settings["time"] != 0 else "⌛": (
                f"`Between-round time` | {self.settings['time']}",
                functools.partial(
                    self.get_int_setting,
                    "time",
                    0,
                    150,
                    "How long should the pause between rounds be?",
                    "(Enter in seconds)",
                    "timers",
                )
            ),
            "⏪": ("Go back to the main settings", self.show_menu),
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

        await self.setup_message.edit(
            title=f"**Change {menu_settings['name']} settings**",
            content="\n".join(
                f"{reaction} {prompt}" if prompt else callback for reaction, (prompt, callback) in reactions.items())
        )

        await self.setup_message.clear_reactions()

        return await _menu(
            message=self.setup_message,
            responding=self.context.author
        )

    async def setup_type(self, chosen):
        """Determine if you want to edit settings (True) or start with the defaults (False)"""
        if not chosen:
            return None
        else:
            return await self.show_menu()
