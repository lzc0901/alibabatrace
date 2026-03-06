"""
tests/test_models.py
单元测试：SQLAlchemy ORM 模型
覆盖范围：
  - 各模型 to_dict() 方法返回期望的字段结构
  - 验证数据库表名和联合索引定义存在
  - 最基础的模型工厂入库 & 查询
"""
import pytest
from datetime import datetime


class TestCallGraphModel:
    """CallGraph 模型测试"""

    def test_table_name(self):
        from app.models.call_graph import CallGraph
        assert CallGraph.__tablename__ == 'call_graph'

    def test_to_dict_has_expected_keys(self):
        from app.models.call_graph import CallGraph
        obj = CallGraph(
            trace_id='t1',
            service_caller='svc_a',
            service_callee='svc_b',
            rpc_latency=0.5,
            timestamp=datetime(2026, 1, 1)
        )
        d = obj.to_dict()
        assert set(d.keys()) == {'trace_id', 'service_caller', 'service_callee', 'rpc_latency', 'timestamp'}

    def test_to_dict_timestamp_is_isoformat(self):
        from app.models.call_graph import CallGraph
        ts = datetime(2026, 3, 7, 12, 0, 0)
        obj = CallGraph(trace_id='t2', service_caller='a', service_callee='b', timestamp=ts)
        d = obj.to_dict()
        assert d['timestamp'] == ts.isoformat()

    def test_to_dict_null_timestamp_is_none(self):
        from app.models.call_graph import CallGraph
        obj = CallGraph(trace_id='t3', service_caller='a', service_callee='b', timestamp=None)
        assert obj.to_dict()['timestamp'] is None

    def test_composite_indexes_defined(self):
        from app.models.call_graph import CallGraph
        index_names = {idx.name for idx in CallGraph.__table__.indexes}
        assert 'idx_caller_timestamp' in index_names
        assert 'idx_callee_timestamp' in index_names


class TestMSResourceModel:
    """MSResource 模型测试"""

    def test_table_name(self):
        from app.models.ms_resource import MSResource
        assert MSResource.__tablename__ == 'ms_resource'

    def test_to_dict_has_expected_keys(self):
        from app.models.ms_resource import MSResource
        obj = MSResource(ms_id='ms_1', qps=100.0, err_rate=0.01, timestamp=datetime(2026, 1, 1))
        d = obj.to_dict()
        assert set(d.keys()) == {'ms_id', 'qps', 'err_rate', 'timestamp'}

    def test_composite_index_defined(self):
        from app.models.ms_resource import MSResource
        index_names = {idx.name for idx in MSResource.__table__.indexes}
        assert 'idx_ms_timestamp' in index_names


class TestNodeMetricsModel:
    """NodeMetrics 模型测试"""

    def test_table_name(self):
        from app.models.node_metrics import NodeMetrics
        assert NodeMetrics.__tablename__ == 'node_metrics'

    def test_to_dict_has_expected_keys(self):
        from app.models.node_metrics import NodeMetrics
        obj = NodeMetrics(node_id='node_1', cpu_usage=0.8, mem_usage=0.6, timestamp=datetime(2026, 1, 1))
        d = obj.to_dict()
        assert set(d.keys()) == {'node_id', 'cpu_usage', 'mem_usage', 'timestamp'}

    def test_composite_index_defined(self):
        from app.models.node_metrics import NodeMetrics
        index_names = {idx.name for idx in NodeMetrics.__table__.indexes}
        assert 'idx_node_timestamp' in index_names


class TestMSRtMcrModel:
    """MSRtMcr 模型测试"""

    def test_table_name(self):
        from app.models.ms_rt_mcr import MSRtMcr
        assert MSRtMcr.__tablename__ == 'ms_rt_mcr'

    def test_to_dict_has_expected_keys(self):
        from app.models.ms_rt_mcr import MSRtMcr
        obj = MSRtMcr(
            timestamp=60000,
            msname='MS_001',
            msinstanceid='MS_001_POD_1',
            nodeid='NODE_01'
        )
        d = obj.to_dict()
        expected_keys = {
            'id', 'timestamp', 'msname', 'msinstanceid', 'nodeid',
            'providerrpc_rt', 'providerrpc_mcr',
            'consumerrpc_rt', 'consumerrpc_mcr',
            'writemc_rt', 'writemc_mcr', 'readmc_rt', 'readmc_mcr',
            'writedb_rt', 'writedb_mcr', 'readdb_rt', 'readdb_mcr',
            'consumermq_rt', 'consumermq_mcr',
            'providermq_rt', 'providermq_mcr',
            'http_mcr', 'http_rt'
        }
        assert set(d.keys()) == expected_keys

    def test_composite_indexes_defined(self):
        from app.models.ms_rt_mcr import MSRtMcr
        index_names = {idx.name for idx in MSRtMcr.__table__.indexes}
        assert 'idx_msname_timestamp' in index_names
        assert 'idx_nodeid_timestamp' in index_names


class TestModelsInDatabase:
    """数据库读写集成测试（使用 SQLite 内存库）"""

    def test_call_graph_insert_and_query(self, app_ctx):
        from app.extensions import db
        from app.models.call_graph import CallGraph

        record = CallGraph(
            trace_id='integration_t1',
            service_caller='svc_x',
            service_callee='svc_y',
            rpc_latency=1.23,
            timestamp=datetime(2026, 3, 7)
        )
        db.session.add(record)
        db.session.commit()

        fetched = CallGraph.query.filter_by(trace_id='integration_t1').first()
        assert fetched is not None
        assert fetched.service_caller == 'svc_x'
        assert fetched.rpc_latency == pytest.approx(1.23)

    def test_node_metrics_insert_and_query(self, app_ctx):
        from app.extensions import db
        from app.models.node_metrics import NodeMetrics

        record = NodeMetrics(
            node_id='NODE_99',
            cpu_usage=0.75,
            mem_usage=0.50,
            timestamp=datetime(2026, 3, 7)
        )
        db.session.add(record)
        db.session.commit()

        fetched = NodeMetrics.query.filter_by(node_id='NODE_99').first()
        assert fetched is not None
        assert fetched.cpu_usage == pytest.approx(0.75)
