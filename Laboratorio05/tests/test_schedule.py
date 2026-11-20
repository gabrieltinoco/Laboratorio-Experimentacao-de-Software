from pathlib import Path
import yaml

from bench.schedule import build_schedule, items_for
from bench.run_matrix import pending, preflight


def cfg():
    return yaml.safe_load(Path("bench/config.yaml").read_text(encoding="utf-8"))


def test_schedule_size():
    schedule = build_schedule(cfg(), "pilot")
    assert len(schedule) == 36


def test_schedule_deterministic():
    assert build_schedule(cfg(), "pilot") == build_schedule(cfg(), "pilot")


def test_pilot_full_differ():
    assert build_schedule(cfg(), "pilot") != build_schedule(cfg(), "full")


def test_block_id_format():
    assert build_schedule(cfg(), "pilot")[0].block_id.startswith("pilot-")


def test_items_shuffled_but_complete():
    block = build_schedule(cfg(), "pilot")[0]
    block_items = items_for(block, cfg())
    if block.workload == "olap":
        assert set(block_items) == set(cfg()["workloads"]["olap"]["queries"])


def test_resume_skips_done_blocks(tmp_path):
    schedule = build_schedule(cfg(), "pilot")
    (tmp_path / f"{schedule[0].block_id}.json").write_text('{"complete": true}', encoding="utf-8")
    assert schedule[0] not in pending(schedule, tmp_path)
