from unstructured.plan import FilesystemPlan


class TestFilesystemPlan:
    def test_is_dataclass(self) -> None:
        plan = FilesystemPlan(depth_avg=2, leaf_file_avg=3, node_dir_avg=2)
        assert plan.depth_avg == 2
        assert plan.depth_delta == 0

    def test_frozen(self) -> None:
        plan = FilesystemPlan(depth_avg=1)
        try:
            plan.depth_avg = 5  # type: ignore[misc]
            assert False, "Should raise FrozenInstanceError"
        except AttributeError:
            pass


class TestExpectedCounts:
    def test_depth_zero(self) -> None:
        plan = FilesystemPlan(depth_avg=0, leaf_file_avg=5, node_dir_avg=2)
        files, dirs = plan._expected_counts()
        assert files == 5
        assert dirs == 0

    def test_depth_one(self) -> None:
        plan = FilesystemPlan(
            depth_avg=1, leaf_file_avg=3, node_file_avg=1, node_dir_avg=2,
        )
        files, dirs = plan._expected_counts()
        # 1 non-leaf (root) with 1 file + 2 leaves with 3 files each = 7
        assert files == 7
        # 2 dirs
        assert dirs == 2

    def test_depth_two(self) -> None:
        plan = FilesystemPlan(
            depth_avg=2, leaf_file_avg=3, node_file_avg=1, node_dir_avg=2,
        )
        files, dirs = plan._expected_counts()
        # non-leaf: 1 + 2 = 3 nodes, leaf: 4 nodes
        # files: 3*1 + 4*3 = 15
        assert files == 15
        # dirs: 2 + 4 = 6
        assert dirs == 6


class TestEstimateLogicalStorage:
    def test_depth_zero_simple(self) -> None:
        plan = FilesystemPlan(depth_avg=0, leaf_file_avg=5, node_dir_avg=2)
        # 5 files, 0 dirs
        # file_storage: 5 * 4096 = 20480
        # inode_storage: (5 + 0 + 1) * 256 = 1536
        # dirent_storage: (5 + 0) * 256 = 1280
        # total = 23296
        assert plan.estimate_logical_storage(4096, 256, 256) == 23296

    def test_depth_one(self) -> None:
        plan = FilesystemPlan(
            depth_avg=1, leaf_file_avg=3, node_file_avg=1, node_dir_avg=2,
        )
        # 7 files, 2 dirs
        # file_storage: 7 * 4096 = 28672
        # inode_storage: (7 + 2 + 1) * 256 = 2560
        # dirent_storage: (7 + 2) * 256 = 2304
        # total = 33536
        assert plan.estimate_logical_storage(4096, 256, 256) == 33536

    def test_custom_sizes(self) -> None:
        plan = FilesystemPlan(depth_avg=0, leaf_file_avg=1, node_dir_avg=1)
        # 1 file, 0 dirs
        # file_storage: 1 * 512 = 512
        # inode_storage: (1 + 0 + 1) * 128 = 256
        # dirent_storage: (1 + 0) * 64 = 64
        # total = 832
        assert plan.estimate_logical_storage(512, 128, 64) == 832

    def test_no_files(self) -> None:
        plan = FilesystemPlan(depth_avg=0, leaf_file_avg=0, node_dir_avg=1)
        # 0 files, 0 dirs
        # file_storage: 0
        # inode_storage: (0 + 0 + 1) * 256 = 256 (root inode)
        # dirent_storage: 0
        # total = 256
        assert plan.estimate_logical_storage(4096, 256, 256) == 256
