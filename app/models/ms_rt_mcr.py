from app.extensions import db

class MSRtMcr(db.Model):
    """微服务(MS)各类请求的响应时间(RT)和调用率(MCR)实时指标数据表"""
    __tablename__ = 'ms_rt_mcr'
    
    id = db.Column(db.BigInteger().with_variant(db.Integer, 'sqlite'), primary_key=True, autoincrement=True, comment='主键ID')
    timestamp = db.Column(db.BigInteger, nullable=False, index=True, comment='指标时间戳(毫秒/时间切片)')
    msname = db.Column(db.String(128), nullable=False, index=True, comment='微服务名称')
    msinstanceid = db.Column(db.String(128), nullable=False, index=True, comment='微服务实例ID(POD)')
    nodeid = db.Column(db.String(128), nullable=False, index=True, comment='节点ID')
    
    # Provider RPC Metrics
    providerrpc_rt = db.Column(db.Float, comment='Provider RPC 响应时间')
    providerrpc_mcr = db.Column(db.Float, comment='Provider RPC 调用率')
    
    # Consumer RPC Metrics
    consumerrpc_rt = db.Column(db.Float, comment='Consumer RPC 响应时间')
    consumerrpc_mcr = db.Column(db.Float, comment='Consumer RPC 调用率')
    
    # Memcached (MC) Metrics
    writemc_rt = db.Column(db.Float, comment='Write MC 响应时间')
    writemc_mcr = db.Column(db.Float, comment='Write MC 调用率')
    readmc_rt = db.Column(db.Float, comment='Read MC 响应时间')
    readmc_mcr = db.Column(db.Float, comment='Read MC 调用率')
    
    # Database (DB) Metrics
    writedb_rt = db.Column(db.Float, comment='Write DB 响应时间')
    writedb_mcr = db.Column(db.Float, comment='Write DB 调用率')
    readdb_rt = db.Column(db.Float, comment='Read DB 响应时间')
    readdb_mcr = db.Column(db.Float, comment='Read DB 调用率')
    
    # Message Queue (MQ) Metrics
    consumermq_rt = db.Column(db.Float, comment='Consumer MQ 响应时间')
    consumermq_mcr = db.Column(db.Float, comment='Consumer MQ 调用率')
    providermq_rt = db.Column(db.Float, comment='Provider MQ 响应时间')
    providermq_mcr = db.Column(db.Float, comment='Provider MQ 调用率')
    
    # HTTP Metrics
    http_mcr = db.Column(db.Float, comment='HTTP 调用率')
    http_rt = db.Column(db.Float, comment='HTTP 响应时间')

    # 建立联合索引支持多维快速查询
    __table_args__ = (
        db.Index('idx_msname_timestamp', 'msname', 'timestamp'),
        db.Index('idx_nodeid_timestamp', 'nodeid', 'timestamp'),
        db.Index('idx_msinstanceid', 'msinstanceid'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp,
            'msname': self.msname,
            'msinstanceid': self.msinstanceid,
            'nodeid': self.nodeid,
            'providerrpc_rt': self.providerrpc_rt,
            'providerrpc_mcr': self.providerrpc_mcr,
            'consumerrpc_rt': self.consumerrpc_rt,
            'consumerrpc_mcr': self.consumerrpc_mcr,
            'writemc_rt': self.writemc_rt,
            'writemc_mcr': self.writemc_mcr,
            'readmc_rt': self.readmc_rt,
            'readmc_mcr': self.readmc_mcr,
            'writedb_rt': self.writedb_rt,
            'writedb_mcr': self.writedb_mcr,
            'readdb_rt': self.readdb_rt,
            'readdb_mcr': self.readdb_mcr,
            'consumermq_rt': self.consumermq_rt,
            'consumermq_mcr': self.consumermq_mcr,
            'providermq_rt': self.providermq_rt,
            'providermq_mcr': self.providermq_mcr,
            'http_mcr': self.http_mcr,
            'http_rt': self.http_rt
        }
