from ai.language import output_language_instruction
from ai.providers import generate_text


def make_blog(
    topic,
    tone,
    length,
    language="ko",
    business="",
    company="",
):
    language_instruction = output_language_instruction(
        language
    )

    prompt = f"""
You are a professional blog content writer.

Topic: {topic}
Business / industry: {business}
Company / brand: {company}
Writing tone / brand mood: {tone}
Requested length: {length}

Write a high-quality blog article that satisfies all of these requirements:

1. An appealing title
2. A natural introduction
3. Main body with useful subheadings
4. Easy-to-read paragraph structure
5. A concise summary at the end
6. 15 relevant hashtags
7. Follow the requested length as closely as reasonably possible
8. Preserve company names, brand names and proper nouns as entered by the user
9. Insert 6 to 10 practical image directions naturally between paragraphs.
10. Format each direction on its own line as [실제 사진] or [AI 보조 이미지].
11. Prefer real photos for actual people, facilities, products, vehicles, food, treatment spaces and proof of condition.
12. Use AI images only for covers, concepts, checklists, educational diagrams and promotional banners.
13. Never invent facts, prices, equipment, staff, results or contact details. Mark missing facts as [직접 입력 필요].
14. Finish with a publishing checklist covering map, hours, contact method and relevant disclaimers.

OUTPUT LANGUAGE RULE:
{language_instruction}
"""

    return generate_text(prompt)
