(() => {
    const STORAGE_KEY = "pf-content-mode";

    function setMatchingOption(select, keywords) {
        if (!select) return;
        const option = Array.from(select.options).find((item) =>
            keywords.some((keyword) => `${item.text} ${item.value}`.toLowerCase().includes(keyword))
        );
        if (option) select.value = option.value;
    }

    function inferSettings(root) {
        const request = root.querySelector('textarea[name="style"], textarea[name="topic"], #posterPurpose');
        const value = (request?.value || "").toLowerCase();
        if (!value) return;
        const platform = root.querySelector('select[name="platform"]');
        if (value.includes("인스타")) setMatchingOption(platform, ["instagram", "인스타"]);
        else if (value.includes("페이스북")) setMatchingOption(platform, ["facebook", "페이스북"]);
        else if (value.includes("틱톡")) setMatchingOption(platform, ["tiktok", "틱톡"]);
        else if (value.includes("네이버")) setMatchingOption(platform, ["naver", "네이버"]);

        const imageStyle = root.querySelector('select[name="image_style"], #posterImageStyle');
        const rules = [
            [["고양이", "강아지", "캐릭터", "귀여"], ["귀여", "character"]],
            [["따뜻", "감성"], ["따뜻", "감성"]],
            [["미니멀", "깔끔"], ["미니멀", "깔끔"]],
            [["강렬", "역동"], ["강렬", "역동"]],
            [["고급", "프리미엄"], ["고급", "프리미엄", "매거진"]],
        ];
        const matched = rules.find(([triggers]) => triggers.some((word) => value.includes(word)));
        if (matched) setMatchingOption(imageStyle, matched[1]);

        const length = root.querySelector('select[name="length"]');
        if (["짧게", "간단히", "요약"].some((word) => value.includes(word))) setMatchingOption(length, ["1000", "짧"]);
        else if (["길게", "자세히", "상세"].some((word) => value.includes(word))) setMatchingOption(length, ["3000", "길"]);
    }

    function applyMode(root, mode) {
        const normalized = mode === "direct" ? "direct" : "simple";
        root.querySelectorAll(".advanced-settings, .poster-form details").forEach((details) => { details.open = normalized === "direct"; });
        root.querySelectorAll("[data-content-mode]").forEach((button) => {
            const active = button.dataset.contentMode === normalized;
            button.classList.toggle("btn-primary", active);
            button.classList.toggle("btn-outline-primary", !active);
            button.setAttribute("aria-pressed", active ? "true" : "false");
        });
        const help = root.querySelector("[data-content-mode-help]");
        if (help) help.textContent = normalized === "direct"
            ? "적어둔 내용을 바탕으로 세부 설정을 추천했습니다. 원하는 부분만 바꾸세요."
            : "원하는 내용을 말하듯 적으면 AI가 나머지를 알아서 정합니다.";
        if (normalized === "direct") inferSettings(root);
        localStorage.setItem(STORAGE_KEY, normalized);
    }

    document.addEventListener("DOMContentLoaded", () => {
        document.querySelectorAll("[data-content-mode-switch]").forEach((switcher) => {
            const root = switcher.closest("form") || document;
            switcher.querySelectorAll("[data-content-mode]").forEach((button) => {
                button.addEventListener("click", () => applyMode(root, button.dataset.contentMode));
            });
            applyMode(root, localStorage.getItem(STORAGE_KEY) || "simple");
        });
    });
})();
