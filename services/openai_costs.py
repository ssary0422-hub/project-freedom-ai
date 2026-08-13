import json
import os
import time
from datetime import datetime, timezone
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


COSTS_URL = "https://api.openai.com/v1/organization/costs"

_CACHE = {
    "expires_at": 0,
    "cache_key": None,
    "value": None,
}


def _month_start_timestamp():
    now = datetime.now(timezone.utc)

    month_start = datetime(
        now.year,
        now.month,
        1,
        tzinfo=timezone.utc
    )

    return int(month_start.timestamp())


def _safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def get_openai_cost_status():
    """
    OpenAI Organization Costs API에서 이번 달 실제 API 비용을 읽습니다.

    환경변수:
      OPENAI_ADMIN_KEY       필수
      OPENAI_PROJECT_ID      선택. 설정하면 해당 프로젝트만 필터링
      OPENAI_MONTHLY_BUDGET  선택. 기본값 50 USD
    """

    admin_key = os.environ.get(
        "OPENAI_ADMIN_KEY",
        ""
    ).strip()

    project_id = os.environ.get(
        "OPENAI_PROJECT_ID",
        ""
    ).strip()

    budget = max(
        0.0,
        _safe_float(
            os.environ.get(
                "OPENAI_MONTHLY_BUDGET",
                "50"
            ),
            50.0
        )
    )

    scope_label = (
        f"프로젝트 {project_id}"
        if project_id
        else "조직 전체"
    )

    base_result = {
        "connected": False,
        "configured": bool(admin_key),
        "error": "",
        "spent": 0.0,
        "budget": budget,
        "remaining": budget,
        "percent": 0.0,
        "status": "unknown",
        "budget_exceeded": False,
        "scope_label": scope_label,
        "project_filtered": bool(project_id),
        "updated_at": "",
    }

    if not admin_key:
        base_result["error"] = (
            "OPENAI_ADMIN_KEY 환경변수가 설정되지 않았습니다."
        )
        return base_result

    cache_key = (
        project_id,
        budget,
        datetime.now(timezone.utc).strftime("%Y-%m")
    )

    now_ts = time.time()

    if (
        _CACHE["value"] is not None
        and _CACHE["cache_key"] == cache_key
        and _CACHE["expires_at"] > now_ts
    ):
        return dict(_CACHE["value"])

    total_usd = 0.0
    next_page = None

    try:
        while True:
            params = {
                "start_time": _month_start_timestamp(),
                "bucket_width": "1d",
                "limit": 31,
            }

            if project_id:
                params["project_ids"] = [project_id]

            if next_page:
                params["page"] = next_page

            query = urlencode(
                params,
                doseq=True
            )

            request = Request(
                f"{COSTS_URL}?{query}",
                headers={
                    "Authorization": f"Bearer {admin_key}",
                    "Content-Type": "application/json",
                },
                method="GET"
            )

            with urlopen(
                request,
                timeout=12
            ) as response:
                payload = json.loads(
                    response.read().decode("utf-8")
                )

            for bucket in payload.get("data", []):
                for item in bucket.get("results", []):
                    amount = item.get("amount") or {}

                    if (
                        str(
                            amount.get(
                                "currency",
                                "usd"
                            )
                        ).lower()
                        != "usd"
                    ):
                        continue

                    total_usd += _safe_float(
                        amount.get("value"),
                        0.0
                    )

            if not payload.get("has_more"):
                break

            next_page = payload.get("next_page")

            if not next_page:
                break

        remaining = max(
            0.0,
            budget - total_usd
        )

        percent = (
            min(
                100.0,
                (total_usd / budget) * 100.0
            )
            if budget > 0
            else 0.0
        )

        if budget <= 0:
            status = "unknown"
        elif total_usd >= budget:
            status = "danger"
        elif percent >= 90:
            status = "critical"
        elif percent >= 80:
            status = "warning"
        else:
            status = "normal"

        result = {
            **base_result,
            "connected": True,
            "error": "",
            "spent": round(total_usd, 4),
            "remaining": round(remaining, 4),
            "percent": round(percent, 1),
            "status": status,
            "budget_exceeded": (
                budget > 0
                and total_usd >= budget
            ),
            "updated_at": datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
        }

        _CACHE["cache_key"] = cache_key
        _CACHE["expires_at"] = (
            now_ts + 60
        )
        _CACHE["value"] = dict(result)

        return result

    except HTTPError as error:
        try:
            detail = error.read().decode(
                "utf-8",
                errors="replace"
            )
        except Exception:
            detail = ""

        base_result["error"] = (
            f"OpenAI Costs API 오류 "
            f"(HTTP {error.code}). "
            f"{detail[:300]}"
        )

    except URLError as error:
        base_result["error"] = (
            "OpenAI Costs API에 연결할 수 없습니다. "
            f"{error.reason}"
        )

    except Exception as error:
        base_result["error"] = (
            "OpenAI 비용 조회 중 오류가 발생했습니다. "
            f"{error}"
        )

    return base_result
