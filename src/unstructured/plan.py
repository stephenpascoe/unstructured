from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FilesystemPlan:
    """Simulation parameters for generating a random filesystem tree.

    This separates the plan (parameters) from the realised tree structure.
    """

    depth_avg: int
    depth_delta: int = 0
    leaf_file_avg: int = 0
    leaf_file_delta: int = 0
    node_file_avg: int = 0
    node_file_delta: int = 0
    node_dir_avg: int = 0
    node_dir_delta: int = 0

    def _expected_counts(self) -> tuple[int, int]:
        """Return (expected_file_count, expected_dir_count) based on averages."""
        d = self.depth_avg
        n = self.node_dir_avg

        if d <= 0:
            return self.leaf_file_avg, 0

        # Number of leaf nodes = n^d
        leaf_nodes = n**d

        # Non-leaf nodes (including root) = 1 + n + n^2 + ... + n^(d-1)
        if n <= 1:
            non_leaf_nodes = d
        else:
            non_leaf_nodes = (n**d - 1) // (n - 1)

        files = non_leaf_nodes * self.node_file_avg + leaf_nodes * self.leaf_file_avg

        # Dirs excluding root = n + n^2 + ... + n^d
        dirs = leaf_nodes + non_leaf_nodes - 1

        return files, dirs

    def estimate_logical_storage(
        self, block_size: int, inode_size: int, dirent_size: int
    ) -> int:
        """Estimate the number of bytes consumed if this plan is materialised.

        Assumes each file consumes exactly 1 block. Accounts for inode and
        directory-entry overhead.  Ignores erasure encoding, filesystem
        metadata, and replication overhead.
        """
        file_count, dir_count = self._expected_counts()

        # Each file occupies one block
        file_storage = file_count * block_size
        # Every file and directory (including root) has an inode
        inode_storage = (file_count + dir_count + 1) * inode_size
        # Every file and subdirectory is a directory entry in its parent
        dirent_storage = (file_count + dir_count) * dirent_size

        return file_storage + inode_storage + dirent_storage
