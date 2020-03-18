import asyncio
import random
import discord
import typing
import re


class Player:
    def __init__(self, member, game):
        self.member = member
        self.score = 0
        self.cards = []
        self.first_card = 0
        self.second_card = 0
        self.coroutines = []
        if len(game.answer_cards) < 10:
            game.answer_cards += game.used_answer_cards.copy()
            game.used_answer_cards = []
        self.cards += random.sample(game.answer_cards, 10)
        for card in self.cards:
            game.answer_cards.remove(card)
            game.used_answer_cards.append(card)
        self.tsar_count = 0


class Game:
    def __init__(self, context, players, available_packs, enabled_packs, score_to_win: typing.Optional[int],
                 min_players,
                 max_players):
        enabled_packs = [pack.lower() for pack in enabled_packs]

        # Initialize basic game variables (Round number, which turn the players are on, etc.)
        self.active = False
        self.skip_round = True
        self.round_number = 0
        self.min = min_players
        self.max = max_players

        # Initialize context related game variables (Channel, creator, etc.)
        self.creator = context.author
        self.ctx = context

        # Initialize our possible question and answer cards
        self.answer_cards = []
        self.question_cards = []
        self.used_question_cards = []
        self.used_answer_cards = []

        for pack, questions, answers, _ in available_packs:
            if (pack in enabled_packs or "all" in enabled_packs) and f"-{pack}" not in enabled_packs:
                self.question_cards += questions  # Add our questions to the possible questions...
                self.answer_cards += answers  # ...and do the same for answers

        if len(self.answer_cards) < 15 or len(self.question_cards) == 0:
            for pack, questions, answers, _ in available_packs:
                if pack == "base":
                    self.question_cards += questions
                    self.answer_cards += answers

        # Create a Player for everyone who's playing
        self.players = [Player(member, self) for member in players]
        random.shuffle(self.players)

        if self.answer_cards:
            self.used_answer_cards = []

        # Initialize user-defined options, including the number of points to win
        self.score_to_win = score_to_win

    async def start(self):
        self.active = True
        self.round_number = 0
        while self.active and \
                (self.score_to_win is None or not any([user.score >= self.score_to_win for user in self.players])):
            self.round_number += 1
            self.skip_round = False
            await self.begin_round()
            if self.active:
                await asyncio.sleep(10)
        final_scores = "\n".join(
            [
                f'{user.member}: {user.score}' for user in
                sorted(self.players, key=lambda user: user.score, reverse=True)
            ]
        )
        await self.ctx.send(
            final_scores,
            title=f"The game has ended! Here are the scores\nScoreboard:",
            color=discord.Color(0x3f51b5)
        )

    async def end(self, force, reason=None):
        if self.active:
            self.active = False
            self.skip_round = force
            if force:
                for player in self.players:
                    for coroutine in player.coroutines:
                        coroutine.cancel()
            await self.ctx.send(
                '<a:blobleave:527721655162896397> The game ' +
                ('has suddenly ended' if force else 'will end after this round') +
                (f" due to {reason}." if reason else "."),
                color=discord.Color(0x8bc34a)
            )

    async def quit(self, player):
        self.players.remove(player)
        for coroutine in player.coroutines:
            coroutine.cancel()
        embed = await self.ctx.send(
            f'{player.member} left the game, bye bye...',
            color=discord.Color(0x8bc34a)
        )
        if len(self.players) < self.min:
            embed = await self.ctx.send(
                f'There are too few players left to continue...',
                color=discord.Color(0x8bc34a)
            )
            await self.end(True, "there not being enough players")
        return embed

    async def begin_round(self):
        if len(self.question_cards) == 0:
            self.question_cards = self.used_question_cards.copy()
            self.used_question_cards = []
        question = self.question_cards.pop(random.randint(0, len(self.question_cards) - 1))
        self.used_question_cards.append(question)
        tsar = sorted(self.players, key=lambda plr: (plr.tsar_count, random.random))[0]
        tsar.tsar_count += 1
        scores = "\n".join(
            [
                f'{user.member}: {user.score}' for user in
                sorted(self.players, key=lambda user: user.score, reverse=True)
            ]
        )
        await self.ctx.send(
            scores,
            title=f"Scoreboard (before round {self.round_number}" +
                  (f", {self.score_to_win} points needed to win):" if self.score_to_win is not None else ")"),
            color=discord.Color(0x3f51b5)
        )
        await asyncio.sleep(5)
        await self.ctx.send(
            f"{question}\n\nEveryone check your dms for your card list."
            f"The card tsar is {tsar.member.name}",
            color=discord.Color(0x212121)
        )

        coroutines = []
        for user in self.players:
            if user != tsar:

                async def wait_for_message(player_to_wait_for):
                    messages_to_ignore = []

                    def wait_check(message: discord.Message):
                        try:
                            return 0 <= int(message.content) <= 10 \
                                   and message.author == player_to_wait_for.member \
                                   and message.guild is None \
                                   and message.content not in messages_to_ignore
                        except ValueError:
                            return False

                    await player_to_wait_for.member.send(
                        embed=discord.Embed(
                            title=f"Please select a card from 1 to 10. You have 2 and a half minutes to decide" +
                                  (" (1/2)" if question.count(r"\_\_") == 2 else ""),
                            color=discord.Color(0x212121)
                        )
                    )
                    try:
                        player_to_wait_for.first_card = (
                            await self.ctx.bot.wait_for('message', check=wait_check, timeout=150)
                        ).content
                        player_to_wait_for.first_card = player_to_wait_for.first_card \
                            if player_to_wait_for.first_card != "0" \
                            else "10"
                        messages_to_ignore = [
                            player_to_wait_for.first_card] if player_to_wait_for.first_card != "10" else \
                            ["0", "10"]
                    except asyncio.TimeoutError:
                        player_to_wait_for.coroutines = []
                        await self.quit(player_to_wait_for)
                        return await player_to_wait_for.member.send(
                            embed=discord.Embed(
                                title=f"You have been removed from the game for inactivity",
                                color=discord.Color(0x8bc34a)
                            )
                        )
                    if question.count(r"\_\_") == 2:
                        await player_to_wait_for.member.send(
                            embed=discord.Embed(
                                title=f"Please select a card from 1 to 10. You have 2 and a half minutes to decide, you"
                                      f" also can't pick the same card as your first card (2/2)",
                                color=discord.Color(0x212121)
                            )
                        )
                        try:
                            player_to_wait_for.second_card = (
                                await self.ctx.bot.wait_for('message', check=wait_check, timeout=150)
                            ).content
                            player_to_wait_for.second_card = player_to_wait_for.second_card \
                                if player_to_wait_for.second_card != "0" \
                                else "10"
                        except asyncio.TimeoutError:
                            await self.quit(player_to_wait_for)
                            await player_to_wait_for.member.send(
                                embed=discord.Embed(
                                    title=f"You have been removed from the game for inactivity",
                                    color=discord.Color(0x8bc34a)
                                )
                            )
                    await player_to_wait_for.member.send(
                        embed=discord.Embed(
                            title=f"Please wait for all players to select their card",
                            description=f'The game will continue in {self.ctx.mention}',
                            color=discord.Color(0x8bc34a)
                        )
                    )
                    s = "s" if question.count(r'\_\_') == 2 else ""
                    await self.ctx.send(
                        f"{player_to_wait_for.member} has selected their card{s}",
                        color=discord.Color(0x8bc34a)
                    )
                    player_to_wait_for.coroutines = []
                    return None

                wfm_user = asyncio.create_task(wait_for_message(user))
                coroutines.append(wfm_user)
                user.coroutines.append(wfm_user)
        if self.skip_round:
            for player in self.players:
                for coroutine in player.coroutines:
                    coroutine.cancel()
                player.coroutines = []
            return
        for user in self.players:
            if user != tsar:
                cards = f"In {self.ctx.mention}\n\n{question}\n" + \
                        "\n".join([f"{card_position + 1}: {card}" for card_position, card in enumerate(user.cards)])
                await user.member.send(
                    embed=discord.Embed(
                        title=f"Cards for {user.member}:", description=cards,
                        color=discord.Color(0x212121))
                )
        if self.skip_round:
            for player in self.players:
                for coroutine in player.coroutines:
                    coroutine.cancel()
                player.coroutines = []
            return
        await asyncio.gather(*coroutines, return_exceptions=True)
        if self.skip_round:
            for player in self.players:
                for coroutine in player.coroutines:
                    coroutine.cancel()
                player.coroutines = []
            return
        playing_users = self.players.copy()
        playing_users.remove(tsar)
        playing_users.sort(key=lambda user: random.random())

        responses = ""
        if question.count(r"\_\_") < 2:
            for user_position, user in enumerate(playing_users):
                responses += f'{user_position + 1}: {user.cards[int(user.first_card) - 1]}\n'
        else:
            for user_position, user in enumerate(playing_users):
                responses += f'{user_position + 1}: {user.cards[int(user.first_card) - 1]} ' \
                             f'| {user.cards[int(user.second_card) - 1]}\n'

        responses += "\n*(Player order is random)*"

        embed = discord.Embed(
            title=f'Select the winner, {tsar.member.name}',
            description=f'{question}\n\n{responses}',
            color=discord.Color(0x212121)
        )
        await tsar.member.send(embed=embed)
        await self.ctx.channel.send(embed=embed)
        await self.ctx.send(
            title=f"Please answer in your DM within 5 minutes",
            color=discord.Color(0x8bc34a)
        )

        def check(message: discord.Message):
            try:
                return 1 <= int(message.content) <= len(playing_users) \
                       and message.author == tsar.member \
                       and message.guild is None
            except ValueError:
                return False

        if self.skip_round:
            for player in self.players:
                for coroutine in player.coroutines:
                    coroutine.cancel()
                player.coroutines = []
            return

        winner = None
        try:
            wf_tsar = asyncio.create_task(self.ctx.bot.wait_for('message', check=check, timeout=300))
            tsar.coroutines.append(wf_tsar)
            winner = (
                await wf_tsar
            ).content
            await tsar.member.send(
                embed=discord.Embed(
                    description=f"Selected. The game will continue in {self.ctx.mention}",
                    color=discord.Color(0x8bc34a)
                )
            )
        except asyncio.TimeoutError:
            winner = random.randint(1, len(playing_users))
            await self.quit(tsar)
            await tsar.member.send(
                embed=discord.Embed(
                    title=f"You have been removed from the game for inactivity",
                    color=discord.Color(0x8bc34a)
                )
            )
        except asyncio.CancelledError:
            return

        winner = playing_users[int(winner) - 1]

        winner.score += 1

        card_in_context = question
        if question.count(r"\_\_") == 0:
            card_in_context = card_in_context + " " + winner.cards[int(winner.first_card) - 1]
        card_in_context = card_in_context.replace(
            "\_\_", re.sub("\.$", "", winner.cards[int(winner.first_card) - 1]), 1)
        card_in_context = card_in_context.replace(
            "\_\_", re.sub("\.$", "", winner.cards[int(winner.second_card) - 1]), 1)
        await self.ctx.send(
            f"**{winner.member.mention}** with **{card_in_context}**",
            title=f"The winner is:",
            color=discord.Color(0x8bc34a)
        )

        if question.count(r"\_\_") < 2:
            for player in self.players:
                if player != tsar:
                    player.cards.pop(int(player.first_card) - 1)
                    if len(self.answer_cards) == 0:
                        self.answer_cards = self.used_answer_cards.copy()
                        self.used_answer_cards = []
                    new_card = self.answer_cards.pop(random.randint(0, len(self.answer_cards) - 1))
                    player.cards.append(new_card)
                    self.used_answer_cards.append(new_card)
        else:
            for player in self.players:
                if player != tsar:
                    self.used_answer_cards.append(player.cards.pop(int(player.first_card) - 1))
                    if int(player.first_card) < int(player.second_card):
                        player.cards.pop(int(player.second_card) - 2)
                    else:
                        self.used_answer_cards.append(player.cards.pop(int(player.second_card) - 1))
                    for _ in range(2):
                        if len(self.answer_cards) == 0:
                            self.answer_cards = self.used_answer_cards.copy()
                            self.used_answer_cards = []
                        new_card = self.answer_cards.pop(random.randint(0, len(self.answer_cards) - 1))
                        player.cards.append(new_card)

        for player in self.players:
            for coroutine in player.coroutines:
                coroutine.cancel()
            player.coroutines = []
