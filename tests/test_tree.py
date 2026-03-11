import dataclasses
import pathlib
import types

import pytest

from unstructured.tree import FilesystemPlan, FilesystemTree


def make_plan(**overrides) -> FilesystemPlan:
    defaults = dict(
        depth_avg=2,
        depth_delta=0,
        leaf_file_avg=3,
        leaf_file_delta=0,
        node_file_avg=1,
        node_file_delta=0,
        node_dir_avg=2,
        node_dir_delta=0,
    )
    defaults.update(overrides)
    return FilesystemPlan(**defaults)


class TestFilesystemPlan:
    def test_is_dataclass(self) -> None:
        assert dataclasses.is_dataclass(FilesystemPlan)

    def test_construction(self) -> None:
        plan = make_plan()
        assert plan.depth_avg == 2
        assert plan.depth_delta == 0
        assert plan.leaf_file_avg == 3
        assert plan.leaf_file_delta == 0
        assert plan.node_file_avg == 1
        assert plan.node_file_delta == 0
        assert plan.node_dir_avg == 2
        assert plan.node_dir_delta == 0

    def test_estimate_logical_storage_depth_zero(self) -> None:
        # depth_avg=0 => 1 leaf node with 5 files, 0 dirs
        plan = make_plan(
            depth_avg=0,
            leaf_file_avg=5,
            node_file_avg=0,
            node_dir_avg=2,
        )
        block_size = 4096
        inode_size = 256
        dirent_size = 64
        # 5 files, 0 dirs
        # storage = 5*block_size + (5+0)*inode_size + (5+0)*dirent_size
        expected = 5 * block_size + 5 * inode_size + 5 * dirent_size
        assert plan.estimate_logical_storage(block_size, inode_size, dirent_size) == expected

    def test_estimate_logical_storage_depth_one(self) -> None:
        # depth_avg=1, node_dir_avg=2, node_file_avg=1, leaf_file_avg=3
        # dirs = 2, files = 1 (root node) + 2*3 (leaves) = 7
        plan = make_plan(
            depth_avg=1,
            leaf_file_avg=3,
            node_file_avg=1,
            node_dir_avg=2,
        )
        block_size = 4096
        inode_size = 256
        dirent_size = 64
        expected = 7 * block_size + (7 + 2) * inode_size + (7 + 2) * dirent_size
        assert plan.estimate_logical_storage(block_size, inode_size, dirent_size) == expected

    def test_estimate_logical_storage_depth_two(self) -> None:
        # depth_avg=2, node_dir_avg=2, node_file_avg=1, leaf_file_avg=3
        # dirs = 2 + 4 = 6, files = 1 + 2 + 4*3 = 15
        plan = make_plan(
            depth_avg=2,
            leaf_file_avg=3,
            node_file_avg=1,
            node_dir_avg=2,
        )
        block_size = 4096
        inode_size = 256
        dirent_size = 64
        expected = 15 * block_size + (15 + 6) * inode_size + (15 + 6) * dirent_size
        assert plan.estimate_logical_storage(block_size, inode_size, dirent_size) == expected

    def test_estimate_logical_storage_no_node_files(self) -> None:
        # depth_avg=1, node_dir_avg=3, node_file_avg=0, leaf_file_avg=2
        # dirs=3, files=3*2=6
        plan = make_plan(
            depth_avg=1,
            leaf_file_avg=2,
            node_file_avg=0,
            node_dir_avg=3,
        )
        block_size = 512
        inode_size = 128
        dirent_size = 32
        expected = 6 * block_size + (6 + 3) * inode_size + (6 + 3) * dirent_size
        assert plan.estimate_logical_storage(block_size, inode_size, dirent_size) == expected


class TestFilesystemTreeConstruction:
    def test_construction_with_plan(self) -> None:
        plan = make_plan()
        tree = FilesystemTree(plan)
        assert tree is not None

    def test_plan_attribute(self) -> None:
        plan = make_plan()
        tree = FilesystemTree(plan)
        assert tree.plan is plan


class TestFilesystemTreeZeroDelta:
    """Tests with all delta parameters set to zero for deterministic results."""

    def test_depth_zero_file_count(self) -> None:
        """Acceptance criteria: depth_avg=0, all deltas=0 => file_count == leaf_file_avg."""
        tree = FilesystemTree(make_plan(
            depth_avg=0,
            leaf_file_avg=5,
            node_file_avg=0,
            node_dir_avg=2,
        ))
        assert tree.file_count() == 5

    def test_depth_zero_path_list_count(self) -> None:
        """Acceptance criteria: depth_avg=0 => len(list(path_list())) == leaf_file_avg."""
        tree = FilesystemTree(make_plan(
            depth_avg=0,
            leaf_file_avg=5,
            node_file_avg=0,
            node_dir_avg=2,
        ))
        paths = list(tree.path_list())
        assert len(paths) == 5

    def test_depth_zero_dir_count(self) -> None:
        """depth_avg=0 means the root is a leaf, so no subdirectories."""
        tree = FilesystemTree(make_plan(
            depth_avg=0,
            leaf_file_avg=3,
            node_file_avg=0,
            node_dir_avg=2,
        ))
        assert tree.dir_count() == 0

    def test_depth_one_structure(self) -> None:
        """depth_avg=1, node_dir_avg=2: root has 2 subdirs, each is a leaf."""
        tree = FilesystemTree(make_plan(
            depth_avg=1,
            leaf_file_avg=3,
            node_file_avg=1,
            node_dir_avg=2,
        ))
        assert tree.dir_count() == 2
        assert tree.file_count() == 7

    def test_depth_two_structure(self) -> None:
        """depth_avg=2, node_dir_avg=2: root->2 dirs->each has 2 leaf dirs."""
        tree = FilesystemTree(make_plan(
            depth_avg=2,
            leaf_file_avg=3,
            node_file_avg=1,
            node_dir_avg=2,
        ))
        assert tree.dir_count() == 6
        assert tree.file_count() == 15


