import pytest
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from asr_system_backend.app.main import app
from asr_system_backend.app.database import Base, get_db
from asr_system_backend.app.models import User, Hotword
from asr_system_backend.app.auth_service import get_password_hash
import tempfile

# 创建测试数据库
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建数据库表
Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

# 覆盖依赖
app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture
def test_user():
    """创建测试用户"""
    db = TestingSessionLocal()
    try:
        # 清理现有测试数据
        db.query(Hotword).delete()
        db.query(User).delete()
        db.commit()
        
        # 创建测试用户
        user = User(
            username="testuser",
            hashed_password=get_password_hash("testpass123")
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return user
    finally:
        db.close()

@pytest.fixture
def auth_headers(test_user):
    """获取认证头"""
    response = client.post("/auth/login", json={
        "username": "testuser",
        "password": "testpass123"
    })
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

class TestHotwordAPI:
    """热词管理API测试"""
    
    def test_create_hotword(self, auth_headers):
        """测试创建热词"""
        response = client.post("/hotwords", json={
            "word": "测试热词",
            "weight": 8
        }, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["word"] == "测试热词"
        assert data["weight"] == 8
        assert "id" in data
        assert "created_at" in data
    
    def test_create_hotword_invalid_weight(self, auth_headers):
        """测试创建热词 - 无效权重"""
        response = client.post("/hotwords", json={
            "word": "测试热词",
            "weight": 15  # 超出范围
        }, headers=auth_headers)
        
        assert response.status_code == 422
    
    def test_create_duplicate_hotword(self, auth_headers):
        """测试创建重复热词"""
        # 创建第一个热词
        client.post("/hotwords", json={
            "word": "重复热词",
            "weight": 5
        }, headers=auth_headers)
        
        # 尝试创建相同的热词
        response = client.post("/hotwords", json={
            "word": "重复热词",
            "weight": 6
        }, headers=auth_headers)
        
        assert response.status_code == 409
        assert "热词已存在" in response.json()["detail"]
    
    def test_get_user_hotwords(self, auth_headers):
        """测试获取用户热词列表"""
        # 创建几个热词
        for i in range(3):
            client.post("/hotwords", json={
                "word": f"热词{i}",
                "weight": 5
            }, headers=auth_headers)
        
        response = client.get("/hotwords", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert all("word" in item for item in data)
    
    def test_get_user_hotwords_pagination(self, auth_headers):
        """测试热词列表分页"""
        # 创建5个热词
        for i in range(5):
            client.post("/hotwords", json={
                "word": f"分页热词{i}",
                "weight": 5
            }, headers=auth_headers)
        
        # 测试分页
        response = client.get("/hotwords?skip=0&limit=2", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        
        response = client.get("/hotwords?skip=2&limit=2", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
    
    def test_update_hotword(self, auth_headers):
        """测试更新热词"""
        # 创建热词
        response = client.post("/hotwords", json={
            "word": "原始热词",
            "weight": 5
        }, headers=auth_headers)
        hotword_id = response.json()["id"]
        
        # 更新热词
        response = client.put(f"/hotwords/{hotword_id}", json={
            "word": "更新热词",
            "weight": 8
        }, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["word"] == "更新热词"
        assert data["weight"] == 8
    
    def test_update_nonexistent_hotword(self, auth_headers):
        """测试更新不存在的热词"""
        response = client.put("/hotwords/nonexistent", json={
            "word": "更新热词",
            "weight": 8
        }, headers=auth_headers)
        
        assert response.status_code == 404
    
    def test_delete_hotword(self, auth_headers):
        """测试删除热词"""
        # 创建热词
        response = client.post("/hotwords", json={
            "word": "待删除热词",
            "weight": 5
        }, headers=auth_headers)
        hotword_id = response.json()["id"]
        
        # 删除热词
        response = client.delete(f"/hotwords/{hotword_id}", headers=auth_headers)
        assert response.status_code == 200
        
        # 验证热词已被删除
        response = client.get("/hotwords", headers=auth_headers)
        data = response.json()
        assert not any(hw["id"] == hotword_id for hw in data)
    
    def test_delete_nonexistent_hotword(self, auth_headers):
        """测试删除不存在的热词"""
        response = client.delete("/hotwords/nonexistent", headers=auth_headers)
        assert response.status_code == 404
    
    def test_bulk_import_hotwords_csv(self, auth_headers):
        """测试批量导入热词 - CSV格式"""
        # 创建临时CSV文件
        csv_content = """热词1,5
热词2,8
热词3,3
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_file = f.name
        
        try:
            # 上传CSV文件
            with open(temp_file, 'rb') as f:
                response = client.post("/hotwords/import", 
                    files={"file": ("hotwords.csv", f, "text/csv")},
                    headers=auth_headers
                )
            
            assert response.status_code == 200
            data = response.json()
            assert data["added_count"] == 3
            assert data["skipped_count"] == 0
            
            # 验证热词已导入
            response = client.get("/hotwords", headers=auth_headers)
            hotwords = response.json()
            assert len(hotwords) == 3
            
        finally:
            os.unlink(temp_file)
    
    def test_bulk_import_hotwords_with_duplicates(self, auth_headers):
        """测试批量导入热词 - 包含重复项"""
        # 先创建一个热词
        client.post("/hotwords", json={
            "word": "已存在热词",
            "weight": 5
        }, headers=auth_headers)
        
        # 创建包含重复热词的CSV文件
        csv_content = """已存在热词,8
新热词1,6
新热词2,7
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write(csv_content)
            temp_file = f.name
        
        try:
            # 上传CSV文件
            with open(temp_file, 'rb') as f:
                response = client.post("/hotwords/import", 
                    files={"file": ("hotwords.csv", f, "text/csv")},
                    headers=auth_headers
                )
            
            assert response.status_code == 200
            data = response.json()
            assert data["added_count"] == 2  # 只添加了两个新热词
            assert data["skipped_count"] == 1  # 跳过了一个重复热词
            
        finally:
            os.unlink(temp_file)
    
    def test_bulk_import_invalid_file_format(self, auth_headers):
        """测试批量导入 - 无效文件格式"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("invalid content")
            temp_file = f.name
        
        try:
            # 上传无效格式文件
            with open(temp_file, 'rb') as f:
                response = client.post("/hotwords/import", 
                    files={"file": ("hotwords.pdf", f, "application/pdf")},
                    headers=auth_headers
                )
            
            assert response.status_code == 422
            
        finally:
            os.unlink(temp_file)
    
    def test_hotword_access_control(self, auth_headers):
        """测试热词访问控制"""
        # 创建另一个用户
        db = TestingSessionLocal()
        try:
            user2 = User(
                username="testuser2",
                hashed_password=get_password_hash("testpass123")
            )
            db.add(user2)
            db.commit()
        finally:
            db.close()
        
        # 获取第二个用户的token
        response = client.post("/auth/login", json={
            "username": "testuser2",
            "password": "testpass123"
        })
        user2_token = response.json()["access_token"]
        user2_headers = {"Authorization": f"Bearer {user2_token}"}
        
        # 用户1创建热词
        response = client.post("/hotwords", json={
            "word": "用户1热词",
            "weight": 5
        }, headers=auth_headers)
        hotword_id = response.json()["id"]
        
        # 用户2尝试访问用户1的热词
        response = client.put(f"/hotwords/{hotword_id}", json={
            "word": "恶意修改",
            "weight": 10
        }, headers=user2_headers)
        
        assert response.status_code == 403
        
        # 用户2尝试删除用户1的热词
        response = client.delete(f"/hotwords/{hotword_id}", headers=user2_headers)
        assert response.status_code == 403
    
    def test_hotword_limit(self, auth_headers):
        """测试热词数量限制"""
        # 创建100个热词（达到限制）
        for i in range(100):
            response = client.post("/hotwords", json={
                "word": f"限制测试热词{i}",
                "weight": 5
            }, headers=auth_headers)
            
            # 前100个应该成功
            if i < 100:
                assert response.status_code == 200
        
        # 尝试创建第101个热词
        response = client.post("/hotwords", json={
            "word": "超限热词",
            "weight": 5
        }, headers=auth_headers)
        
        assert response.status_code == 400
        assert "热词数量已达上限" in response.json()["detail"]

class TestHotwordAuthentication:
    """热词API认证测试"""
    
    def test_access_without_auth(self):
        """测试未认证访问"""
        response = client.get("/hotwords")
        assert response.status_code == 401
        
        response = client.post("/hotwords", json={
            "word": "测试热词",
            "weight": 5
        })
        assert response.status_code == 401
    
    def test_access_with_invalid_token(self):
        """测试无效token访问"""
        headers = {"Authorization": "Bearer invalid_token"}
        
        response = client.get("/hotwords", headers=headers)
        assert response.status_code == 401
        
        response = client.post("/hotwords", json={
            "word": "测试热词",
            "weight": 5
        }, headers=headers)
        assert response.status_code == 401

# 清理测试数据
def teardown_module():
    """测试模块清理"""
    if os.path.exists("test.db"):
        os.remove("test.db") 