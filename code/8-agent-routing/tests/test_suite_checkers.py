import routing_lab_answers_import_helper  # noqa: F401  (see the helper's docstring)
from routing_lab_answers_import_helper import answers as lab

def test_load_tasks_shape():
    tasks = lab.load_tasks()
    assert len(tasks) == 12
    assert {t["kind"] for t in tasks} == {"commodity", "frontier"}

def test_contains_checker():
    t = {"check": {"type": "contains", "value": "1969"}}
    assert lab.check_task(t, "It was 1969.") is True
    assert lab.check_task(t, "no idea") is False

def test_contains_all_checker():
    t = {"check": {"type": "contains_all", "value": ["Ada", "platform"]}}
    assert lab.check_task(t, '{"name":"Ada","team":"platform"}') is True
    assert lab.check_task(t, "Ada only") is False

def test_judge_checker_uses_injected_judge():
    t = {"check": {"type": "judge", "value": "rubric text"}}
    assert lab.check_task(t, "three bullets...", judge=lambda rubric, out: True) is True
