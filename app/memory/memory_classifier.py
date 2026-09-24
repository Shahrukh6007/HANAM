def classify_memory(text):
    text = text.strip()

    lower_text = text.lower()

    if lower_text.startswith("my name is "):
        return "user_name", text[11:].strip()

    if lower_text.startswith("my favorite programming language is "):
        return "favorite_programming_language", text[36:].strip()

    if lower_text.startswith("my favorite language is "):
        return "favorite_programming_language", text[24:].strip()

    if lower_text in [
        "forget my favorite programming language",
        "forget my favorite programming language."
    ]:
        return "forget_favorite_programming_language", "programming_language"

    if lower_text.startswith("i like "):
        return "preference", text[7:].strip()

    if lower_text.startswith("i prefer "):
        return "preference", text[9:].strip()

    if lower_text.startswith("i enjoy "):
        return "preference", text[8:].strip()

    if lower_text.startswith("i love "):
        return "preference", text[7:].strip()

    if lower_text.startswith("i am building "):
        return "fact", text

    return None