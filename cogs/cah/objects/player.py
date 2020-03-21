import random
import discord
from . import game
from utils.miniutils import minidiscord
import asyncio
import typing


class Player:
    def __init__(self, game_instance: game.Game, member: discord.Member):
        # Save information about the game and who's playing it
        self.game = game_instance
        self.member: minidiscord.Context = await game_instance.context.copy_context_with(channel=member, author=member)

        # Save information about the cards
        self.cards = []
        self.picked = []

        for _ in range(10):  # Repeat 10 times...
            self.deal_card()  # Deal a card

        # Save information about the coroutines the player is currently running
        self.coros = []

    def deal_card(self):
        if not self.game.answer_cards:
            self.game.answer_cards = self.game.used_answer_cards.copy()
            self.game.used_answer_cards.clear()
        card = self.game.answer_cards.pop(
            random.randint(
                1,
                len(self.game.answer_cards) - 1
            )
        )
        self.game.dealt_answer_cards.append(card)
        self.cards.append(card)

    async def pick_cards(self, question, tsar) -> typing.Optional[typing.List[str]]:
        cards = question.count(r"\_\_") or 1
        for cardNumber in range(question.count(r"\_\_")):
            try:
                card, _ = await self.member.input(
                    title=f"Pick a card from 1 to {len(self.cards)} ({cardNumber}/{cards})",
                    prompt=f"The tsar is **{tsar}**\n"
                           f"The question is **{question}**\n"
                           f"Your cards are:\n"
                           f"\n".join([f'{position + 1}- **{card}**' for position, card in enumerate(self.cards)]),
                    timeout=60 * 2.5,
                    check=lambda message: 0 <= int(message.content) <= len(self.cards),
                    error=f"That isn't a number from 1 to {len(self.cards)}"
                )
                card = self.cards.pop(card)
                self.picked.append(card)
                self.game.used_answer_cards.append(card)
            except asyncio.TimeoutError:
                await self.quit(
                    timed_out=True
                )
                return None
            except asyncio.CancelledError:
                return None

    async def quit(self, timed_out=False):
