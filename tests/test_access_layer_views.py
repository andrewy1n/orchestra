from pathlib import Path

from canon_support import make_project, seed_effort
from orchestra import views


def test_derived_view_record_reference_has_id_without_file_link(tmp_path: Path) -> None:
    project = make_project(tmp_path / "repo")
    seed_effort(project, "alpha")
    records = views.load_records(project)
    goal = next(record for record in records if record["record_type"] == "score:effort")
    text = views.render_view(views.VIEWS["handoff"], records)
    assert goal["id"] in text
    assert ".canon/" not in text
    assert "](" not in next(line for line in text.splitlines() if goal["id"] in line)
