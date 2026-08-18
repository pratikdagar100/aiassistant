"""peft/transformers/bitsandbytes are intentionally NOT installed by
default (see requirements.txt) — these tests verify the module reports that
honestly instead of crashing or pretending it's ready."""

from app.learning.lora_trainer import TrainingConfig, dry_run, is_environment_ready


def test_environment_reports_missing_packages_honestly():
    status = is_environment_ready()
    assert isinstance(status["missing_packages"], list)
    # In this project's default environment these are NOT installed —
    # if this assertion ever fails it means someone installed them, which
    # is fine, but the "ready" flag must then also flip to True.
    if status["missing_packages"]:
        assert status["ready"] is False
        assert status["install_hint"] is not None
    else:
        assert status["ready"] is True


def test_dry_run_reports_missing_dataset_path():
    config = TrainingConfig(dataset_path="")
    result = dry_run(config)
    assert result["can_run"] is False
    assert result["dataset"]["valid"] is False


def test_dry_run_validates_real_dataset(tmp_path):
    ds_path = tmp_path / "ds.jsonl"
    ds_path.write_text('{"input": "a", "output": "b", "category": "correction"}\n', encoding="utf-8")

    config = TrainingConfig(dataset_path=str(ds_path))
    result = dry_run(config)
    assert result["dataset"]["example_count"] == 1
    # can_run also depends on environment readiness, which we don't control here —
    # what matters is the dataset side of the report is accurate.
    assert "issues" in result["dataset"]


def test_validate_dataset_flags_missing_fields(tmp_path):
    ds_path = tmp_path / "bad.jsonl"
    ds_path.write_text('{"input": "a"}\n', encoding="utf-8")

    from app.learning.lora_trainer import validate_dataset

    report = validate_dataset(str(ds_path), min_examples=1)
    assert report["valid"] is False
    assert any("missing" in issue for issue in report["issues"])
