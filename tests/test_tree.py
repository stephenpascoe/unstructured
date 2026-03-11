import pathlib
import types

import pytest

from unstructured.plan import FilesystemPlan
from unstructured.tree import FilesystemTree


class TestFilesystemTreeConstruction:
    def test_default_construction(self) -> None:
        plan = FilesystemPlan(
            depth_avg=2,
            depth_delta=0,
            leaf_file_avg=3,
            leaf_file_delta=0,
            node_file_avg=1,
            node_file_delta=0,
            node_dir_avg=2,
            node_dir_delta=0,
        )
        tree = FilesystemTree(plan)
        assert tree.plan.depth_avg == 2
        assert tree.plan.depth_delta == 0
        assert tree.plan.leaf_file_avg == 3
        assert tree.plan.leaf_file_delta == 0
        assert tree.plan.node_file_avg == 1
        assert tree.plan.node_file_delta == 0
        assert tree.plan.node_dir_avg == 2
        assert tree.plan.node_dir_delta == 0


class TestFilesystemTreeZeroDelta:
    """Tests with all delta parameters set to zero for deterministic results."""

    def test_depth_zero_file_count(self) -> None:
        """Acceptance criteria: depth_avg=0, all deltas=0 => file_count == leaf_file_avg."""
        plan = FilesystemPlan(
            depth_avg=0, leaf_file_avg=5, node_dir_avg=2,
        )
        tree = FilesystemTree(plan)
        assert tree.file_count() == 5

    def test_depth_zero_path_list_count(self) -> None:
        """Acceptance criteria: depth_avg=0 => len(list(path_list())) == leaf_file_avg."""
        plan = FilesystemPlan(
            depth_avg=0, leaf_file_avg=5, node_dir_avg=2,
        )
        tree = FilesystemTree(plan)
        paths = list(tree.path_list())
        assert len(paths) == 5

    def test_depth_zero_dir_count(self) -> None:
        """depth_avg=0 means the root is a leaf, so no subdirectories."""
        plan = FilesystemPlan(
            depth_avg=0, leaf_file_avg=3, node_dir_avg=2,
        )
        tree = FilesystemTree(plan)
        assert tree.dir_count() == 0

    def test_depth_one_structure(self) -> None:
        """depth_avg=1, node_dir_avg=2: root has 2 subdirs, each is a leaf."""
        plan = FilesystemPlan(
            depth_avg=1, leaf_file_avg=3, node_file_avg=1, node_dir_avg=2,
        )
        tree = FilesystemTree(plan)
        # 2 subdirs
        assert tree.dir_count() == 2
        # 1 file in root (node) + 3 files in each of 2 leaf dirs = 7
        assert tree.file_count() == 7

    def test_depth_two_structure(self) -> None:
        """depth_avg=2, node_dir_avg=2: root->2 dirs->each has 2 leaf dirs."""
        plan = FilesystemPlan(
            depth_avg=2, leaf_file_avg=3, node_file_avg=1, node_dir_avg=2,
        )
        tree = FilesystemTree(plan)
        # root has 2 subdirs, each has 2 leaf subdirs = 2 + 4 = 6
        assert tree.dir_count() == 6
        # root: 1 file, 2 node dirs: 1 file each, 4 leaf dirs: 3 files each = 1 + 2 + 12 = 15
        assert tree.file_count() == 15


class TestPathList:
    def test_returns_generator(self) -> None:
        plan = FilesystemPlan(
            depth_avg=0, leaf_file_avg=2, node_dir_avg=1,
        )
        tree = FilesystemTree(plan)
        result = tree.path_list()
        assert isinstance(result, types.GeneratorType)

    def test_path_list_includes_dirs_and_files(self) -> None:
        plan = FilesystemPlan(
            depth_avg=1, leaf_file_avg=2, node_file_avg=1, node_dir_avg=2,
        )
        tree = FilesystemTree(plan)
        paths = list(tree.path_list())
        # 2 dirs + 1 node file + 2*2 leaf files = 7
        assert len(paths) == 2 + 1 + 4


