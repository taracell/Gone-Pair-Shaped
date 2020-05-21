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

from utils.miniutils import minidiscord
from cogs.gps.objects import player

class Game:
    def __init__(self, context, cog, use_whitelist, blacklist, lang="gb"):
        self.question_data = context.bot.gps_question_data
        self.answer_data = context.bot.gps_answer_data
        self.all_packs = context.bot.gps_packs

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