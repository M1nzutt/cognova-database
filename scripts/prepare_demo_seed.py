"""Validate and adapt a data-only pg_dump from a sanitized scratch database."""

import argparse
import re
import sys
from pathlib import Path

DEMO_EMAIL = "demo.software@example.com"
DEMO_USER_INSERT = re.compile(
    r"INSERT INTO public\.users .*?VALUES "
    r"\(36, 'Lucia Torres Demo', 'demo\.software@example\.com', NULL,",
    re.DOTALL,
)
EMAIL = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE)
SECRET = re.compile(
    r"\$argon2(?:id|i|d)\$|AIza[0-9A-Za-z_-]{30,}|"
    r"\bBearer\s+[A-Za-z0-9._~-]{16,}|-----BEGIN (?:RSA )?PRIVATE KEY-----"
)
ACTIVITY_INSERT = "INSERT INTO public.activities "


def prepare(source: Path, destination: Path) -> None:
    if source.resolve() == destination.resolve():
        raise ValueError("source_and_destination_must_differ")

    lines = source.read_text(encoding="utf-8").splitlines()
    if any(
        line.startswith("\\") and not line.startswith(("\\restrict", "\\unrestrict"))
        for line in lines
    ):
        raise ValueError("unsupported_psql_meta_command")
    sql = "\n".join(
        line for line in lines if not line.startswith(("\\restrict", "\\unrestrict"))
    )

    if len(re.findall(r"INSERT INTO public\.users \(", sql)) != 1:
        raise ValueError("unexpected_user_count")
    if not DEMO_USER_INSERT.search(sql):
        raise ValueError("demo_identity_or_null_password_missing")
    if set(EMAIL.findall(sql)) != {DEMO_EMAIL}:
        raise ValueError("unexpected_email_in_seed")
    if SECRET.search(sql):
        raise ValueError("credential_or_token_pattern_in_seed")
    for table in ("auth_sessions", "academic_conversations", "academic_messages"):
        if f"INSERT INTO public.{table} " in sql:
            raise ValueError("authentication_or_chat_data_in_seed")

    activity_lines = [
        index for index, line in enumerate(lines) if line.startswith(ACTIVITY_INSERT)
    ]
    if not activity_lines:
        raise ValueError("academic_activity_rows_missing")

    # This import preserves historical deadline metadata; the normal write trigger
    # correctly forbids that metadata on new API-created activities.
    clean_lines = [
        line for line in lines if not line.startswith(("\\restrict", "\\unrestrict"))
    ]
    activity_lines = [
        index
        for index, line in enumerate(clean_lines)
        if line.startswith(ACTIVITY_INSERT)
    ]
    clean_lines.insert(
        activity_lines[0],
        "ALTER TABLE public.activities DISABLE TRIGGER activity_prepare;",
    )
    clean_lines.insert(
        activity_lines[-1] + 2,
        "ALTER TABLE public.activities ENABLE TRIGGER activity_prepare;",
    )
    while clean_lines and not clean_lines[-1].strip():
        clean_lines.pop()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("\n".join(clean_lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args(argv)
    try:
        prepare(args.source, args.destination)
    except Exception as exc:
        print(f"seed_preparation_failed reason={type(exc).__name__}", file=sys.stderr)
        return 1
    print("seed_preparation=passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
