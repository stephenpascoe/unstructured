from __future__ import annotations

import dataclasses
import pathlib
import random
import string
from typing import Generator


def _random_suffix(length: int = 6) -> str:
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))


def _clamp_non_negative(value: int) -> int:
    return max(0, value)


def _rand_int(avg: int, delta: int) -> int:
    if delta == 0:
        return avg
    return _clamp_non_negative(random.randint(avg - delta, avg + delta))


@dataclasses.dataclass
class FilesystemPlan:
    """Parameters used to construct a FilesystemTree, without generating random files/dirs."""

    depth_avg: int
    depth_delta: int
    leaf_file_avg: int
    leaf_file_delta: int
    node_file_avg: int
    node_file_delta: int
    node_dir_avg: int
    node_dir_delta: int

    def _estimated_dir_count(self) -> int:
        """Estimate number of directories using avg parameters (ignoring delta)."""
        D = self.depth_avg
        N = self.node_dir_avg
        if D == 0 or N == 0:
            return 0
        if N == 1:
            return D
        return round(N * (N**D - 1) / (N - 1))

    def _estimated_file_count(self) -> int:
        """Estimate number of files using avg parameters (ignoring delta)."""
        D = self.depth_avg
        N = self.node_dir_avg
        Lf = self.leaf_file_avg
        Nf = self.node_file_avg
        if N == 0 or D == 0:
            # Root is a leaf
            return Lf
        leaf_nodes = N**D
        if N == 1:
            non_leaf_nodes = D
        else:
            non_leaf_nodes = round((N**D - 1) / (N - 1))
        return Nf * non_leaf_nodes + Lf * leaf_nodes

    def estimate_logical_storage(self, block_size: int, inode_size: int, dirent_size: int) -> int:
        """Estimate bytes consumed if this plan were materialised.

        Assumes each file consumes 1 block. Accounts for inodes and directory
        entries. Ignores erasure encoding, filesystem metadata and replication.
        """
        file_count = self._estimated_file_count()
        dir_count = self._estimated_dir_count()
        storage = (
            file_count * block_size
            + (file_count + dir_count) * inode_size
            + (file_count + dir_count) * dirent_size
        )
        return storage


class _Node:
    """Internal representation of a node in the filesystem tree."""

    def __init__(self, name: str, files: list[str], children: list[_Node]) -> None:
        self.name = name
        self.files = files
        self.children = children


class FilesystemTree:
    """Encapsulates the structure of a random filesystem tree."""

    def __init__(self, plan: FilesystemPlan) -> None:
        self.plan = plan
        self._root = self._build_tree(
            remaining_depth=_rand_int(plan.depth_avg, plan.depth_delta)
        )

    def _build_tree(self, remaining_depth: int) -> _Node:
        plan = self.plan
        if remaining_depth <= 0:
            # Leaf node
            num_files = _rand_int(plan.leaf_file_avg, plan.leaf_file_delta)
            files = [f"file_{_random_suffix()}" for _ in range(num_files)]
            return _Node(name="root", files=files, children=[])

        # Non-leaf node
        num_files = _rand_int(plan.node_file_avg, plan.node_file_delta)
        num_dirs = _rand_int(plan.node_dir_avg, plan.node_dir_delta)
        files = [f"file_{_random_suffix()}" for _ in range(num_files)]
        children = []
        for _ in range(num_dirs):
            child = self._build_tree(remaining_depth=remaining_depth - 1)
            child.name = f"dir_{_random_suffix()}"
            children.append(child)
        return _Node(name="root", files=files, children=children)

    def path_list(self) -> Generator[str, None, None]:
        """Returns a generator of paths for each file and directory in the tree."""
        yield from self._path_list_node(self._root, pathlib.PurePosixPath("."))

    def _path_list_node(
        self, node: _Node, prefix: pathlib.PurePosixPath
    ) -> Generator[str, None, None]:
        for child in node.children:
            child_path = prefix / child.name
            yield str(child_path)
            yield from self._path_list_node(child, child_path)
        for f in node.files:
            yield str(prefix / f)

    def dir_count(self) -> int:
        """Returns the total number of directories under the root."""
        return self._count_dirs(self._root)

    def _count_dirs(self, node: _Node) -> int:
        count = len(node.children)
        for child in node.children:
            count += self._count_dirs(child)
        return count

    def file_count(self) -> int:
        """Returns the total number of files under the root."""
        return self._count_files(self._root)

    def _count_files(self, node: _Node) -> int:
        count = len(node.files)
        for child in node.children:
            count += self._count_files(child)
        return count

    def apply(self, path: pathlib.Path) -> None:
        """Create files and directories under path to materialise the tree."""
        self._apply_node(self._root, path)

    def _apply_node(self, node: _Node, path: pathlib.Path) -> None:
        path.mkdir(parents=True, exist_ok=True)
        for f in node.files:
            (path / f).write_text(f"This is a test file {f}")
        for child in node.children:
            child_path = path / child.name
            self._apply_node(child, child_path)
