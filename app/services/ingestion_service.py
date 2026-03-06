import os
import pandas as pd
import logging
from app.extensions import db
from app.models import CallGraph, MSResource, NodeMetrics, MSRtMcr

logger = logging.getLogger(__name__)

class IngestionService:
    # 映射 dataset_type 到具体的 SQLAlchemy Model
    MODEL_MAP = {
        'CallGraph': CallGraph,
        'MSResource': MSResource,
        'Node': NodeMetrics,
        'MSRTMCR': MSRtMcr
    }

    @classmethod
    def ingest_csv(cls, dataset_type: str, file_path: str, chunk_size: int = 5000):
        """
        流式读取 CSV 并批量导入对应的数据库表中。
        针对亿级数据：保持低内存，每 `chunk_size` 条数据做一次 bulk insert 和 commit。
        """
        if dataset_type not in cls.MODEL_MAP:
            raise ValueError(f"Unknown dataset type: {dataset_type}")
            
        model = cls.MODEL_MAP[dataset_type]
        
        # 安全防御：防目录遍历攻击 (Directory Traversal)
        # 获取允许的数据根目录绝对路径
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../data'))
        # 将传入的文件路径转为绝对路径
        abs_file_path = os.path.abspath(file_path)
        
        if not abs_file_path.startswith(base_dir):
            raise PermissionError(f"Secure path violation. Access denied to path outside of data directory.")
            
        if not os.path.exists(abs_file_path):
            raise FileNotFoundError(f"File not found: {abs_file_path}")

        total_inserted = 0
        errors = 0
        
        try:
            # 1. 使用 Pandas 按块读取 (Chunking 流式处理)
            for chunk in pd.read_csv(abs_file_path, chunksize=chunk_size):
                # 2. 数据清洗 (将 csv 中的 null、NaN 统一替换成 None 适配数据库)
                # 先转成 object dtype，防止 pandas 把 float 列的 None 再转回 nan
                chunk = chunk.astype(object).where(pd.notnull(chunk), None)
                
                # 可选：如果有些列是时间戳但在 csv 里是字符串，这里可以加转换拦截逻辑
                # if 'timestamp' in chunk.columns and dataset_type != 'MSRTMCR':
                #    chunk['timestamp'] = pd.to_datetime(chunk['timestamp'], unit='ms')

                # 转为字典列表
                records = chunk.to_dict(orient='records')
                
                # 3. 批量高并发写入 (Bulk Insert)
                try:
                    db.session.bulk_insert_mappings(model, records)
                    db.session.commit()  # 提交该批次的事务
                    total_inserted += len(records)
                    logger.info(f"Inserted {total_inserted} records into {model.__tablename__}...")
                except Exception as e:
                    # 单个 chunk 发生错误则回滚该批次
                    db.session.rollback()
                    errors += len(records)
                    logger.error(f"Error inserting chunk in {abs_file_path}: {str(e)}")
                    # TODO: 若需要极致容错，这里可以降级为逐行检查插入或者写入错误日志流
                    
            return {"status": "success", "inserted": total_inserted, "errors": errors}
            
        except Exception as e:
            logger.error(f"Ingestion process failed for {file_path}: {str(e)}")
            raise
