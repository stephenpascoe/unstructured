from __future__ import annotations

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


class _Node:
    """Internal representation of a node in the filesystem tree."""

    def __init__(self, name: str, files: list[str], children: list[_Node]) -> None:
        self.name = name
        self.files = files
        self.children = children


class FilesystemTree:
    """Encapsulates the structure of a random filesystem tree."""

    def __init__(
        self,
        *,
        depth_avg: int,
        depth_delta: int,
        leaf_file_avg: int,
        leaf_file_delta: int,
        node_file_avg: int,
        node_file_delta: int,
        node_dir_avg: int,
        node_dir_delta: int,
    ) -> None:
        self.depth_avg = depth_avg
        self.depth_delta = depth_delta
        self.leaf_file_avg = leaf_file_avg
        self.leaf_file_delta = leaf_file_delta
        self.node_file_avg = node_file_avg
        self.node_file_delta = node_file_delta
        self.node_dir_avg = node_dir_avg
        self.node_dir_delta = node_dir_delta

        self._root = self._build_tree(remaining_depth=_rand_int(depth_avg, depth_delta))

    def _build_tree(self, remaining_depth: int) -> _Node:
        if remaining_depth <= 0:
            # Leaf node
            num_files = _rand_int(self.leaf_file_avg, self.leaf_file_delta)
            files = [f"file_{_random_suffix()}" for _ in range(num_files)]
            return _Node(name="root", files=files, children=[])

        # Non-leaf node
        num_files = _rand_int(self.node_file_avg, self.node_file_delta)
        num_dirs = _rand_int(self.node_dir_avg, self.node_dir_delta)
        files = [f"file_{_random_suffix()}" for _ in range(num_files)]
        children = []
        for _ in range(num_dirs):
            child_depth = remaining_depth - 1
            child = self._build_tree(remaining_depth=child_depth)
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
