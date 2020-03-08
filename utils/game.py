import asyncio
import random
import discord
import typing


class Player:
  def __init__(self, member, available_cards):
    self.member = member
    self.score = 0
    self.cards = []
    self.first_card = 0
    self.second_card = 0
    self.cards.append(random.sample(available_cards, 10))
    self.tsar_count = 0


class Game:
  def __init__(self, context, players, available_packs, enabled_packs, score_to_win: typing.Optional[int], min_players,
               max_players):
    enabled_packs = enabled_packs or ["base"]

    # Initialize basic game variables (Round number, which turn the players are on, etc.)
    self.active = False
    self.skip_round = True
    self.round_number = 0
    self.min = min_players
    self.max = max_players

    # Initialize context related game variables (Channel, creator, etc.)
    self.creator = context.author
    self.channel = context.channel
    self.ctx = context

    # Initialize our possible question and answer cards
    self.answer_cards = []
    self.question_cards = []

    for pack, questions, answers, _ in available_packs:
      if (pack in enabled_packs or "all" in enabled_packs) and f"-{pack}" not in enabled_packs:
        self.question_cards += questions  # Add our questions to the possible questions...
        self.answer_cards += answers  # ...and do the same for answers

    # Create a Player for everyone who's playing
    self.players = [Player(member, self.answer_cards) for member in players]
    random.shuffle(self.players)

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
    final_scores = "\n".join(
      [
        f'{user.member}: {user.score}' for user in sorted(self.players, key=lambda user: user.score, reverse=True)
      ]
    )
    await self.channel.send(
      embed=discord.Embed(
        title=f"The game has ended! Here are the scores\nScoreboard:",
        description=final_scores,
        color=discord.Color(0x3f51b5)
      )
    )

  async def end(self, _, __=False):
    embed = discord.Embed(description='<a:blobleave:527721655162896397> The game will end after this round',
                          color=discord.Color(0x8bc34a))
    self.active = False
    await self.channel.send(embed=embed)

  async def quit(self, player):
    embed = discord.Embed(description=f'{player.member} left the game, bye bye...',
                          color=discord.Color(0x8bc34a))
    self.players.remove(player)
    embed = await self.channel.send(embed=embed)
    if len(self.players) < self.min:
      embed = await self.channel.send(embed=discord.Embed(description=f'There are too few players left to continue...',
                                                          color=discord.Color(0x8bc34a)))
      await self.end(True)
    return embed

  async def begin_round(self):
    question = random.choice(self.question_cards)
    if all([player.tsar_count == self.players[0].tsar_count for player in self.players]):
      random.shuffle(self.players)  # shuffle the players so we don't know who will be tsar
    tsar = sorted(self.players, key=lambda player: player.tsar_count)[0]
    tsar.tsar_count += 1
    scores = "\n".join(
      [
        f'{user.member}: {user.score}' for user in sorted(self.players, key=lambda user: user.score, reverse=True)
      ]
    )
    await self.channel.send(
      embed=discord.Embed(
        title=f"Scoreboard (before round {self.round_number}" +
              (f", {self.score_to_win} points needed to win):" if self.score_to_win is not None else ")"),
        description=scores,
        color=discord.Color(0x3f51b5)
      )
    )
    await asyncio.sleep(5)
    await self.channel.send(
      embed=discord.Embed(
        title=f"The card tsar is {tsar.member.name}.",
        description=f"{question}\n\nEveryone check your dms for your card list.",
        color=discord.Color(0x212121)
      )
    )

    coroutines = []
    for user in self.players:
      if user != tsar:
        cards = f"In {self.channel.mention}\n\n{question}\n" + \
                "\n".join([f"{card_position + 1}: {card}" for card_position, card in enumerate(user.cards[0])])
        await user.member.send(
          embed=discord.Embed(
            title=f"Cards for {user.member}:", description=cards,
            color=discord.Color(0x212121))
        )

        async def wait_for_message(player_to_wait_for):
          def wait_check(message: discord.Message):
            try:
              return 0 <= int(message.content) <= 10 \
                     and message.author == player_to_wait_for.member \
                     and message.guild is None
            except ValueError:
              return False

          await player_to_wait_for.member.send(
            embed=discord.Embed(
              title=f"Please select a card from 1 to 10. You have 1 minute to decide" +
                    (" (1/2)" if question.count(r"\_\_") == 2 else ""),
              color=discord.Color(0x212121)
            )
          )
          try:
            player_to_wait_for.first_card = (
              await self.ctx.bot.wait_for('message', check=wait_check, timeout=60)
            ).content
          except asyncio.TimeoutError:
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
                title=f"Please select a card from 1 to 10. You have 1 minute to decide" + " (2/2)",
                color=discord.Color(0x212121)
              )
            )
            try:
              player_to_wait_for.second_card = (
                await self.ctx.bot.wait_for('message', check=wait_check, timeout=60)
              ).content
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
              description=f'The game will continue in {self.channel.mention}',
              color=discord.Color(0x8bc34a)
            )
          )
          await self.channel.send(
            embed=discord.Embed(
              description=f"{player_to_wait_for.member} has selected their card",
              color=discord.Color(0x8bc34a)
            )
          )
          return None

        coroutines.append(wait_for_message(user))
    await asyncio.gather(*coroutines)

    playing_users = self.players.copy()
    playing_users.remove(tsar)
    playing_users.sort(key=lambda user: random.random())

    responses = ""
    if question.count(r"\_\_") < 2:
      for user_position, user in enumerate(playing_users):
        responses += f'{user_position + 1}: {user.cards[0][int(user.first_card) - 1]}\n'
    else:
      for user_position, user in enumerate(playing_users):
        responses += f'{user_position + 1}: {user.cards[0][int(user.first_card) - 1]} ' \
                     f'| {user.cards[0][int(user.second_card) - 1]}\n'

    responses += "\n*(Player order is random)*"

    embed = discord.Embed(
      title=f'Select the winner, {tsar.member.name}',
      description=f'{question}\n\n{responses}',
      color=discord.Color(0x212121)
    )
    await self.channel.send(embed=embed)
    await tsar.member.send(embed=embed)
    await self.channel.send(embed=discord.Embed(title=f"Please answer in your DM", color=discord.Color(0x8bc34a)))

    def check(message: discord.Message):
      try:
        return 1 <= int(message.content) <= len(playing_users) \
               and message.author == tsar.member \
               and message.guild is None
      except ValueError:
        return False

    try:
      winner = (
        await self.ctx.bot.wait_for('message', check=check, timeout=120)
      ).content
      await tsar.member.send(
        embed=discord.Embed(
          description=f"Selected. The game will continue in {self.channel.mention}",
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

    winner = playing_users[int(winner) - 1]

    winner.score += 1

    await self.channel.send(
      embed=discord.Embed(
        title=f"The winner is:",
        description=f'{winner.member}! :tada:\n{winner.cards[0][int(winner.first_card) - 1]}' + (
          f" | {winner.cards[0][int(winner.second_card) - 1]}" if question.count(r"\_\_") == 2 else ""
        ),
        color=discord.Color(0x8bc34a)
      )
    )

    if question.count(r"\_\_") < 2:
      for player in self.players:
        if player != tsar:
          player.cards[0].pop(int(player.first_card) - 1)
          player.cards[0].append(random.choice(self.answer_cards))
    else:
      for player in self.players:
        if player != tsar:
          player.cards[0].pop(int(player.first_card) - 1)
          if int(player.first_card) < int(player.second_card):
            player.cards[0].pop(int(player.second_card) - 2)
          else:
            player.cards[0].pop(int(player.second_card) - 1)
          for _ in range(2):
            player.cards[0].append(random.choice(self.answer_cards))

    await asyncio.sleep(10)
