import s_taper as s_t
from s_taper.consts import *

scheme = {
    "user_id": INT+KEY,
    "nickname": TEXT,
    "race": TEXT,
    "hp": INT,
    "damage": INT,
    "lvl": INT,
    "exp": INT
}
carachters = s_t.Taper("users", "data.db").create_table(scheme)

races = {"огр": (150, 15.0),
         "эльф": (75, 20.0),
         "гном": (150, 10.0),
         "дварф": (200, 5.0),
         "человек": (100, 10.0),
         "ведьмак": (100, 15.0)
         }

heal_scheme = {
    "user_id": INT+KEY,
    "food": TEXT
}
heals = s_t.Taper("heals", "data.db").create_table(heal_scheme)