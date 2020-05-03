## Inspiration (but not code) taken from https://github.com/Elizafox/pycardcast
## PyCardCast by Minion3665
import aiohttp
import datetime
import re

class CardCastResponse:
    def __init__(self, success, code, status, request, response=""):
        self.status = status
        self.request = request
        self.code = code
        self.success = success
        self.response = response


class CardCastAuthor:
    def __init__(self, username, id):
        self.username = username
        self.id = id

class CardCastDeck:
    def __init__(
        self,
        author: CardCastAuthor,
        name: str,
        desc: str,
        play_code: str,
        listed: bool,
        creation: datetime.datetime,
        last_update: datetime.datetime,
        external_copyright: bool,
        external_copyright_url: str,
        category: str,
        black_count: int,
        white_count: int,
        rating: float,
        cardcast
    ):
        self.author = author
        self.name = name
        self.desc = desc
        self.play_code = play_code
        self.listed = listed
        self.creation = creation
        self.last_update = last_update
        self.external_copyright = external_copyright
        self.external_copyright_url = external_copyright_url
        self.category = category
        self.card_counts = {
            "black": black_count,
            "white": white_count
        }
        self.rating = rating
        self._cardcast = cardcast

    @classmethod
    def from_deckinfo(cls, deck_info, cardcast):
        print(deck_info)
        return cls(
            author=CardCastAuthor(
                username=deck_info["author"]["username"],
                id=deck_info["author"]["id"]
            ),
            name=deck_info["name"],
            desc=deck_info["description"],
            play_code=deck_info["code"],
            listed=not deck_info["unlisted"],
            creation=datetime.datetime.fromisoformat(deck_info["created_at"]),
            last_update=datetime.datetime.fromisoformat(deck_info["updated_at"]),
            external_copyright=deck_info["external_copyright"],
            external_copyright_url=deck_info["copyright_holder_url"],
            category=deck_info["category"],
            black_count=deck_info["call_count"],
            white_count=deck_info["response_count"],
            rating=deck_info["rating"],
            cardcast=cardcast
        )

    async def get_cards(self):
        return await self._cardcast.get_cards(self.play_code)

class CardCast:
    endpoint = "https://api.cardcastgame.com/v1/decks"
    deck_list_url = endpoint
    deck_info_url = endpoint + "/{code}"
    card_list_url = endpoint + "/{code}/cards"

    async def get_deck(self, code):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                    self.deck_info_url.format(code=code)
            ) as resp:
                if resp.status == 200:
                    response = await resp.json()
                    return CardCastResponse(
                        success=True,
                        code=code,
                        status=resp.status,
                        request=resp,
                        response=CardCastDeck.from_deckinfo(response, self)
                    )
                elif resp.status == 404:
                    return CardCastResponse(
                        success=False,
                        code=code,
                        status=resp.status,
                        request=resp,
                        response=f"Deck {code} not found"
                    )
                else:
                    return CardCastResponse(
                        success=False,
                        code=code,
                        status=resp.status,
                        request=resp,
                        response=f"Unknown error ({req.status})"
                    )

    async def get_cards(self, code):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                    self.card_list_url.format(code=code)
            ) as resp:
                if resp.status == 200:
                    response = await resp.json()
                    black_cards = (r"\_\_".join(part for part in card["text"]).strip() for card in response["calls"])
                    return CardCastResponse(
                        success=True,
                        code=code,
                        status=resp.status,
                        request=resp,
                        response={
                            "white": [card["text"][0] for card in response["responses"]],
                            "black": [
                              card if card.count(
                                r"\_\_"
                              ) > 1 else re.sub(
                                r"^(((?!(\\_\\_)).)*)(\? \\_\\_)$", r"\1?", card
                              ) for card in black_cards
                            ],
                        }
                    )
                elif resp.status == 404:
                    return CardCastResponse(
                        success=False,
                        code=code,
                        status=resp.status,
                        request=resp,
                        response=f"Deck {code} not found"
                    )
                else:
                    return CardCastResponse(
                        success=False,
                        code=code,
                        status=resp.status,
                        request=resp,
                        response=f"Unknown error ({req.status})"
                    )
