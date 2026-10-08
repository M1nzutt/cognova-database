"""Fail CI if the integration suite was absent, skipped, or failed."""

import sys
from xml.etree import ElementTree


def main() -> int:
    root = ElementTree.parse(sys.argv[1]).getroot()
    cases = list(root.iter("testcase"))
    integration = [c for c in cases if ".integration." in c.get("classname", "")]
    if not integration or any(
        c.find(tag) is not None
        for c in cases
        for tag in ("skipped", "failure", "error")
    ):
        print("CI requires successful, unskipped PostgreSQL integration tests")
        return 1
    print(f"Verified {len(cases)} tests including {len(integration)} PostgreSQL cases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
