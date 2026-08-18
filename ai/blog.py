from ai.language import output_language_instruction
from ai.providers import generate_text
from ai.quality import generate_with_quality_check


def make_blog(
    topic,
    tone,
    length,
    language="ko",
    business="",
    company="",
    uploaded_photo_names=(),
):
    language_instruction = output_language_instruction(
        language
    )

    prompt = f"""
You are a professional blog content writer.

User's topic, goal and mandatory details: {topic}
Business / industry: {business}
Company / brand: {company}
Uploaded real photos ({len(uploaded_photo_names)}): {', '.join(uploaded_photo_names) if uploaded_photo_names else 'none'}
Writing tone / brand mood: {tone}
Requested length: {length}

Write a high-quality blog article that satisfies all of these requirements:

1. Treat every concrete user detail as a hard constraint. Never invent facts, prices, equipment, staff, results, medical claims or contact details.
2. Write a specific, useful title that accurately matches the article; avoid clickbait.
3. Open by identifying the reader's real problem and what the article will help them do.
4. Use descriptive subheadings, short mobile-friendly paragraphs, practical examples and actionable steps.
5. Remove filler, repeated conclusions and vague marketing superlatives.
6. Finish with a concise summary, one natural call to action, and 6 to 10 focused hashtags.
7. Follow the requested length as closely as reasonably possible
8. Preserve company names, brand names and proper nouns as entered by the user
9. Write a complete article that can be pasted directly into a blog. Do not include image directions, editing notes, bracketed placeholders or production instructions in the article.
10. If uploaded photos were supplied, refer only to facts visibly supported by those photos and never expose their file names or internal ordering labels.
11. Prefer concrete, useful explanations over generic promotional filler.
12. Keep the generated cover image separate from the article body; do not describe where an editor should insert it.
13. Omit missing business-specific facts instead of showing placeholders. For health, legal or financial topics, avoid diagnosis or guaranteed outcomes and add an appropriate concise disclaimer.
14. Finish with a publishing checklist only for verified details already supplied by the user; never expose internal editing instructions.
15. Return the publish-ready article only, without explaining how it was written.

OUTPUT LANGUAGE RULE:
{language_instruction}
"""

    return generate_with_quality_check(
        generate_text, prompt, company=company, min_chars=500
    )
