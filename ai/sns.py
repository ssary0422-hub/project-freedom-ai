from ai.language import output_language_instruction
from ai.providers import generate_text
from ai.quality import generate_with_quality_check
import json


def make_sns(
    business,
    company,
    style,
    platform,
    language="ko",
    recent_copy=(),
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
Previous openings from this user's recent posts (avoid repeating their wording, rhythm and premise):
{json.dumps(list(recent_copy), ensure_ascii=False)}

Create a social media post that satisfies all requirements:

1. Treat concrete details in the user's request as hard constraints and never invent a price, date, result, address or contact method.
2. Make the first line specific and attention-grabbing without clickbait.
3. Naturally include the company / brand name exactly as entered.
4. Use short paragraphs and generous line breaks for mobile reading.
5. Pick one concrete occasion, observation, question or product detail supported by the brief. Change the underlying idea across posts, not just the brand name or synonyms. Do not default to '한 입', '즐거움', '오늘은', '특별한 순간', '한눈에' unless the user explicitly requested that exact wording. Consider when and why someone would want the product; do not fabricate brand attributes.
6. Let the purpose decide the ending: a question for conversation, a quiet closing for awareness, an action only for a conversion request. Do not append an unsolicited contact invitation to every post. Never output placeholders.
7. End with 6 to 10 highly relevant hashtags instead of generic hashtag stuffing.
8. Adapt length, rhythm and emoji use to the selected platform; use no more than three emojis total.
9. Return only the publish-ready post, with no analysis or prefacing explanation.
10. Layout instructions, palette names, product_closeup and other production terms are instructions to you, not customer-facing copy. Do not describe the design process or turn the brief into the caption. Keep any requested AI/concept disclosure concise.

OUTPUT LANGUAGE RULE:
{language_instruction}
"""

    result = generate_with_quality_check(
        generate_text, prompt, company=company, min_chars=100
    )
    # Keep common model phrasing from leaking the user's production instruction
    # into publish-ready copy.
    return (result
            .replace("예약은 매장 문의로 안내해주세요", "예약 문의는 매장으로 부탁드립니다.")
            .replace("예약은 매장 문의로 안내해 주세요", "예약 문의는 매장으로 부탁드립니다."))
