from __future__ import annotations

import argparse
import pathlib
import sys

from unstructured.tree import FilesystemPlan, FilesystemTree


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate large filesystem trees for testing.",
    )
    parser.add_argument("--depth-avg", type=int, required=True, help="Average depth of subdirs.")
    parser.add_argument("--depth-delta", type=int, default=0, help="Depth variation +/-.")
    parser.add_argument("--leaf-file-avg", type=int, required=True, help="Average files per leaf dir.")
    parser.add_argument("--leaf-file-delta", type=int, default=0, help="Leaf file variation +/-.")
    parser.add_argument("--node-file-avg", type=int, default=0, help="Average files per non-leaf dir.")
    parser.add_argument("--node-file-delta", type=int, default=0, help="Node file variation +/-.")
    parser.add_argument("--node-dir-avg", type=int, required=True, help="Average subdirs per non-leaf dir.")
    parser.add_argument("--node-dir-delta", type=int, default=0, help="Node dir variation +/-.")

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("file-count", help="Print the total number of files.")
    subparsers.add_parser("dir-count", help="Print the total number of directories.")
    subparsers.add_parser("path-list", help="Print all paths in the tree.")

    apply_parser = subparsers.add_parser("apply", help="Materialise the tree at a given path.")
    apply_parser.add_argument("target", type=pathlib.Path, help="Target directory.")

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)

    plan = FilesystemPlan(
        depth_avg=args.depth_avg,
        depth_delta=args.depth_delta,
        leaf_file_avg=args.leaf_file_avg,
        leaf_file_delta=args.leaf_file_delta,
        node_file_avg=args.node_file_avg,
        node_file_delta=args.node_file_delta,
        node_dir_avg=args.node_dir_avg,
        node_dir_delta=args.node_dir_delta,
    )
    tree = FilesystemTree(plan)

    if args.command == "file-count":
        print(tree.file_count())
    elif args.command == "dir-count":
        print(tree.dir_count())
    elif args.command == "path-list":
        for p in tree.path_list():
            print(p)
    elif args.command == "apply":
        tree.apply(args.target)
        print(f"Created {tree.file_count()} files and {tree.dir_count()} directories under {args.target}")


if __name__ == "__main__":
    main()
