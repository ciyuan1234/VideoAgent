#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""重新生成剧本快照基线：python -m tests.update_snapshots"""

import os

from engine import story_planner as planner

from tests.support import SNAPSHOTS_DIR, dumps_fingerprint, list_fixtures, load_fixture, storyboard_fingerprint


def main():
    os.makedirs(SNAPSHOTS_DIR, exist_ok=True)
    for name in list_fixtures():
        fixture = load_fixture(name)
        spec = planner.build_storyboard(
            fixture["content"],
            story_profile=fixture.get("story_profile", "auto"),
            story_variant=fixture.get("story_variant", "auto"),
        )
        with open(os.path.join(SNAPSHOTS_DIR, name), "w", encoding="utf-8") as handle:
            handle.write(dumps_fingerprint(storyboard_fingerprint(spec)))
        print(f"updated {name}")


if __name__ == "__main__":
    main()