class TestPathList:
    def test_returns_generator(self) -> None:
        tree = FilesystemTree(make_plan(
            depth_avg=0,
            leaf_file_avg=2,
            node_file_avg=0,
            node_dir_avg=1,
        ))
        result = tree.path_list()
        assert isinstance(result, types.GeneratorType)

    def test_path_list_includes_dirs_and_files(self) -> None:
        tree = FilesystemTree(make_plan(
            depth_avg=1,
            leaf_file_avg=2,
            node_file_avg=1,
            node_dir_avg=2,
        ))
        paths = list(tree.path_list())
        assert len(paths) == 2 + 1 + 4


class TestNamingConvention:
    def test_file_names(self) -> None:
        tree = FilesystemTree(make_plan(
            depth_avg=0,
            leaf_file_avg=3,
            node_file_avg=0,
            node_dir_avg=1,
        ))
        paths = list(tree.path_list())
        for p in paths:
            name = pathlib.PurePosixPath(p).name
            assert name.startswith("file_")
            assert len(name) == len("file_") + 6

    def test_dir_names(self) -> None:
        tree = FilesystemTree(make_plan(
            depth_avg=1,
            leaf_file_avg=1,
            node_file_avg=0,
            node_dir_avg=2,
        ))
        paths = list(tree.path_list())
        dirs = [p for p in paths if pathlib.PurePosixPath(p).name.startswith("dir_")]
        assert len(dirs) == 2
        for d in dirs:
            name = pathlib.PurePosixPath(d).name
            assert len(name) == len("dir_") + 6


class TestApply:
    def test_apply_creates_files(self, tmp_path: pathlib.Path) -> None:
        tree = FilesystemTree(make_plan(
            depth_avg=0,
            leaf_file_avg=3,
            node_file_avg=0,
            node_dir_avg=1,
        ))
        tree.apply(tmp_path)
        created_files = list(tmp_path.rglob("file_*"))
        assert len(created_files) == 3

    def test_apply_creates_dirs(self, tmp_path: pathlib.Path) -> None:
        tree = FilesystemTree(make_plan(
            depth_avg=1,
            leaf_file_avg=1,
            node_file_avg=0,
            node_dir_avg=2,
        ))
        tree.apply(tmp_path)
        created_dirs = [d for d in tmp_path.rglob("dir_*") if d.is_dir()]
        assert len(created_dirs) == 2

    def test_apply_file_content(self, tmp_path: pathlib.Path) -> None:
        tree = FilesystemTree(make_plan(
            depth_avg=0,
            leaf_file_avg=2,
            node_file_avg=0,
            node_dir_avg=1,
        ))
        tree.apply(tmp_path)
        for f in tmp_path.rglob("file_*"):
            content = f.read_text()
            assert content == f"This is a test file {f.name}"

    def test_apply_depth_one(self, tmp_path: pathlib.Path) -> None:
        tree = FilesystemTree(make_plan(
            depth_avg=1,
            leaf_file_avg=2,
            node_file_avg=1,
            node_dir_avg=2,
        ))
        tree.apply(tmp_path)
        all_files = list(tmp_path.rglob("file_*"))
        all_dirs = [d for d in tmp_path.rglob("dir_*") if d.is_dir()]
        assert len(all_files) == 5
        assert len(all_dirs) == 2


class TestRandomVariation:
    def test_depth_delta_varies_depth(self) -> None:
        """With non-zero delta, different subtrees may have different depths."""
        tree = FilesystemTree(make_plan(
            depth_avg=3,
            depth_delta=2,
            leaf_file_avg=1,
            node_file_avg=0,
            node_dir_avg=2,
        ))
        count = tree.file_count()
        assert count > 0

    def test_leaf_file_delta(self) -> None:
        tree = FilesystemTree(make_plan(
            depth_avg=0,
            leaf_file_avg=5,
            leaf_file_delta=2,
            node_file_avg=0,
            node_dir_avg=1,
        ))
        count = tree.file_count()
        assert 3 <= count <= 7

    def test_counts_non_negative(self) -> None:
        """Even with large deltas, counts should never be negative."""
        tree = FilesystemTree(make_plan(
            depth_avg=1,
            depth_delta=1,
            leaf_file_avg=1,
            leaf_file_delta=1,
            node_file_avg=1,
            node_file_delta=1,
            node_dir_avg=1,
            node_dir_delta=1,
        ))
        assert tree.file_count() >= 0
        assert tree.dir_count() >= 0
