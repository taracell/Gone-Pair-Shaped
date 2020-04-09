## Inspiration (but not code) taken from https://github.com/Elizafox/pycardcast
## PyCardCast by Minion3665 and PineappleFanYT
import aiohttp

class CardCastResponse:
    def __init__(self, success, code, status, request, response=""):
        self.status = status
        self.request = request
        self.code = code
        self.success = success
        self.response = response

class CardCast:
    endpoint = "https://api.cardcastgame.com/v1/decks"
    deck_list_url = endpoint
    deck_info_url = endpoint + "/{code}"
    card_list_url = endpoint + "/{code}/cards"

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
                                r"^(((?!(\\_\\_)).)*)(\? \\_\\_)$", "$1?", card
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
