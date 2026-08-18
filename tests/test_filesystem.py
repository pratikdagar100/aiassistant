import pytest

from app.computer import filesystem


def test_create_write_read_file(tmp_path):
    target = tmp_path / "note.txt"
    filesystem.create_file(str(target))
    assert target.exists()

    filesystem.write_file(str(target), "hello world")
    assert filesystem.read_file(str(target)) == "hello world"


def test_write_file_overwrite_false_raises(tmp_path):
    target = tmp_path / "note.txt"
    filesystem.write_file(str(target), "one")
    with pytest.raises(filesystem.FilesystemError):
        filesystem.write_file(str(target), "two", overwrite=False)


def test_list_directory(tmp_path):
    (tmp_path / "a.txt").write_text("a")
    (tmp_path / "sub").mkdir()
    entries = filesystem.list_directory(str(tmp_path))
    names = {e["name"] for e in entries}
    assert names == {"a.txt", "sub"}


def test_copy_move_rename(tmp_path):
    src = tmp_path / "src.txt"
    src.write_text("content")

    filesystem.copy(str(src), str(tmp_path / "copy.txt"))
    assert (tmp_path / "copy.txt").read_text() == "content"

    filesystem.move(str(tmp_path / "copy.txt"), str(tmp_path / "moved.txt"))
    assert (tmp_path / "moved.txt").exists()
    assert not (tmp_path / "copy.txt").exists()

    filesystem.rename(str(tmp_path / "moved.txt"), "renamed.txt")
    assert (tmp_path / "renamed.txt").exists()


def test_delete_file_and_folder(tmp_path):
    f = tmp_path / "gone.txt"
    f.write_text("x")
    filesystem.delete(str(f))
    assert not f.exists()

    d = tmp_path / "gone_dir"
    d.mkdir()
    (d / "inner.txt").write_text("x")
    filesystem.delete(str(d))
    assert not d.exists()


def test_delete_nonexistent_raises(tmp_path):
    with pytest.raises(filesystem.FilesystemError):
        filesystem.delete(str(tmp_path / "nope.txt"))


def test_archive_creates_zip(tmp_path):
    (tmp_path / "a.txt").write_text("a")
    (tmp_path / "b.txt").write_text("b")
    out = tmp_path / "out.zip"
    result = filesystem.archive([str(tmp_path / "a.txt"), str(tmp_path / "b.txt")], str(out))
    assert out.exists()
    assert result["entries"] == 2


def test_compare_identical_and_different(tmp_path):
    a = tmp_path / "a.txt"
    b = tmp_path / "b.txt"
    a.write_text("same")
    b.write_text("same")
    assert filesystem.compare(str(a), str(b))["identical"] is True

    b.write_text("different")
    assert filesystem.compare(str(a), str(b))["identical"] is False


def test_metadata_includes_hash(tmp_path):
    f = tmp_path / "f.txt"
    f.write_text("data")
    meta = filesystem.metadata(str(f))
    assert meta["size_bytes"] == 4
    assert "sha256" in meta


def test_search_finds_pattern(tmp_path):
    (tmp_path / "one.py").write_text("x")
    (tmp_path / "two.txt").write_text("x")
    results = filesystem.search(str(tmp_path), "*.py")
    assert len(results) == 1
    assert results[0].endswith("one.py")
