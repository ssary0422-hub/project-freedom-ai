import re


def _remove_unfinished_markers(text):
    value = str(text or "")
    value = re.sub(
        r"(?:지금\s*)?\[(?:직접\s*)?입력\s*필요\](?:에서)?\s*(?:확인해\s*보세요|확인하세요)?[.!]?",
        "자세한 내용은 업체에 문의해 주세요.",
        value,
    )
    blocked = ("[AI 보조 이미지]", "[실제 사진]", "[업로드 사진")
    value = "\n".join(
        line for line in value.splitlines()
        if not any(marker in line for marker in blocked)
    )
    return value.replace("{{", "").replace("}}", "").strip()


def content_quality_issues(text, *, company="", min_chars=80):
    value = (text or "").strip()
    issues = []
    if len(value) < min_chars:
        issues.append(f"결과가 너무 짧음({len(value)}자)")
    if company and company not in value:
        issues.append("업체명 누락")
    lowered = value.lower()
    if any(marker in lowered for marker in ("as an ai", "i cannot", "요청하신 내용을 작성", "다음은 요청")):
        issues.append("불필요한 AI 설명 포함")
    if any(marker in value for marker in (
        "[직접 입력 필요]", "[입력 필요]", "[AI 보조 이미지]", "[실제 사진]",
        "[업로드 사진", "{{", "}}",
    )):
        issues.append("사용자에게 노출하면 안 되는 미완성 표식 포함")
    return issues


def generate_with_quality_check(generate, prompt, *, company="", min_chars=80):
    result = generate(prompt)
    issues = content_quality_issues(result, company=company, min_chars=min_chars)
    if not issues:
        return result

    repair_prompt = f"""
You are the final quality editor for publish-ready Korean marketing content.

Original brief:
{prompt}

Draft:
{result}

Problems found: {', '.join(issues)}

Rewrite the complete final content. Preserve every verified user detail and the exact company name.
Do not invent missing facts. If a sentence requires a missing fact, omit that sentence or replace it
with a natural generic action such as "자세한 내용은 업체에 문의해 주세요". Never output brackets,
placeholders, template variables, or instructions to the user. Remove AI commentary.
Follow the original output format exactly.
Return only the corrected publish-ready content.
""".strip()
    repaired = generate(repair_prompt)
    return _remove_unfinished_markers(repaired.strip() or result)
