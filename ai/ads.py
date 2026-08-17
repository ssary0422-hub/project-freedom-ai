from ai.language import output_language_instruction
from ai.providers import generate_text


def make_ads(
    business,
    company,
    style,
    count=5,
    language="ko"
):
    language_instruction = output_language_instruction(
        language
    )

    prompt = f"""
You are a professional advertising copywriter.

Business category: {business}
Company / brand name: {company}
Brand mood: {style}

Create {count} advertising copy options that fit this brand.

Requirements:
- Make each option easy to read and attention-grabbing.
- Naturally reflect the business category and brand mood.
- Keep the company / brand name exactly as the user entered it.
- Avoid unnecessary explanations before or after the copy.
- Use natural marketing language for the target audience.
- Emojis may be used when they improve the copy.

OUTPUT LANGUAGE RULE:
{language_instruction}
"""

    return generate_text(prompt)
