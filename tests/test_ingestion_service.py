"""
tests/test_ingestion_service.py
单元测试：IngestionService.ingest_csv 核心流水线逻辑
覆盖范围：
  - 正常路径：合法 CSV 分块读取 & 批量写入
  - Chunking 机制：确认 chunksize 参数被正确传递（保证低内存流式处理）
  - 容错机制：某批次 DB 异常后回滚，其余批次照常入库
  - 安全防护：目录遍历路径拦截 -> PermissionError
  - 文件缺失：不存在的文件 -> FileNotFoundError
  - 未知类型：无效的 dataset_type -> ValueError
"""
import os
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock, call


# 计算测试用的合法 data 目录
BASE_DATA_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../data')
)
VALID_FILE_PATH = os.path.join(BASE_DATA_DIR, 'CallGraph', 'CallGraph_0.csv')


class TestIngestionServiceValidation:
    """参数校验类测试"""

    def test_unknown_dataset_type_raises_value_error(self, app_ctx):
        """未知的 dataset_type 应立即抛出 ValueError"""
        from app.services.ingestion_service import IngestionService
        with pytest.raises(ValueError, match="Unknown dataset type"):
            IngestionService.ingest_csv('UnknownType', VALID_FILE_PATH)

    def test_path_traversal_raises_permission_error(self, app_ctx):
        """目录遍历攻击路径（../../../etc/passwd）应抛出 PermissionError"""
        from app.services.ingestion_service import IngestionService
        malicious_path = '../../../etc/passwd'
        with pytest.raises(PermissionError, match="Access denied"):
            IngestionService.ingest_csv('CallGraph', malicious_path)

    def test_absolute_path_outside_data_dir_raises_permission_error(self, app_ctx):
        """指向 data 目录以外的绝对路径同样要被拦截"""
        from app.services.ingestion_service import IngestionService
        outside_path = os.path.abspath('/tmp/evil.csv')
        with pytest.raises(PermissionError):
            IngestionService.ingest_csv('CallGraph', outside_path)

    def test_file_not_found_raises_error(self, app_ctx):
        """合法路径格式但文件不存在时应抛出 FileNotFoundError"""
        from app.services.ingestion_service import IngestionService
        non_existent = os.path.join(BASE_DATA_DIR, 'CallGraph', 'nonexistent.csv')
        with pytest.raises(FileNotFoundError):
            IngestionService.ingest_csv('CallGraph', non_existent)


class TestIngestionServiceHappyPath:
    """正常流程类测试"""

    @patch('app.services.ingestion_service.pd.read_csv')
    @patch('app.services.ingestion_service.os.path.exists', return_value=True)
    @patch('app.services.ingestion_service.db')
    def test_happy_path_returns_correct_counts(self, mock_db, mock_exists, mock_read_csv, app_ctx):
        """
        正常路径：CSV 包含 10 行数据（1 个 chunk），应成功插入并返回 inserted=10, errors=0
        """
        from app.services.ingestion_service import IngestionService

        # 模拟 1 个包含 10 行的 chunk
        mock_chunk = pd.DataFrame({
            'trace_id': [f'trace_{i}' for i in range(10)],
            'service_caller': ['svc_a'] * 10,
            'service_callee': ['svc_b'] * 10,
            'rpc_latency': [0.5] * 10,
            'timestamp': ['2026-01-01 00:00:00'] * 10
        })
        mock_read_csv.return_value = [mock_chunk]

        result = IngestionService.ingest_csv('CallGraph', VALID_FILE_PATH)

        assert result['status'] == 'success'
        assert result['inserted'] == 10
        assert result['errors'] == 0
        mock_db.session.bulk_insert_mappings.assert_called_once()
        mock_db.session.commit.assert_called_once()

    @patch('app.services.ingestion_service.pd.read_csv')
    @patch('app.services.ingestion_service.os.path.exists', return_value=True)
    @patch('app.services.ingestion_service.db')
    def test_chunking_is_used_with_correct_chunksize(self, mock_db, mock_exists, mock_read_csv, app_ctx):
        """
        确认 pandas.read_csv 调用时传入了 chunksize 参数（保证流式低内存读取，不一次性加载）
        """
        from app.services.ingestion_service import IngestionService

        mock_read_csv.return_value = []  # 无数据，只测参数传递
        IngestionService.ingest_csv('CallGraph', VALID_FILE_PATH, chunk_size=2000)

        _, kwargs = mock_read_csv.call_args
        assert kwargs.get('chunksize') == 2000, "必须传入 chunksize 进行流式处理"

    @patch('app.services.ingestion_service.pd.read_csv')
    @patch('app.services.ingestion_service.os.path.exists', return_value=True)
    @patch('app.services.ingestion_service.db')
    def test_multiple_chunks_are_all_inserted(self, mock_db, mock_exists, mock_read_csv, app_ctx):
        """
        多批次数据（3 个 chunk，每个 5 行）：应累计插入 15 行
        """
        from app.services.ingestion_service import IngestionService

        def make_chunk(n=5):
            return pd.DataFrame({'trace_id': [f'id_{i}' for i in range(n)]})

        mock_read_csv.return_value = [make_chunk(), make_chunk(), make_chunk()]

        result = IngestionService.ingest_csv('CallGraph', VALID_FILE_PATH)

        assert result['inserted'] == 15
        assert mock_db.session.commit.call_count == 3


