import json

import requests
from pydantic import BaseModel, Field, ValidationError


LM_STUDIO_URL = "http://localhost:1234/v1"


class DictionaryEntry(BaseModel):
    word: str = Field(min_length=1)
    definitions: list[str] = Field(min_length=1)
    synonyms: list[str]
    antonyms: list[str]
    examples: list[str] = Field(min_length=1)


def get_loaded_model_id() -> str:
    response = requests.get(f"{LM_STUDIO_URL}/models", timeout=10)
    response.raise_for_status()
    models = response.json().get("data", [])

    if not models:
        raise RuntimeError("LM Studiossa ei ole ladattua mallia.")

    return models[0]["id"]


def create_entry(word: str) -> DictionaryEntry:
    model_id = get_loaded_model_id()

    payload = {
        "model": model_id,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Olet huolellinen suomenkielinen sanakirja-avustaja. "
                    "Palauta vain pyydetyn JSON-skeeman mukainen tieto. "
                    "Määritelmät ja esimerkit kirjoitetaan suomeksi."
                ),
            },
            {
                "role": "user",
                "content": f"Laadi sanakirjamerkintä sanalle tai termille: {word}",
            },
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "dictionary_entry",
                "strict": True,
                "schema": DictionaryEntry.model_json_schema(),
            },
        },
        "temperature": 0.0,
        "max_tokens": 2000,
    }

    response = requests.post(
        f"{LM_STUDIO_URL}/chat/completions",
        json=payload,
        timeout=120,
    )
    response.raise_for_status()

    response_data = response.json()
    
    message = response_data["choices"][0]["message"]
    content = message.get("content") or message.get("reasoning_content")

    if not content:
        raise RuntimeError("Malli palautti tyhjän vastauksen.")

    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Malli ei palauttanut kelvollista JSONia.") from exc

    try:
        return DictionaryEntry.model_validate(data)
    except ValidationError as exc:
        raise RuntimeError("Vastaus ei vastannut vaadittua skeemaa.") from exc


def print_entry(entry: DictionaryEntry) -> None:
    print("\n--- Schema-validated AI Dictionary ---")
    print(f"\nSana: {entry.word}")

    print("\nMääritelmät:")
    for definition in entry.definitions:
        print(f"- {definition}")

    print("\nSynonyymit:")
    print(", ".join(entry.synonyms) if entry.synonyms else "Ei soveltuvia synonyymejä.")

    print("\nAntonyymit:")
    print(", ".join(entry.antonyms) if entry.antonyms else "Ei soveltuvia antonyymejä.")

    print("\nEsimerkit:")
    for example in entry.examples:
        print(f"- {example}")


def main() -> None:
    word = input("Anna haettava sana tai termi: ").strip()

    if not word:
        raise ValueError("Sana ei voi olla tyhjä.")

    print(f"\nLuodaan merkintä sanalle: {word} ...")
    entry = create_entry(word)
    print_entry(entry)


if __name__ == "__main__":
    main()
