from app.extensions import db

class CallGraph(db.Model):
    """服务调用图数据表"""
    __tablename__ = 'call_graph'
    
    trace_id = db.Column(db.String(128), primary_key=True, comment='调用链跟踪ID')
    service_caller = db.Column(db.String(128), nullable=False, index=True, comment='调用方微服务')
    service_callee = db.Column(db.String(128), nullable=False, index=True, comment='被调用方微服务')
    rpc_latency = db.Column(db.Float, comment='RPC请求延迟')
    timestamp = db.Column(db.DateTime, nullable=False, index=True, comment='调用时间戳')
    
    # 建立联合索引以支持多维快速查询
    __table_args__ = (
        db.Index('idx_caller_timestamp', 'service_caller', 'timestamp'),
        db.Index('idx_callee_timestamp', 'service_callee', 'timestamp'),
    )

    def to_dict(self):
        return {
            'trace_id': self.trace_id,
            'service_caller': self.service_caller,
            'service_callee': self.service_callee,
            'rpc_latency': self.rpc_latency,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }
