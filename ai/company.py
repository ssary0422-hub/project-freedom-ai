from concurrent.futures import ThreadPoolExecutor, as_completed

from ai.providers import generate_text


DEPARTMENTS = {
    "planning": {
        "name": "기획·전략팀",
        "icon": "🧭",
        "keywords": ("기획", "전략", "사업", "아이디어", "분석", "계획", "조사"),
        "mission": "목표를 실행 단계로 나누고 우선순위, 위험, 성공 기준을 정한다.",
    },
    "development": {
        "name": "개발팀",
        "icon": "💻",
        "keywords": ("개발", "코드", "기능", "버그", "오류", "웹", "앱", "자동화"),
        "mission": "구현 방법, 기술 작업, 테스트와 운영 위험을 구체화한다.",
    },
    "marketing": {
        "name": "마케팅팀",
        "icon": "📣",
        "keywords": ("마케팅", "광고", "홍보", "sns", "블로그", "고객", "판매", "콘텐츠"),
        "mission": "고객, 메시지, 채널, 실행 콘텐츠와 측정 지표를 제안한다.",
    },
    "design": {
        "name": "디자인팀",
        "icon": "🎨",
        "keywords": ("디자인", "이미지", "포스터", "로고", "화면", "ui", "사진", "브랜드"),
        "mission": "시각 방향, 정보 구조, 필요한 제작물과 품질 기준을 제안한다.",
    },
}


def assign_departments(objective):
    """Route work predictably so the user can understand why each team joined."""
    normalized = (objective or "").lower()
    selected = [
        key for key, department in DEPARTMENTS.items()
        if any(keyword in normalized for keyword in department["keywords"])
    ]
    if not selected:
        selected = ["planning", "marketing"]
    elif "planning" not in selected:
        selected.insert(0, "planning")
    return selected[:3]


def _department_prompt(department_key, objective, context):
    department = DEPARTMENTS[department_key]
    return f"""
당신은 Project Freedom AI의 {department['name']} 담당자입니다.
대표가 지시한 업무: {objective}
추가 배경: {context or '없음'}
담당 임무: {department['mission']}

다른 부서의 일을 대신하지 말고 담당 분야에서 다음 형식으로 한국어 보고서를 작성하세요.
1. 판단
2. 구체적인 실행안
3. 필요한 결과물
4. 위험과 확인할 사항
외부 게시, 결제, 삭제, 고객 연락은 실행하지 말고 반드시 승인 대상으로 표시하세요.
""".strip()


def run_company_task(objective, context="", generator=None):
    generator = generator or generate_text
    department_keys = assign_departments(objective)
    reports = {}

    with ThreadPoolExecutor(max_workers=len(department_keys)) as executor:
        futures = {
            executor.submit(
                generator,
                _department_prompt(key, objective, context),
            ): key
            for key in department_keys
        }
        for future in as_completed(futures):
            key = futures[future]
            try:
                reports[key] = future.result().strip()
            except Exception as exc:
                reports[key] = f"부서 작업 실패: {exc}"

    successful = {
        key: report for key, report in reports.items()
        if not report.startswith("부서 작업 실패:")
    }
    if not successful:
        raise RuntimeError("배정된 모든 AI 부서의 작업이 실패했습니다.")

    joined_reports = "\n\n".join(
        f"[{DEPARTMENTS[key]['name']}]\n{reports[key]}"
        for key in department_keys
    )
    summary_prompt = f"""
당신은 Project Freedom AI의 총괄실장 '순금이'입니다.
대표의 업무: {objective}
추가 배경: {context or '없음'}

아래 부서 보고를 중복 없이 하나의 실행 보고서로 통합하세요.
{joined_reports}

한국어로 다음 항목을 포함하세요.
- 총괄 결론
- 지금 실행할 일(우선순위 순)
- 대표의 승인이 필요한 일
- 완료 기준
부서 보고에 없는 사실을 확정적으로 만들지 마세요.
""".strip()
    executive_summary = generator(summary_prompt).strip()

    return {
        "departments": [
            {
                "key": key,
                "name": DEPARTMENTS[key]["name"],
                "icon": DEPARTMENTS[key]["icon"],
                "report": reports[key],
            }
            for key in department_keys
        ],
        "executive_summary": executive_summary,
    }
