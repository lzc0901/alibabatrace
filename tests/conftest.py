import pytest
import os
from app import create_app
from app.extensions import db as _db


@pytest.fixture(scope='session')
def app():
    """创建测试用 Flask 应用实例（使用 SQLite 内存库，测试间完全隔离）"""
    test_app = create_app('testing')
    yield test_app


@pytest.fixture(scope='function')
def client(app):
    """提供 Flask 测试客户端"""
    with app.test_client() as c:
        yield c


@pytest.fixture(scope='function')
def app_ctx(app):
    """提供 Flask 应用上下文"""
    with app.app_context():
        _db.create_all()
        yield
        _db.session.remove()
        _db.drop_all()