class TestIngestionServiceFaultTolerance:
    """容错与脏数据类测试"""

    @patch('app.services.ingestion_service.pd.read_csv')
    @patch('app.services.ingestion_service.os.path.exists', return_value=True)
    @patch('app.services.ingestion_service.db')
    def test_db_error_in_one_chunk_causes_rollback_and_continues(
        self, mock_db, mock_exists, mock_read_csv, app_ctx
    ):
        """
        容错核心测试：第 1 个 chunk 写入失败 -> 该批次 rollback，但第 2 批次应照常入库。
        最终：inserted=5, errors=5
        """
        from app.services.ingestion_service import IngestionService

        chunk_ok = pd.DataFrame({'trace_id': [f'ok_{i}' for i in range(5)]})
        chunk_bad = pd.DataFrame({'trace_id': [f'bad_{i}' for i in range(5)]})

        # 第一次调用 bulk_insert_mappings 抛出异常，第二次正常
        mock_db.session.bulk_insert_mappings.side_effect = [Exception("DB error"), None]
        mock_read_csv.return_value = [chunk_bad, chunk_ok]

        result = IngestionService.ingest_csv('CallGraph', VALID_FILE_PATH)

        # 第 1 批失败 rollback，第 2 批成功
        assert result['errors'] == 5
        assert result['inserted'] == 5
        mock_db.session.rollback.assert_called_once()
        assert mock_db.session.commit.call_count == 1

    @patch('app.services.ingestion_service.pd.read_csv')
    @patch('app.services.ingestion_service.os.path.exists', return_value=True)
    @patch('app.services.ingestion_service.db')
    def test_nan_values_are_replaced_with_none(self, mock_db, mock_exists, mock_read_csv, app_ctx):
        """
        数据清洗验证：CSV 中的 NaN 值应被替换为 None 后再传入 bulk_insert_mappings
        """
        import math
        from app.services.ingestion_service import IngestionService

        chunk = pd.DataFrame({'trace_id': ['t1', None], 'rpc_latency': [float('nan'), 0.5]})
        mock_read_csv.return_value = [chunk]

        IngestionService.ingest_csv('CallGraph', VALID_FILE_PATH)

        # 取实际传入的 records 列表
        call_args = mock_db.session.bulk_insert_mappings.call_args
        records = call_args[0][1]

        # NaN/None 都应该被转换成 None
        for record in records:
            for v in record.values():
                assert not (isinstance(v, float) and math.isnan(v)), \
                    "NaN 值未被清洗为 None，可能导致数据库写入异常"