class TestNamingConvention:
    def test_file_names(self) -> None:
        plan = FilesystemPlan(
            depth_avg=0, leaf_file_avg=3, node_dir_avg=1,
        )
        tree = FilesystemTree(plan)
        paths = list(tree.path_list())
        for p in paths:
            name = pathlib.PurePosixPath(p).name
            assert name.startswith("file_")
            assert len(name) == len("file_") + 6

    def test_dir_names(self) -> None:
        plan = FilesystemPlan(
            depth_avg=1, leaf_file_avg=1, node_dir_avg=2,
        )
        tree = FilesystemTree(plan)
        paths = list(tree.path_list())
        dirs = [p for p in paths if pathlib.PurePosixPath(p).name.startswith("dir_")]
        assert len(dirs) == 2
        for d in dirs:
            name = pathlib.PurePosixPath(d).name
            assert len(name) == len("dir_") + 6


class TestApply:
    def test_apply_creates_files(self, tmp_path: pathlib.Path) -> None:
        plan = FilesystemPlan(
            depth_avg=0, leaf_file_avg=3, node_dir_avg=1,
        )
        tree = FilesystemTree(plan)
        tree.apply(tmp_path)
        created_files = list(tmp_path.rglob("file_*"))
        assert len(created_files) == 3

    def test_apply_creates_dirs(self, tmp_path: pathlib.Path) -> None:
        plan = FilesystemPlan(
            depth_avg=1, leaf_file_avg=1, node_dir_avg=2,
        )
        tree = FilesystemTree(plan)
        tree.apply(tmp_path)
        created_dirs = [d for d in tmp_path.rglob("dir_*") if d.is_dir()]
        assert len(created_dirs) == 2

    def test_apply_file_content(self, tmp_path: pathlib.Path) -> None:
        plan = FilesystemPlan(
            depth_avg=0, leaf_file_avg=2, node_dir_avg=1,
        )
        tree = FilesystemTree(plan)
        tree.apply(tmp_path)
        for f in tmp_path.rglob("file_*"):
            content = f.read_text()
            assert content == f"This is a test file {f.name}"

    def test_apply_depth_one(self, tmp_path: pathlib.Path) -> None:
        plan = FilesystemPlan(
            depth_avg=1, leaf_file_avg=2, node_file_avg=1, node_dir_avg=2,
        )
        tree = FilesystemTree(plan)
        tree.apply(tmp_path)
        all_files = list(tmp_path.rglob("file_*"))
        all_dirs = [d for d in tmp_path.rglob("dir_*") if d.is_dir()]
        assert len(all_files) == 5  # 1 node + 2*2 leaf
        assert len(all_dirs) == 2


class TestRandomVariation:
    def test_depth_delta_varies_depth(self) -> None:
        """With non-zero delta, different subtrees may have different depths."""
        plan = FilesystemPlan(
            depth_avg=3, depth_delta=2, leaf_file_avg=1, node_dir_avg=2,
        )
        tree = FilesystemTree(plan)
        # Just verify it produces a valid tree without errors
        count = tree.file_count()
        assert count > 0

    def test_leaf_file_delta(self) -> None:
        plan = FilesystemPlan(
            depth_avg=0, leaf_file_avg=5, leaf_file_delta=2, node_dir_avg=1,
        )
        tree = FilesystemTree(plan)
        count = tree.file_count()
        assert 3 <= count <= 7

    def test_counts_non_negative(self) -> None:
        """Even with large deltas, counts should never be negative."""
        plan = FilesystemPlan(
            depth_avg=1, depth_delta=1, leaf_file_avg=1, leaf_file_delta=1,
            node_file_avg=1, node_file_delta=1, node_dir_avg=1, node_dir_delta=1,
        )
        tree = FilesystemTree(plan)
        assert tree.file_count() >= 0
        assert tree.dir_count() >= 0
