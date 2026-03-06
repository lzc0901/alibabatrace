"""
tests/test_ingestion_bp.py
单元测试：Flask Blueprint 路由 /api/v1/ingestion/*
覆盖范围：
  - POST /ingestion/start：合法请求 -> 202 + task_id
  - POST /ingestion/start：缺少参数 -> 400
  - GET  /ingestion/status/<task_id>：已知 task_id -> 200 + 状态
  - GET  /ingestion/status/<unknown>：未知 task_id -> 404
"""
import json
import pytest
from unittest.mock import patch


class TestIngestionStart:
    """POST /api/v1/ingestion/start 端点测试"""

    @patch('app.api.ingestion_bp.threading.Thread')
    def test_valid_request_returns_202_with_task_id(self, mock_thread, client):
        """合法请求：应立即返回 202，并在响应中携带有效的 task_id"""
        mock_thread.return_value.start.return_value = None

        response = client.post(
            '/api/v1/ingestion/start',
            data=json.dumps({
                'dataset_type': 'CallGraph',
                'file_path': 'data/CallGraph/CallGraph_0.csv',
                'batch_size': 5000
            }),
            content_type='application/json'
        )

        assert response.status_code == 202
        data = response.get_json()
        assert 'task_id' in data
        assert data['status'] == 'running'
        # 验证后台线程被启动
        mock_thread.return_value.start.assert_called_once()

    def test_missing_dataset_type_returns_400(self, client):
        """缺少 dataset_type 参数应返回 400 Bad Request"""
        response = client.post(
            '/api/v1/ingestion/start',
            data=json.dumps({'file_path': 'data/CallGraph/CallGraph_0.csv'}),
            content_type='application/json'
        )
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data

    def test_missing_file_path_returns_400(self, client):
        """缺少 file_path 参数应返回 400 Bad Request"""
        response = client.post(
            '/api/v1/ingestion/start',
            data=json.dumps({'dataset_type': 'CallGraph'}),
            content_type='application/json'
        )
        assert response.status_code == 400

    def test_missing_both_params_returns_400(self, client):
        """同时缺少 dataset_type 和 file_path 应返回 400"""
        response = client.post(
            '/api/v1/ingestion/start',
            data=json.dumps({}),
            content_type='application/json'
        )
        assert response.status_code == 400

    @patch('app.api.ingestion_bp.threading.Thread')
    def test_default_batch_size_is_applied(self, mock_thread, client):
        """未传 batch_size 参数时，系统应使用默认值（5000）而不报错"""
        mock_thread.return_value.start.return_value = None

        response = client.post(
            '/api/v1/ingestion/start',
            data=json.dumps({
                'dataset_type': 'Node',
                'file_path': 'data/Node/NodeMetricsUpdate_0.csv'
            }),
            content_type='application/json'
        )
        assert response.status_code == 202


class TestIngestionStatus:
    """GET /api/v1/ingestion/status/<task_id> 端点测试"""

    @patch('app.api.ingestion_bp.threading.Thread')
    def test_known_task_id_returns_200_with_status(self, mock_thread, client):
        """先创建任务拿到 task_id，再轮询该 task_id 应返回 200 并携带状态信息"""
        mock_thread.return_value.start.return_value = None

        # 创建一个任务
        start_resp = client.post(
            '/api/v1/ingestion/start',
            data=json.dumps({
                'dataset_type': 'CallGraph',
                'file_path': 'data/CallGraph/CallGraph_0.csv'
            }),
            content_type='application/json'
        )
        task_id = start_resp.get_json()['task_id']

        # 轮询状态
        status_resp = client.get(f'/api/v1/ingestion/status/{task_id}')
        assert status_resp.status_code == 200
        status_data = status_resp.get_json()
        assert 'status' in status_data

    def test_unknown_task_id_returns_404(self, client):
        """未知的 task_id 应返回 404 Not Found"""
        response = client.get('/api/v1/ingestion/status/nonexistent-task-id-000')
        assert response.status_code == 404
        data = response.get_json()
        assert 'error' in data
