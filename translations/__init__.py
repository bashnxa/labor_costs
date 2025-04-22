import json
import os

from config import LANG


def load_translations() -> dict:
    translations = {}
    for filename in os.listdir(os.path.dirname(__file__)):
        if filename.endswith(".json"):
            lang_code = filename.split(".")[0]
            with open(
                os.path.join(os.path.dirname(__file__), filename), encoding="utf-8"
            ) as file:
                translations[lang_code] = json.load(file)
    return translations


TRANSLATIONS = load_translations()
DEFAULT_LANGUAGE = "en"
current_language = LANG


# Установка языка (один раз)
def set_language(lang: str):
    global current_language
    current_language = lang if lang in TRANSLATIONS else DEFAULT_LANGUAGE


# Функция для получения перевода
def t(key: str) -> str:
    return TRANSLATIONS.get(current_language, {}).get(
        key, TRANSLATIONS[DEFAULT_LANGUAGE].get(key, f"[{key}]")
    )
