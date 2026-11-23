from tests import test_layout_conductor_landing_tasks as landing_tasks
from tests import test_layout_conductor_phases as phases
from tests import test_layout_conductor_verification as verification
from tests import test_layout_score as score
from tests import test_layout_tuner as tuner
from tests.layout_support import ROOT, moved_old_paths, old_path_imports, old_path_leftovers

MOVED = moved_old_paths(
    {
        "score": [score.SCORE],
        "tuner": [tuner.TUNER],
        "conductor": [
            verification.VERIFICATION,
            landing_tasks.SLICE,
            phases.SLICE,
        ],
    }
)


def test_old_path_moved_modules_leave_no_file_at_their_old_path():
    assert old_path_leftovers(ROOT, MOVED) == []


def test_old_path_imports_do_not_appear_anywhere_in_the_repository():
    assert old_path_imports(ROOT, MOVED) == []


def test_old_path_scan_flags_a_re_export_and_an_old_import_in_a_seeded_tree(tmp_path):
    (tmp_path / "orchestra" / "score").mkdir(parents=True)
    (tmp_path / "orchestra" / "score" / "phase.py").write_text(
        "from orchestra.score.planning.phase import *\n"
    )
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_a.py").write_text("import orchestra.score.phase\n")
    (tmp_path / "tests" / "test_b.py").write_text("from orchestra.score import phase, acceptance\n")
    (tmp_path / "tests" / "test_c.py").write_text("from orchestra.score.planning import phase\n")
    moved = {"score": ["phase"]}
    assert old_path_leftovers(tmp_path, moved) == ["orchestra/score/phase.py"]
    assert old_path_imports(tmp_path, moved) == [
        "tests/test_a.py:1: orchestra.score.phase",
        "tests/test_b.py:1: orchestra.score.phase",
    ]


def test_old_path_scan_skips_worktree_directories(tmp_path):
    hidden = tmp_path / ".worktrees" / "other" / "tests"
    hidden.mkdir(parents=True)
    (hidden / "test_a.py").write_text("import orchestra.score.phase\n")
    assert old_path_imports(tmp_path, {"score": ["phase"]}) == []


def test_composer_holds_only_its_flat_modules():
    root = ROOT / "orchestra" / "composer"
    entries = {path.stem for path in root.iterdir() if path.name != "__pycache__"}
    assert entries == {
        "__init__",
        "cli",
        "idea",
        "idea_facts",
        "idea_source",
        "placement",
        "records",
        "schemas",
    }
