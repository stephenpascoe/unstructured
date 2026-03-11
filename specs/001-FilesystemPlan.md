# FilesystemPlan class to separate simulation parameters with the simulation result

Refactor `FilesystemTree` constructor so that it takes a single argument, an instance of `FilesystemPlan`.
A `FilesystemPlan` is a `dataclass` which represents all the parameters used to construct a `FilesystemTree` without
generating the random files and directories.

In addition to being the input parameter for `FilesystemTree` constructor, `FilesystemPlan` has the following methods:

 - estimate_logical_storage(block_size: int, inode_size: int, dirent_size): estimate the number of bytes consumed if
   we materialised this `FilesystemPlan`. Since all files are small we can assume each file consumes 1 block.
   We also take into account the cost of storing inodes and directory entries.  We ignore any erasure encoding,
   filesystem metadata and replication overhead.

Use red/green TDD to develop this feature.  Ensure the test suite and `proposal.md` are updated to reflect these changes.
