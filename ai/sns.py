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
6. Include one natural call to action. If no link or contact was supplied, invite the reader to contact the business without inventing a channel. Prefer conversational Korean such as "예약 문의는 매장으로 부탁드립니다." Never use instruction-like wording such as "예약은 매장 문의로 안내해주세요" and never output placeholders.
7. End with 6 to 10 highly relevant hashtags instead of generic hashtag stuffing.
8. Adapt length, rhythm and emoji use to the selected platform; use no more than three emojis total.
9. Return only the publish-ready post, with no analysis or prefacing explanation.

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
