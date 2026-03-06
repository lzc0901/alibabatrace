from app.extensions import db

class MSResource(db.Model):
    """微服务资源指标数据表"""
    __tablename__ = 'ms_resource'
    
    id = db.Column(db.BigInteger().with_variant(db.Integer, 'sqlite'), primary_key=True, autoincrement=True, comment='主键ID')
    ms_id = db.Column(db.String(128), nullable=False, index=True, comment='微服务ID')
    qps = db.Column(db.Float, comment='Queries Per Second 请求率')
    err_rate = db.Column(db.Float, comment='Error Rate 错误率')
    timestamp = db.Column(db.DateTime, nullable=False, index=True, comment='指标时间戳')

    # 支持基于微服务和时间的快速时序图查询
    __table_args__ = (
        db.Index('idx_ms_timestamp', 'ms_id', 'timestamp'),
    )

    def to_dict(self):
        return {
            'ms_id': self.ms_id,
            'qps': self.qps,
            'err_rate': self.err_rate,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }
