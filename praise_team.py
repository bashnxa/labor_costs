import secrets

import ollama

from translations import t


def praise_team():
    phrases = t("phrases")
    try:
        phrases_text = "\n".join([f"- {phrase}" for phrase in phrases])
        response = ollama.generate(
            model="llama3.1",
            system=t("phrases_system"),
            prompt=t("phrases_prompt").format(phrases_text=phrases_text),
        )
        return response["response"]
    except Exception:
        return secrets.choice(phrases)
