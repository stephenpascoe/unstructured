import pathlib

from click.testing import CliRunner

from unstructured.cli import main


class TestCli:
    def test_estimate(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, [
            "estimate", "--depth-avg", "1", "--leaf-file-avg", "2", "--node-dir-avg", "3",
            "--block-size", "4096", "--inode-size", "256", "--dirent-size", "256",
        ])
        assert result.exit_code == 0
        # depth=1, node_dir=3: leaf_nodes=3, non_leaf=1
        # files = 1*0 + 3*2 = 6, dirs = 3+1-1 = 3
        assert "Files:           6" in result.output
        assert "Directories:     3" in result.output
        assert "Logical storage:" in result.output

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

    def test_estimate_storage_values(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, [
            "estimate",
            "--depth-avg", "0",
            "--leaf-file-avg", "5",
            "--node-dir-avg", "2",
            "--block-size", "4096",
            "--inode-size", "256",
            "--dirent-size", "256",
        ])
        assert result.exit_code == 0
        assert "Files:           5" in result.output
        assert "Directories:     0" in result.output
        # 5 files, 0 dirs: 5*4096 + (5+0+1)*256 + (5+0)*256 = 20480 + 1536 + 1280 = 23296
        assert "Logical storage: 23296" in result.output

    def test_estimate_defaults(self) -> None:
        runner = CliRunner()
        result = runner.invoke(main, [
            "estimate",
            "--depth-avg", "0",
            "--leaf-file-avg", "1",
            "--node-dir-avg", "1",
        ])
        assert result.exit_code == 0
        assert "Files:           1" in result.output
        assert "Directories:     0" in result.output
