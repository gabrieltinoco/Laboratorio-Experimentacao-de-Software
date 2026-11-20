from dataclasses import dataclass
import random
from pathlib import Path


@dataclass(frozen=True)
class Block:
    block_id: str
    phase: str
    order: int
    engine: str
    sf: float
    workload: str
    round: int


def build_schedule(cfg: dict, phase: str) -> list[Block]:
    if phase not in {"pilot", "full"}:
        raise ValueError("phase must be pilot or full")
    repetitions = cfg["repetitions"][phase]
    blocks = []
    order = 0
    for engine in cfg["engines"]:
        for sf in cfg["scale_factors"]:
            for workload in cfg["workloads"]:
                for round_number in range(1, repetitions + 1):
                    order += 1
                    block_id = f"{phase}-{engine}-sf{sf}-{workload}-r{round_number:02d}"
                    blocks.append(
                        Block(block_id, phase, order, engine, sf, workload, round_number)
                    )
    rng = random.Random(cfg["seed"] + {"pilot": 0, "full": 1}[phase])
    rng.shuffle(blocks)
    return [
        Block(block.block_id, block.phase, index, block.engine, block.sf, block.workload, block.round)
        for index, block in enumerate(blocks)
    ]


def items_for(block: Block, cfg: dict) -> list[str]:
    if block.workload == "olap":
        items = list(cfg["workloads"]["olap"]["queries"])
    else:
        items = list(cfg["workloads"]["oltp"]["ops"])
    if block.phase == "full":
        censored = set(cfg.get("censored_queries", []))
        if censored:
            items = [item for item in items if item not in censored or block.round <= cfg["reps_censored_full"]]
    rng = random.Random(cfg["seed"] + block.order)
    rng.shuffle(items)
    return items
