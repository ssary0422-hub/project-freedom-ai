LANGUAGE_NAMES = {
    "ko": "Korean",
    "en": "English",
    "ja": "Japanese",
    "th": "Thai",
    "zh": "Simplified Chinese",
    "es": "Spanish",
}

LANGUAGE_NATIVE_NAMES = {
    "ko": "한국어",
    "en": "English",
    "ja": "日本語",
    "th": "ไทย",
    "zh": "简体中文",
    "es": "Español",
}


def normalize_language(language):
    code = (language or "ko").strip().lower()
    return code if code in LANGUAGE_NAMES else "ko"


def output_language_instruction(language):
    code = normalize_language(language)
    english_name = LANGUAGE_NAMES[code]
    native_name = LANGUAGE_NATIVE_NAMES[code]

    return (
        f"Write the entire final answer in {english_name} ({native_name}). "
        "Do not switch to Korean unless Korean is the selected output language. "
        "Keep the user's company name, brand name, product names, URLs, "
        "and other proper nouns exactly as provided unless localization is clearly needed."
    )
