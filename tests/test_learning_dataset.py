from app.db.database import session_scope
from app.db.models import TrainingExample
from app.entities import manager as entity_manager
from app.learning import dataset


def _make_entity(entity_id: str):
    with session_scope() as db:
        entity_manager.create_entity(db, id=entity_id, name=entity_id.title())


def test_build_dataset_only_includes_approved():
    _make_entity("test-ds-a")
    with session_scope() as db:
        db.add(TrainingExample(entity_id="test-ds-a", input_text="i1", output_text="o1", status="approved"))
        db.add(TrainingExample(entity_id="test-ds-a", input_text="i2", output_text="o2", status="pending"))
        db.add(TrainingExample(entity_id="test-ds-a", input_text="i3", output_text="o3", status="rejected"))

    with session_scope() as db:
        rows = dataset.build_dataset(db, "test-ds-a")

    assert len(rows) == 1
    assert rows[0]["input"] == "i1"


def test_export_dataset_writes_jsonl(tmp_path):
    _make_entity("test-ds-b")
    with session_scope() as db:
        db.add(TrainingExample(entity_id="test-ds-b", input_text="i1", output_text="o1", status="approved"))

    with session_scope() as db:
        result = dataset.export_dataset_jsonl(db, "test-ds-b")

    assert result["example_count"] == 1
    rows = dataset.load_dataset_jsonl(result["path"])
    assert rows[0]["input"] == "i1"


def test_export_dataset_raises_when_insufficient_examples():
    _make_entity("test-ds-c")
    import pytest

    with pytest.raises(dataset.DatasetError):
        with session_scope() as db:
            dataset.export_dataset_jsonl(db, "test-ds-c", min_examples=5)
