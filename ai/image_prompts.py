def _subject_for(business: str, context: str) -> str:
    source = f"{business} {context}".lower()
    if any(key in source for key in ("카페", "coffee", "cafe", "베이커리", "bakery")):
        if any(key in source for key in ("복숭아", "peach")):
            return "a photorealistic iced peach latte in a clear glass, visible peach pieces, soft pink and cream layers"
        return "a photorealistic signature cafe beverage on a clean wooden table"
    if any(key in source for key in ("병원", "의원", "clinic", "hospital", "정형외과")):
        return "a bright, clean and trustworthy modern medical consultation room, no patients identifiable"
    if any(key in source for key in ("러닝", "마라톤", "running", "fitness", "헬스")):
        return "diverse adult runners training together outdoors at sunrise, natural athletic movement"
    if any(key in source for key in ("중고차", "자동차", "car", "auto")):
        return "a clean modern car in a professional dealership showroom, realistic commercial photography"
    if any(key in source for key in ("음식", "식당", "restaurant", "food")):
        return "an appetizing hero shot of the signature dish in a welcoming restaurant"
    return f"a realistic commercial scene clearly representing this business: {business}"


def _creative_subject(custom_concept: str, business: str, context: str) -> str:
    concept = (custom_concept or "").strip()
    lowered = concept.lower()
    if any(key in lowered for key in ("고양이", "cat", "kitten")):
        return (
            "adorable expressive cats as the only characters, acting out the "
            f"business idea ({business}) in a visibly funny, playful situation; "
            "no human workers or human customers"
        )
    if any(key in lowered for key in ("강아지", "개", "dog", "puppy")):
        return (
            "adorable expressive dogs as the only characters, acting out the "
            f"business idea ({business}) in a visibly funny, playful situation; "
            "no human workers or human customers"
        )
    return (
        "a scene that literally and unmistakably expresses this user-requested "
        f"creative concept: {concept}; connected clearly to {business} and {context}"
    )


def build_marketing_image_prompt(*, business: str, context: str, mood: str,
                                 image_style: str, placement: str,
                                 custom_concept: str = "") -> str:
    subject = (
        _creative_subject(custom_concept, business, context)
        if custom_concept.strip()
        else _subject_for(business, f"{context} {mood} {image_style}")
    )
    priority = (
        f"The user's custom concept is the HIGHEST priority: {custom_concept}. "
        "Do not replace its characters or idea with a conventional business scene."
        if custom_concept.strip()
        else ""
    )
    return f"""
Create one premium commercial photograph for {placement}.
The main subject MUST be {subject}.
{priority}
Business category: {business}.
Campaign context: {context}.
Mood: {mood}. Visual style: {image_style}.
Use believable materials, natural lighting, accurate proportions and a professional advertising composition.
Keep a clean area for copy to be added later by the website.
STRICTLY NO text, letters, words, logos, signs, labels, watermarks, captions, borders or fake writing anywhere in the image.
Do not substitute an unrelated landscape, object, food or location.
Photorealistic, high detail, commercially usable.
""".strip()


def build_poster_background_prompt(user_prompt: str) -> str:
    subject = _subject_for("", user_prompt)
    return f"""
Create a vertical premium advertising background.
Requested concept: {user_prompt}.
The main subject MUST be {subject}.
Place the subject in the upper or right third and preserve generous clean negative space for Korean copy.
Photorealistic commercial photography, natural light, accurate materials, cohesive colors.
STRICTLY NO text, letters, words, logos, signs, labels, captions, frames or watermarks.
Do not generate an unrelated landscape or abstract object.
""".strip()
