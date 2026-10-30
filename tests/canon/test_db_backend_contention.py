from __future__ import annotations

import multiprocessing
import pytest

from test_db_backend_contract import (
    DbStore,
    _contested_worker,
    _join,
    _record,
    db_store as db_store,
)

from orchestra.canon.oplog import fold


def test_same_revision_has_one_winner_with_normalized_body(request: pytest.FixtureRequest) -> None:
    store: DbStore = request.getfixturevalue("db_store")
    first = store.backend.create_record(_record("contested"))
    context = multiprocessing.get_context("spawn")
    barrier, results = context.Barrier(2), context.Queue()
    workers = [
        context.Process(
            target=_contested_worker,
            args=(str(store.root), first, body, barrier, results),
        )
        for body in ("one", "two")
    ]
    for worker in workers:
        worker.start()
    _join(workers)
    outcomes = [results.get(timeout=5) for _ in workers]
    assert sorted(outcome[0] for outcome in outcomes) == ["ok", "stale"], outcomes
    winner = next(body for outcome, body in outcomes if outcome == "ok")
    stored = store.backend.read_record("contract:setting", first["id"])
    assert stored["body"] == winner + "\n"
    chain = dict(store.backend.iter_chains())[first["id"]]
    assert len(chain) == 2
    assert fold(chain) == stored
