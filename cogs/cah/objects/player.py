import random
import discord
import asyncio
import typing
import sys
import traceback
from utils.miniutils import decorators


class Player:
    def __init__(self, game_instance, member: discord.Member):
        # Save information about the game and who's playing it
        self.game = game_instance
        self.user = member
        self.member = None
        self.points = 0

        # Save information about the cards
        self.cards = []
        self.picked = []

        self.deal_cards()  # Deal cards until we have {the limit}

        # Save information about the coroutines the player is currently running
        self.coros = []

        self.tsar_count = 0

    def __str__(self):
        return "???" if self.game.anon else str(self.user)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.user == other.user and self.game == other.game
        return self.user == other

    async def advanced_init(self):
        self.member = await self.game.context.copy_context_with(
            channel=self.user.dm_channel or await self.user.create_dm(), author=self.user
        )

    def deal_cards(self):
        for _ in range(self.game.hand_size - len(self.cards)):
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

    @decorators.debug
    async def pick_cards(self, question, tsar) -> typing.Optional[typing.List[str]]:
        cards = question.count(r"\_\_") or 1
        for cardNumber in range(cards):
            if not self.cards:
                return False
            try:
                card, _ = await self.member.input(
                    title=f"Pick a card from 1 to {len(self.cards)} ({cardNumber + 1}/{cards})",
                    prompt=f"**The tsar is:** {tsar.user}\n"
                           f"**The question is:** {question}\n"
                           f"**Your cards are:**\n" +
                           f"\n".join([f'**{position + 1}-** {card}' for position, card in enumerate(self.cards)]),
                    paginate_by="\n",
                    required_type=int,
                    timeout=self.game.timeout,
                    check=lambda message: 0 <= int(message.content) <= len(self.cards),
                    error=f"That isn't a number from 1 to {len(self.cards)}"
                )
                card = card - 1
                card = self.cards.pop(card)
                self.picked.append(card)
                self.game.used_answer_cards.append(card)
            except asyncio.TimeoutError:
                await self.quit(
                    timed_out=True
                )
                return False
            except asyncio.CancelledError:
                return False
            except Exception as e:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                print(f"An error occurred, {e}")
                print("- [x] " + "".join(traceback.format_tb(exc_traceback)).replace("\n", "\n- [x] "))

        self.deal_cards()
        await self.member.send(
            f"Your cards have been chosen, the game will continue in {self.game.context.channel.mention}",
            title="Sit tight!"
        )
        await self.game.context.send(
            f"{self.user} has chosen their cards...",
            title="Picked!"
        )
        return True

    async def quit(self, ctx=None, timed_out=False):
        if self not in self.game.players:
            if not timed_out and ctx is not None:
                return await ctx.send(
                    f"{self.user}, I wasn't able to make you leave the game. Perhaps you left already?",
                    title="Huh? That's odd..."
                )
            return
        self.game.players.remove(self)
        for coro in self.coros:
            coro.cancel()
        self.coros.clear()
        await self.game.context.send(
            f"{self.user.mention} has left the game",
            title="Man down!"
        )
        if timed_out:
            await self.member.send(
                f"You've been timed out for inactivity",
                title="Bye"
            )
        if len(self.game.players) < self.game.minimumPlayers:
            await self.game.end(
                instantly=True,
                reason="there weren't enough players to continue"
            )
