from __future__ import annotations

import pathlib

import click

from unstructured.plan import FilesystemPlan
from unstructured.tree import FilesystemTree


def _plan_options(f):  # noqa: ANN001, ANN202
    """Shared click options for building a FilesystemPlan."""
    f = click.option("--depth-avg", type=int, required=True, help="Average depth of subdirs.")(f)
    f = click.option("--depth-delta", type=int, default=0, help="Depth variation +/-.")(f)
    f = click.option("--leaf-file-avg", type=int, required=True, help="Average files per leaf dir.")(f)
    f = click.option("--leaf-file-delta", type=int, default=0, help="Leaf file variation +/-.")(f)
    f = click.option("--node-file-avg", type=int, default=0, help="Average files per non-leaf dir.")(f)
    f = click.option("--node-file-delta", type=int, default=0, help="Node file variation +/-.")(f)
    f = click.option("--node-dir-avg", type=int, required=True, help="Average subdirs per non-leaf dir.")(f)
    f = click.option("--node-dir-delta", type=int, default=0, help="Node dir variation +/-.")(f)
    return f


def _make_plan(kwargs: dict) -> FilesystemPlan:  # noqa: ANN001
    return FilesystemPlan(
        depth_avg=kwargs["depth_avg"],
        depth_delta=kwargs["depth_delta"],
        leaf_file_avg=kwargs["leaf_file_avg"],
        leaf_file_delta=kwargs["leaf_file_delta"],
        node_file_avg=kwargs["node_file_avg"],
        node_file_delta=kwargs["node_file_delta"],
        node_dir_avg=kwargs["node_dir_avg"],
        node_dir_delta=kwargs["node_dir_delta"],
    )


@click.group(help="Generate large filesystem trees for testing.")
def main() -> None:
    pass


@main.command("path-list", help="Print all paths in the tree.")
@_plan_options
def path_list(**kwargs: int) -> None:
    plan = _make_plan(kwargs)
    tree = FilesystemTree(plan)
    for p in tree.path_list():
        click.echo(p)


@main.command("apply", help="Materialise the tree at a given path.")
@_plan_options
@click.argument("target", type=click.Path(path_type=pathlib.Path))
def apply_cmd(target: pathlib.Path, **kwargs: int) -> None:
    plan = _make_plan(kwargs)
    tree = FilesystemTree(plan)
    tree.apply(target)
    click.echo(
        f"Created {tree.file_count()} files and {tree.dir_count()} directories under {target}"
    )
    tree = FilesystemTree(plan)


@main.command("estimate", help="Print analytical estimates for files, directories, and logical storage.")
@_plan_options
@click.option("--block-size", type=int, default=4096, help="Block size in bytes.")
@click.option("--inode-size", type=int, default=256, help="Inode size in bytes.")
@click.option("--dirent-size", type=int, default=256, help="Directory entry size in bytes.")
def estimate(block_size: int, inode_size: int, dirent_size: int, **kwargs: int) -> None:
    plan = _make_plan(kwargs)
    file_count, dir_count = plan._expected_counts()
    logical_storage = plan.estimate_logical_storage(block_size, inode_size, dirent_size)
    click.echo(f"Files:           {file_count}")
    click.echo(f"Directories:     {dir_count}")
    click.echo(f"Logical storage: {logical_storage}")


if __name__ == "__main__":
    main()
