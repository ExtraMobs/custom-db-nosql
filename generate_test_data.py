import pickle
import random

silabas = [
    "ma",
    "pa",
    "os",
    "so",
    "ta",
    "te",
    "ri",
    "ir",
    "ok",
    "ko",
    "qe",
    "er",
    "re",
    "ça",
    "ço",
    "çu",
    "pu",
    "tu",
]


pickle.dump(
    ["".join([random.choice(silabas) for _ in range(4)]) for word_count in range(100)],
    open("string_list_dump", "wb"),
)
