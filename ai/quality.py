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
Do not invent missing facts. Remove AI commentary. Follow the original output format exactly.
Return only the corrected publish-ready content.
""".strip()
    repaired = generate(repair_prompt)
    return repaired.strip() or result
