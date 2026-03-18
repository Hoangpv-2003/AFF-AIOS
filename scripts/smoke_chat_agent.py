from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import create_app


def main() -> None:
    client = TestClient(create_app())

    case1 = client.post(
        "/api/v1/agents/chat",
        json={"message": "Tao report gia vang va tao hinh anh tom tat"},
    )
    data1 = case1.json()
    print(
        "case1",
        case1.status_code,
        bool((data1.get("artifacts") or {}).get("report_markdown")),
        bool((data1.get("artifacts") or {}).get("image_base64")),
        bool(
            ((data1.get("artifacts") or {}).get("report_files") or {})
            .get("html_url")
        ),
    )

    case2 = client.post(
        "/api/v1/agents/chat",
        json={
            "message": "Len lich nhac toi hop voi team",
            "schedule_time": "2026-03-20T09:00:00+07:00",
        },
    )
    data2 = case2.json()
    print(
        "case2",
        case2.status_code,
        ((data2.get("artifacts") or {}).get("schedule") or {}).get(
            "provider"
        ),
    )

    case3 = client.post(
        "/api/v1/agents/chat",
        json={
            "message": "Gui email bao cao cho toi",
            "user_email": "onboarding@resend.dev",
        },
    )
    data3 = case3.json()
    print(
        "case3",
        case3.status_code,
        ((data3.get("artifacts") or {}).get("email") or {}).get("sent"),
    )

    files = {
        "file": (
            "sample.csv",
            "date,revenue\n2026-03-01,100\n2026-03-08,120\n",
            "text/csv",
        )
    }
    case4 = client.post(
        "/api/v1/agents/chat/upload",
        data={
            "message": "Tao report tu file nay va tom tat doanh thu",
            "force_new": "false",
        },
        files=files,
    )
    data4 = case4.json()
    print(
        "case4",
        case4.status_code,
        bool(data4.get("uploaded_file")),
    )


if __name__ == "__main__":
    main()
