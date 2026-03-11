import pathlib

from unstructured.cli import main


class TestCli:
    def test_file_count(self, capsys: object) -> None:
        main(["--depth-avg", "0", "--leaf-file-avg", "5", "--node-dir-avg", "2", "file-count"])
        captured = capsys.readouterr()  # type: ignore[attr-defined]
        assert captured.out.strip() == "5"

    def test_dir_count(self, capsys: object) -> None:
        main(["--depth-avg", "1", "--leaf-file-avg", "2", "--node-dir-avg", "3", "dir-count"])
        captured = capsys.readouterr()  # type: ignore[attr-defined]
        assert captured.out.strip() == "3"

    def test_path_list(self, capsys: object) -> None:
        main(["--depth-avg", "0", "--leaf-file-avg", "3", "--node-dir-avg", "1", "path-list"])
        captured = capsys.readouterr()  # type: ignore[attr-defined]
        lines = [l for l in captured.out.strip().split("\n") if l]
        assert len(lines) == 3

    def test_apply(self, tmp_path: pathlib.Path, capsys: object) -> None:
        main([
            "--depth-avg", "1",
            "--leaf-file-avg", "2",
            "--node-dir-avg", "2",
            "--node-file-avg", "1",
            "apply", str(tmp_path / "output"),
        ])
        captured = capsys.readouterr()  # type: ignore[attr-defined]
        assert "Created" in captured.out
        assert (tmp_path / "output").exists()
