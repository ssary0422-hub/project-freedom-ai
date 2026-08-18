from ai.language import output_language_instruction
from ai.providers import generate_text
from ai.quality import generate_with_quality_check


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
User's campaign request and mandatory details: {style}

Create {count} advertising copy options that fit this brand.

Requirements:
- Treat every concrete detail in the user's request (offer, date, price, audience, channel, mandatory phrase) as a hard constraint. Never invent missing details.
- Make each option easy to scan in under three seconds: one strong hook, one clear customer benefit, and one specific call to action.
- Prefer concrete benefits over vague superlatives such as "최고", "혁신", or "특별한 경험".
- Make the options meaningfully different: benefit-led, event-led, trust-led, urgency-led, and friendly conversational.
- Keep the company / brand name exactly as the user entered it.
- If essential information is missing, use [직접 입력 필요] instead of inventing it.
- Avoid unnecessary explanations before or after the copy.
- Use natural marketing language for the target audience.
- Use at most one emoji per option and only when it improves clarity.
- Format each option as: 제목 | 핵심 혜택 | 행동 문구

OUTPUT LANGUAGE RULE:
{language_instruction}
"""

    return generate_with_quality_check(
        generate_text, prompt, company=company, min_chars=120
    )
