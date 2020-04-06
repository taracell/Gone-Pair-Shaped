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
                self.game.answer_cards = self.game.used_answer_cards
                self.game.used_answer_cards = []
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
                    title=f"{self.game.context.bot.emotes['choice']} Pick a card from 1 to "
                          f"{len(self.cards)} ({cardNumber + 1}/{cards})",
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
            except discord.Forbidden:
                await self.quit(
                    reason="I can't DM them"
                )
                return False
            except asyncio.TimeoutError:
                await self.quit(
                    reason="they took too long to answer"
                )
                return False
            except asyncio.CancelledError:
                return False
            except Exception as e:
                print(f"An error occurred, {e}")
                print("- [x] " + "".join(traceback.format_exc()).replace("\n", "\n- [x] "))

        self.deal_cards()
        await self.member.send(
            f"Your card{'s' if cards == 1 else ''} have been chosen, "
            f"the game will continue in {self.game.context.channel.mention}",
            title=f"{self.game.context.bot.emotes['tsar']} Sit tight!",
            color=self.game.context.bot.colors["success"]
        )
        await self.game.context.send(
            f"{self.user} has chosen their cards...",
            title=f"{self.game.context.bot.emotes['success']} Picked!",
            color=self.game.context.bot.colors["info"]
        )
        return True

    @decorators.debug
    async def quit(self, ctx=None, reason=""):
        if self not in self.game.players:
            if not reason and ctx is not None:
                return await ctx.send(
                    f"{self.user}, I wasn't able to make you leave the game. Perhaps you left already?",
                    title=f"{self.game.context.bot.emotes['valueerror']} Huh? That's odd...",
                    color=ctx.bot.colors["error"]
                )
            return
        self.game.players.remove(self)
        for coro in self.coros:
            coro.cancel()
        self.coros.clear()
        await self.game.context.send(
            f"{self.user.mention} has left the game" + (" because " + reason + "." if reason else "."),
            title=f"{self.game.context.bot.emotes['leave']} Man down!",
            color=self.game.context.bot.colors["error"]
        )
        if len(self.game.players) < self.game.minimumPlayers and self.game.joined:
            await self.game.end(
                instantly=True,
                reason="there weren't enough players to continue",
            )
