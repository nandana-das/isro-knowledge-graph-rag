"""Create a deterministic benchmark split for model development and final evaluation."""

from __future__ import annotations

import json
import random
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BENCHMARK_PATH = ROOT / "data" / "benchmark" / "isro_qa.json"
DEV_PATH = ROOT / "data" / "benchmark" / "dev_ids.json"
TEST_PATH = ROOT / "data" / "benchmark" / "test_ids.json"

DEV_PER_TIER = {1: 10, 2: 6, 3: 4}
SEED = 42


def build_split(benchmark: list[dict]) -> tuple[list[str], list[str]]:
    by_tier: dict[int, list[dict]] = defaultdict(list)
    for item in benchmark:
        by_tier[int(item.get("tier", 1))].append(item)

    dev_ids: list[str] = []
    test_ids: list[str] = []
    for tier in sorted(by_tier):
        rng = random.Random(SEED + tier)
        tier_items = by_tier[tier][:]
        rng.shuffle(tier_items)
        dev_count = DEV_PER_TIER.get(tier, 0)
        dev_ids.extend(item["id"] for item in tier_items[:dev_count])
        test_ids.extend(item["id"] for item in tier_items[dev_count:])

    dev_ids = sorted(dev_ids)
    test_ids = sorted(test_ids)
    if len(test_ids) != 180:
        raise ValueError(f"Expected 180 test IDs, found {len(test_ids)}")
    return dev_ids, test_ids


def main() -> None:
    benchmark = json.loads(BENCHMARK_PATH.read_text(encoding="utf-8-sig"))
    dev_ids, test_ids = build_split(benchmark)
    DEV_PATH.write_text(json.dumps(dev_ids, indent=2), encoding="utf-8")
    TEST_PATH.write_text(json.dumps(test_ids, indent=2), encoding="utf-8")
    print(f"Development IDs: {len(dev_ids)}")
    print(f"Test IDs: {len(test_ids)}")
    print("Saved to", DEV_PATH)
    print("Saved to", TEST_PATH)


if __name__ == "__main__":
    main()
