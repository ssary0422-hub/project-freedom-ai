def _subject_for(business: str, context: str) -> str:
    source = f"{business} {context}".lower()
    if any(key in source for key in ("ai 마케팅", "마케팅 콘텐츠", "광고 제작 플랫폼", "project freedom")):
        return (
            "a real small-business owner using a laptop to organize four visually distinct blank "
            "marketing content cards for advertising, social media, blog and poster work"
        )
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


ANIMAL_KEYWORDS = (
    "고양이", "cat", "kitten", "강아지", "개", "dog", "puppy",
    "코끼리", "elephant", "토끼", "rabbit", "bunny", "곰", "bear",
    "판다", "panda", "여우", "fox", "동물", "animal",
)


def _is_animal_concept(custom_concept: str) -> bool:
    lowered = (custom_concept or "").lower()
    return any(key in lowered for key in ANIMAL_KEYWORDS)


def _animal_action(business: str, context: str) -> str:
    source = f"{business} {context}".lower()
    if any(key in source for key in ("마사지", "스파", "massage", "spa")):
        return (
            "exactly two tiny baby animals in a cozy miniature spa: one stays on four paws "
            "and gently kneads the other animal's back with its front paws while the other lies "
            "happily on a small soft cushion"
        )
    if any(key in source for key in ("세차", "자동차", "car wash", "car")):
        return (
            "exactly two tiny baby animals happily washing a small toy-like car with soft foam "
            "and a little sponge in a bright miniature car wash"
        )
    if any(key in source for key in ("카페", "커피", "라테", "cafe", "coffee", "latte")):
        return (
            "one tiny baby animal sitting at a miniature cafe table, happily sipping a colorful "
            "latte from a small cup held between its front paws"
        )
    return (
        "one or two tiny baby animals clearly performing the business activity in a simple, "
        "playful miniature setting"
    )


def _creative_subject(custom_concept: str, business: str, context: str) -> str:
    concept = (custom_concept or "").strip()
    lowered = concept.lower()
    action = _animal_action(business, f"{context} {concept}")
    if any(key in lowered for key in ("고양이", "cat", "kitten")):
        return (
            f"{action}, and every character is an irresistibly cute fluffy baby kitten; "
            "the kittens remain natural four-legged animals"
        )
    if any(key in lowered for key in ("강아지", "개", "dog", "puppy")):
        return (
            f"{action}, and every character is an irresistibly cute fluffy baby puppy; "
            "the puppies remain natural four-legged animals"
        )
    if any(key in lowered for key in ("코끼리", "elephant")):
        return (
            f"{action}, and every character is an irresistibly cute round baby elephant with "
            "oversized ears and a short trunk"
        )
    if _is_animal_concept(concept):
        return (
            "irresistibly cute, friendly animal characters acting out the "
            f"business idea ({business}) in a funny and heartwarming situation; "
            "no human workers or human customers"
        )
    return (
        "a scene that literally and unmistakably expresses this user-requested "
        f"creative concept: {concept}; connected clearly to {business} and {context}"
    )


def _recommended_visual_style(business: str, context: str) -> str:
    source = f"{business} {context}".lower()
    if any(key in source for key in ("병원", "의원", "정형외과", "치과", "clinic", "hospital")):
        return "premium trustworthy healthcare editorial photography, clean navy and white palette"
    if any(key in source for key in ("카페", "커피", "베이커리", "디저트", "cafe", "coffee")):
        return "warm premium food and beverage editorial photography with refined natural light"
    if any(key in source for key in ("헬스", "피트니스", "러닝", "마라톤", "요가", "fitness", "running")):
        return "cinematic premium sports campaign photography with strong but realistic motion"
    if any(key in source for key in ("미용", "뷰티", "헤어", "네일", "스킨케어", "beauty")):
        return "elegant premium beauty campaign photography with clean soft lighting"
    if any(key in source for key in ("식당", "음식", "요리", "restaurant", "food")):
        return "appetizing premium culinary campaign photography with realistic texture"
    return "premium modern commercial editorial photography selected to fit the business and campaign"


