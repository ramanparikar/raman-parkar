#!/usr/bin/env python3
"""Fail-closed validator for scripture edition rights register metadata."""
from __future__ import annotations
import argparse
import csv
import re
import sys
from datetime import date, datetime
from pathlib import Path

REQUIRED = {
    "rights_holder", "work_code", "edition_code", "content_type", "rights_state",
    "public_display_allowed", "search_indexing_allowed", "embeddings_allowed",
    "ai_retrieval_allowed", "redistribution_allowed", "permission_reference",
    "evidence_source_title", "evidence_source_url", "permitted_languages",
    "starts_on", "expires_on", "reviewed_by", "reviewed_at",
}
STATES = {"unknown", "public_domain_confirmed", "permission_pending", "licensed_for_use", "restricted", "not_cleared"}
BOOLS = {"true", "false", "yes", "no", "1", "0"}
ACTIONS = {
    "public_display": "public_display_allowed",
    "search_indexing": "search_indexing_allowed",
    "embeddings": "embeddings_allowed",
    "ai_retrieval": "ai_retrieval_allowed",
    "redistribution": "redistribution_allowed",
}

def validate(path: Path) -> list[str]:
    errors = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = REQUIRED - set(reader.fieldnames or [])
        if missing:
            return ["Missing required columns: " + ", ".join(sorted(missing))]
        count = 0
        seen = set()
        for line, raw in enumerate(reader, 2):
            count += 1
            row = {k: (v or "").strip() for k, v in raw.items()}
            key = (row["work_code"], row["edition_code"], row["content_type"], row["rights_holder"])
            if key in seen:
                errors.append(f"Line {line}: duplicate rights register record {key}")
            seen.add(key)
            if row["work_code"] not in {"BG", "SB", "CC"}:
                errors.append(f"Line {line}: unsupported work_code {row['work_code']!r}")
            if not row["edition_code"] or not row["content_type"] or not row["rights_holder"]:
                errors.append(f"Line {line}: edition_code, content_type and rights_holder are required")
            state = row["rights_state"]
            if state not in STATES:
                errors.append(f"Line {line}: invalid rights_state {state!r}")
            flags = {}
            for action, field in ACTIONS.items():
                value = row[field].lower()
                if value not in BOOLS:
                    errors.append(f"Line {line}: {field} must be an explicit true/false value")
                flags[action] = value in {"true", "yes", "1"}
            for field in ("starts_on", "expires_on"):
                if row[field]:
                    try:
                        date.fromisoformat(row[field])
                    except ValueError:
                        errors.append(f"Line {line}: {field} must use YYYY-MM-DD")
            if row["starts_on"] and row["expires_on"]:
                try:
                    if date.fromisoformat(row["expires_on"]) < date.fromisoformat(row["starts_on"]):
                        errors.append(f"Line {line}: expires_on precedes starts_on")
                except ValueError:
                    pass
            if row["reviewed_at"]:
                try:
                    datetime.fromisoformat(row["reviewed_at"].replace("Z", "+00:00"))
                except ValueError:
                    errors.append(f"Line {line}: reviewed_at must be an ISO-8601 timestamp")
            evidence = bool(row["evidence_source_title"] and row["evidence_source_url"].startswith("https://"))
            if state == "licensed_for_use":
                for field in ("permission_reference", "reviewed_by", "reviewed_at"):
                    if not row[field]:
                        errors.append(f"Line {line}: licensed_for_use requires {field}")
                if not evidence:
                    errors.append(f"Line {line}: licensed_for_use requires HTTPS evidence source title and URL")
                if not row["permitted_languages"]:
                    errors.append(f"Line {line}: licensed_for_use requires explicit permitted_languages")
            if state == "public_domain_confirmed":
                if not evidence:
                    errors.append(f"Line {line}: public_domain_confirmed requires documented HTTPS evidence")
                if not row["reviewed_by"] or not row["reviewed_at"]:
                    errors.append(f"Line {line}: public_domain_confirmed requires reviewer and timestamp")
            if state != "licensed_for_use" and any(flags.values()):
                errors.append(f"Line {line}: usage flags must remain false unless rights_state is licensed_for_use")
            if state in {"unknown", "permission_pending", "restricted", "not_cleared"} and any(flags.values()):
                errors.append(f"Line {line}: uncleared rights cannot grant usage permissions")
        if count == 0:
            errors.append("Rights register has a header but no records")
    return errors

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_file", type=Path)
    args = parser.parse_args()
    errors = validate(args.csv_file)
    if errors:
        print("RIGHTS REGISTER VALIDATION FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    print("RIGHTS REGISTER VALIDATION PASSED")
    print("Metadata structure only; legal authority and licence scope still require human review.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
