import pathlib

from click.testing import CliRunner

from unstructured.cli import main


class TestCli:
    def test_file_count(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, [
            "file-count", "--depth-avg", "0", "--leaf-file-avg", "5", "--node-dir-avg", "2",
        ])
        assert result.exit_code == 0
        assert result.output.strip() == "5"

    def test_dir_count(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, [
            "dir-count", "--depth-avg", "1", "--leaf-file-avg", "2", "--node-dir-avg", "3",
        ])
        assert result.exit_code == 0
        assert result.output.strip() == "3"

    def test_path_list(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, [
            "path-list", "--depth-avg", "0", "--leaf-file-avg", "3", "--node-dir-avg", "1",
        ])
        assert result.exit_code == 0
        lines = [line for line in result.output.strip().split("\n") if line]
        assert len(lines) == 3

    def test_apply(self, tmp_path: pathlib.Path) -> None:
        runner = CliRunner()
        result = runner.invoke(main, [
            "apply",
            "--depth-avg", "1",
            "--leaf-file-avg", "2",
            "--node-dir-avg", "2",
            "--node-file-avg", "1",
            str(tmp_path / "output"),
        ])
        assert result.exit_code == 0
        assert "Created" in result.output
        assert (tmp_path / "output").exists()

    def test_estimate_storage(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, [
            "estimate-storage",
            "--depth-avg", "0",
            "--leaf-file-avg", "5",
            "--node-dir-avg", "2",
            "--block-size", "4096",
            "--inode-size", "256",
            "--dirent-size", "256",
        ])
        assert result.exit_code == 0
        # 5 files, 0 dirs: 5*4096 + (5+0+1)*256 + (5+0)*256 = 20480 + 1536 + 1280 = 23296
        assert result.output.strip() == "23296"

    def test_estimate_storage_defaults(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, [
            "estimate-storage",
            "--depth-avg", "0",
            "--leaf-file-avg", "1",
            "--node-dir-avg", "1",
        ])
        assert result.exit_code == 0
        # 1 file, 0 dirs: 1*4096 + (1+0+1)*256 + (1+0)*256 = 4096 + 512 + 256 = 4864
        assert result.output.strip() == "4864"
