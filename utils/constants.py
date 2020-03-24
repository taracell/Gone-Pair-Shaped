import discord


def setup(bot):
    bot.colors = {
        "error": discord.Color(0xf44336),
        "success": discord.Color(0x8bc34a),
        "status": discord.Color(0x3f51b5),
        "info": discord.Color(0x212121)
    }

    bot.emojis = {
        "choice": "<a:blobcouncil:527721654361522186>",
        "success": "<:blobenjoy:527721625257508866>",
        "status": "<:blobnitro:527721625659899904>",
        "error": "<:bloboutage:527721625374818305>",
        "valueerror": "<:blobfrowningbig:527721625706168331>",
        "leave": "<a:blobleave:527721655162896397>",
        "enter": "<a:blobjoin:527721655041261579>",
        "tsar": "<:blobfingerguns:527721625605636099>",
        "settings": "<:blobidea:527721625563693066>",
        "uhoh": "<a:blobnervous:527721653795291136>",
        "winner": "<a:blobparty:527721653673918474>",
    }
