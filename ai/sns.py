from ai.language import output_language_instruction
from ai.providers import generate_text
from ai.quality import generate_with_quality_check


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
User's campaign request and mandatory details: {style}
Platform: {platform}

Create a social media post that satisfies all requirements:

1. Treat concrete details in the user's request as hard constraints and never invent a price, date, result, address or contact method.
2. Make the first line specific and attention-grabbing without clickbait.
3. Naturally include the company / brand name exactly as entered.
4. Use short paragraphs and generous line breaks for mobile reading.
5. Explain one clear customer benefit before the promotional message.
6. Include one concrete call to action; use [직접 입력 필요] for missing links or contact details.
7. End with 6 to 10 highly relevant hashtags instead of generic hashtag stuffing.
8. Adapt length, rhythm and emoji use to the selected platform; use no more than three emojis total.
9. Return only the publish-ready post, with no analysis or prefacing explanation.

OUTPUT LANGUAGE RULE:
{language_instruction}
"""

    return generate_with_quality_check(
        generate_text, prompt, company=company, min_chars=100
    )
