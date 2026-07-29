import random

GIFS = {
    "uzgun": [
        "https://media.giphy.com/media/d2lcHJTG5Tscg/giphy.gif",
        "https://media.giphy.com/media/OPU6wzx8JrHna/giphy.gif"
    ],

    "tasarim": [
        "https://media.giphy.com/media/l3q2K5jinAlChoCLS/giphy.gif"
    ],

    "sinir": [
        "https://media.tenor.com/2roX3uxz_68AAAAC/angry.gif"
    ]
}


class GifManager:

    @staticmethod
    def random(name: str):

        if name not in GIFS:
            return None

        return random.choice(GIFS[name])