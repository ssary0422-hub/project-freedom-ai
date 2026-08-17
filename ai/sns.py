from ai.language import output_language_instruction
from ai.providers import generate_text


def make_sns(
    business,
    company,
    style,
    platform,
    language="ko"
):
    language_instruction = output_language_instruction(
        language
    )

    prompt = f"""
You are a professional social media marketing content writer.

Business category: {business}
Company / brand name: {company}
Desired mood: {style}
Platform: {platform}

Create a social media post that satisfies all requirements:

1. Make the first line attention-grabbing
2. Naturally include the company / brand name
3. Use emojis where appropriate
4. Use line breaks for easy reading
5. Include a natural promotional message
6. Include a call to visit, contact, book, buy, or learn more when appropriate
7. End with 15 relevant hashtags
8. Adapt the writing style to the selected platform
9. Keep company names, brand names and proper nouns exactly as entered by the user

OUTPUT LANGUAGE RULE:
{language_instruction}
"""

    return generate_text(prompt)