def build_marketing_image_prompt(*, business: str, context: str, mood: str,
                                 image_style: str, placement: str,
                                 custom_concept: str = "") -> str:
    resolved_image_style = (
        _recommended_visual_style(business, context)
        if not image_style.strip() or image_style.strip() == "AI 추천"
        else image_style.strip()
    )
    subject = (
        _creative_subject(custom_concept, business, context)
        if custom_concept.strip()
        else _subject_for(business, f"{context} {mood} {image_style}")
    )
    placement_source = placement.lower()
    source = f"{business} {context}".lower()
    is_ai_marketing = any(
        key in source
        for key in ("ai 마케팅", "마케팅 콘텐츠", "광고 제작 플랫폼", "project freedom")
    )
    if is_ai_marketing and not custom_concept.strip():
        if "blog" in placement_source:
            subject = (
                "a real independent shop owner planning a practical weekly marketing calendar "
                "on a laptop inside their authentic small retail store"
            )
        elif "advertising" in placement_source or "advertisement" in placement_source:
            subject = (
                "a clean hero laptop on a small-business counter with four polished blank visual "
                "campaign cards emerging in an organized fan shape, clearly symbolizing one-click content production; no person"
            )
        else:
            subject = (
                "a close-up hand holding a modern smartphone surrounded by four vivid blank social "
                "content tiles with energetic depth and strong contrast; no visible words and no office worker"
            )
    priority = (
        f"The user's custom concept is the HIGHEST priority: {custom_concept}. "
        "Do not replace its characters or idea with a conventional business scene."
        if custom_concept.strip()
        else ""
    )
    visual_direction = (
        "ADORABLE_CHARACTER_MODE. Use a polished kawaii 3D animated advertising illustration, "
        "soft rounded baby proportions, chubby cheeks, big sparkling expressive eyes, warm pastel "
        "colors, charming smiles and clean character design. Show no more than two characters. "
        "The animals must look healthy, safe and joyful, with coherent anatomy and the correct "
        "number of limbs. They must stay animal-shaped on four paws: no upright human posture, "
        "clothing, suits, human bodies, human hands or human feet. Avoid realism, horror, distress, "
        "crowds and uncanny faces. Make it instantly lovable, cute and shareable."
        if _is_animal_concept(custom_concept)
        else "Photorealistic, high detail, commercially usable."
    )
    if "blog" in placement_source:
        channel_direction = (
            "BLOG COVER: show credible real-world business context and useful visual storytelling. "
            "Use a calm editorial composition with room for a headline."
        )
    elif "advertising" in placement_source or "advertisement" in placement_source:
        channel_direction = (
            "ADVERTISEMENT: communicate the campaign benefit in one glance with a clear hero subject, "
            "purposeful commercial lighting, a stronger problem-to-solution visual idea and clean negative "
            "space for one short headline and CTA. Do not look like a casual office stock photograph."
        )
    elif any(key in placement_source for key in ("social", "sns", "instagram")):
        channel_direction = (
            "SOCIAL FEED: create a stop-scroll square composition with one unmistakable focal action, "
            "closer framing, lively depth and strong color contrast. Avoid a passive person simply looking at a laptop."
        )
    else:
        channel_direction = "Use a clear campaign-specific hero composition with intentional copy space."
    return f"""
Create one premium commercial photograph for {placement}.
The main subject MUST be {subject}.
{priority}
Business category: {business}.
Campaign context: {context}.
Mood and campaign request: {mood}. Visual style: {resolved_image_style}.
Use believable materials, natural lighting, accurate proportions and a professional advertising composition.
Keep a clean area for copy to be added later by the website.
STRICTLY NO text, letters, words, logos, signs, labels, watermarks, captions, borders or fake writing anywhere in the image.
Do not substitute an unrelated landscape, object, food or location.
The result must look like a final premium campaign asset, not a generic stock photo or an AI demo.
{channel_direction}
{visual_direction}
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
