from flask import Flask
from config import config_map
from app.extensions import db, migrate
from app import models  

def create_app(config_name="default"):
    app = Flask(__name__)
    app.config.from_object(config_map[config_name])

    # 初始化扩展
    db.init_app(app)
    migrate.init_app(app, db)

    # 注册蓝图 (CSV导入与任务检测相关 API)
    from app.api import api_bp
    app.register_blueprint(api_bp, url_prefix="/api/v1")

    @app.route("/health")
    def health_check():
        return {"status": "ok"}

    return app

