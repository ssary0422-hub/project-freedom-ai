from ai.language import output_language_instruction
from ai.providers import generate_text


def make_blog(
    topic,
    tone,
    length,
    language="ko"
):
    language_instruction = output_language_instruction(
        language
    )

    prompt = f"""
You are a professional blog content writer.

Topic: {topic}
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

OUTPUT LANGUAGE RULE:
{language_instruction}
"""

    return generate_text(prompt)
