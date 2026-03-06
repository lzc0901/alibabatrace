from flask import Blueprint, request, jsonify
import uuid
import threading
from app.services.ingestion_service import IngestionService
from app.extensions import db
from flask import current_app

api_bp = Blueprint('api', __name__)

# 使用一个简单的内存字典来模拟任务状态存储 (生产环境中可换成 Redis)
# 结构: task_id -> {"status": "pending|running|success|failed", "inserted": 0, "errors": 0}
TASK_STATUS_STORE = {}

def bg_ingestion_task(app, task_id, dataset_type, file_path, batch_size):
    """
    后台线程执行的入库任务
    """
    with app.app_context():
        TASK_STATUS_STORE[task_id]['status'] = 'running'
        try:
            result = IngestionService.ingest_csv(dataset_type, file_path, batch_size)
            TASK_STATUS_STORE[task_id].update({
                'status': 'success',
                'inserted': result['inserted'],
                'errors': result['errors']
            })
        except Exception as e:
            TASK_STATUS_STORE[task_id].update({
                'status': 'failed',
                'error_msg': str(e)
            })

@api_bp.route('/ingestion/start', methods=['POST'])
def start_ingestion():
    """
    触发数据导入控制的能力
    Input (JSON): { "dataset_type": "CallGraph", "file_path": "data/CallGraph/CallGraph_0.csv", "batch_size": 10000 }
    """
    # 鉴权中间件在实际项目中会被引入 (e.g. @admin_required)
    data = request.get_json()
    
    dataset_type = data.get('dataset_type')
    file_path = data.get('file_path')
    batch_size = data.get('batch_size', 5000)
    
    if not dataset_type or not file_path:
        return jsonify({"error": "Missing required parameters: dataset_type or file_path"}), 400

    task_id = str(uuid.uuid4())
    TASK_STATUS_STORE[task_id] = {
        "status": "pending",
        "inserted": 0,
        "errors": 0
    }

    # 启动后台线程执行（避免阻塞 API 返回，应对大体量 CSV 落库）
    app = current_app._get_current_object()
    thread = threading.Thread(
        target=bg_ingestion_task, 
        args=(app, task_id, dataset_type, file_path, batch_size)
    )
    thread.start()

    return jsonify({"task_id": task_id, "status": "running"}), 202

@api_bp.route('/ingestion/status/<task_id>', methods=['GET'])
def get_ingestion_status(task_id):
    """
    轮询返回任务运行状态、完成行数和错误行数统计。
    """
    task_info = TASK_STATUS_STORE.get(task_id)
    if not task_info:
        return jsonify({"error": "Task not found"}), 404
        
    return jsonify(task_info), 200
