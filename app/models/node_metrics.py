from app.extensions import db

class NodeMetrics(db.Model):
    """节点性能指标数据表"""
    __tablename__ = 'node_metrics'
    
    id = db.Column(db.BigInteger().with_variant(db.Integer, 'sqlite'), primary_key=True, autoincrement=True, comment='主键ID')
    node_id = db.Column(db.String(128), nullable=False, index=True, comment='机器节点标识')
    cpu_usage = db.Column(db.Float, comment='CPU 使用率')
    mem_usage = db.Column(db.Float, comment='内存 使用率')
    timestamp = db.Column(db.DateTime, nullable=False, index=True, comment='指标时间戳')

    # 支持基于节点ID和时间戳的高效索引
    __table_args__ = (
        db.Index('idx_node_timestamp', 'node_id', 'timestamp'),
    )

    def to_dict(self):
        return {
            'node_id': self.node_id,
            'cpu_usage': self.cpu_usage,
            'mem_usage': self.mem_usage,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }
