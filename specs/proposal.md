# Proposal: Create large filesystem trees for testing unstructured data management tools

Create a python tool for generating a file system tree with potentially over 1 billion files.
The functionality should be accessible through a clear Python API using type hints.
There is a cli wrapper around the API to execute all functionality on the command line.

Use uv and a project.toml file for package management.  Use red/green TDD during development.

The API includes a `FilesystemPlan` dataclass and a `FilesystemTree` class.

A `FilesystemPlan` holds all the parameters that describe a filesystem structure without generating
any random files or directories.  `FilesystemTree` takes a single `FilesystemPlan` argument and
generates the random tree from it.

`FilesystemPlan` is constructed with the following parameters:

 - depth_avg: The average depth of each subdir under the root.
 - depth_delta: Random variation of the depth of each subdir under the root +/- this value.
 - leaf_file_avg: The average number of files in each leaf dir.  I.e. dirs without subdirs.
 - leaf_file_delta: Random variation +/- of the number of files in each leaf dir.
 - node_file_avg: The average number of files in non-leaf dirs.  I.e. folders containing subfolders.
 - node_file_delta: Random variation +/- of the number of files in each non-leaf dir.
 - node_dir_avg: The average number of subdirs in non-leaf dirs.
 - node_dir_delta: Random variation +/- of the number of subdirs in each non-leaf dir.

`FilesystemPlan` has the following methods:

 - estimate_logical_storage(block_size: int, inode_size: int, dirent_size: int): Estimate the number
   of bytes consumed if the plan were materialised.  Each file is assumed to consume 1 block.
   Inode and directory entry costs are included.  Erasure encoding, filesystem metadata and
   replication overhead are ignored.

`FilesystemTree` is constructed from a `FilesystemPlan` and has the following methods:

 - path_list(): returns a generator of paths for each file and directory in the FilesystemTree.
 - dir_count(): returns the total number of directories under the root.
 - file_count(): returns the total number of files under the root.
 - apply(path: pathlib.Path): Create files and directories under `path` to materialise the FilesystemTree.

Files should follow the naming convention `file_{6-random-chars}` and directories `dir_{6-random-chars}`.
When materialising the FilesystemTree each file should contain a short test string of the form `This is a test file {filename}`

## Acceptance criteria

GIVEN a FilesystemTree where all *_delta parameters are zero
WHEN depth_avg is 0
THEN file_count() == len(list(path_list())) == leaf_file_avg
