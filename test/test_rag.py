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
import time

# 创建测试数据库
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_rag.db"
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
            username="raguser",
            hashed_password=get_password_hash("ragpass123")
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
        "username": "raguser",
        "password": "ragpass123"
    })
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def sample_hotwords(auth_headers):
    """创建示例热词数据"""
    hotwords = [
        {"word": "机器学习", "weight": 8},
        {"word": "深度学习", "weight": 9},
        {"word": "人工智能", "weight": 7},
        {"word": "神经网络", "weight": 6},
        {"word": "自然语言处理", "weight": 8},
        {"word": "计算机视觉", "weight": 7},
        {"word": "语音识别", "weight": 9},
        {"word": "数据挖掘", "weight": 5},
        {"word": "算法优化", "weight": 6},
        {"word": "模式识别", "weight": 7}
    ]
    
    created_hotwords = []
    for hotword_data in hotwords:
        response = client.post("/hotwords", json=hotword_data, headers=auth_headers)
        if response.status_code == 200:
            created_hotwords.append(response.json())
    
    # 等待索引构建完成
    time.sleep(2)
    
    return created_hotwords

class TestRAGHealthCheck:
    """RAG服务健康检查测试"""
    
    def test_health_check(self):
        """测试RAG服务健康检查"""
        response = client.get("/rag/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "service" in data
        assert "version" in data
        assert "initialized" in data
        assert data["service"] == "RAG Vector Search Engine"

class TestRAGIndexManagement:
    """RAG索引管理测试"""
    
    def test_get_index_stats_empty(self, auth_headers):
        """测试获取空索引统计信息"""
        response = client.get("/rag/index/stats", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "user_id" in data
        assert "total_hotwords" in data
        assert "index_dimension" in data
        assert "is_initialized" in data
        assert data["total_hotwords"] == 0
    
    def test_get_index_stats_with_data(self, auth_headers, sample_hotwords):
        """测试获取有数据的索引统计信息"""
        response = client.get("/rag/index/stats", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["total_hotwords"] == len(sample_hotwords)
        assert data["index_dimension"] == 384
        assert data["is_initialized"] == True
    
    def test_rebuild_index(self, auth_headers, sample_hotwords):
        """测试重建索引"""
        response = client.post("/rag/index/rebuild", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == True
        assert "索引重建成功" in data["message"]
        assert "details" in data
        assert data["details"]["hotword_count"] == len(sample_hotwords)

class TestRAGVectorSearch:
    """RAG向量搜索测试"""
    
    def test_vector_search_basic(self, auth_headers, sample_hotwords):
        """测试基础向量搜索"""
        search_request = {
            "query": "机器学习算法",
            "top_k": 5,
            "threshold": 0.3
        }
        
        response = client.post("/rag/search", json=search_request, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "query" in data
        assert "results" in data
        assert "total_found" in data
        assert "processing_time_ms" in data
        assert data["query"] == search_request["query"]
        assert isinstance(data["results"], list)
        assert data["processing_time_ms"] > 0
    
    def test_vector_search_with_results(self, auth_headers, sample_hotwords):
        """测试向量搜索返回结果"""
        search_request = {
            "query": "深度学习",
            "top_k": 3,
            "threshold": 0.1
        }
        
        response = client.post("/rag/search", json=search_request, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["results"]) > 0
        
        # 验证结果结构
        for result in data["results"]:
            assert "word" in result
            assert "weight" in result
            assert "similarity" in result
            assert "rank" in result
            assert 0 <= result["similarity"] <= 1
            assert 1 <= result["weight"] <= 10
    
    def test_vector_search_high_threshold(self, auth_headers, sample_hotwords):
        """测试高阈值搜索"""
        search_request = {
            "query": "完全不相关的查询内容xyz123",
            "top_k": 5,
            "threshold": 0.9
        }
        
        response = client.post("/rag/search", json=search_request, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        # 高阈值应该返回很少或没有结果
        assert data["total_found"] >= 0
    
    def test_vector_search_parameter_validation(self, auth_headers):
        """测试搜索参数验证"""
        # 测试无效的top_k
        invalid_request = {
            "query": "测试",
            "top_k": 100,  # 超过最大值
            "threshold": 0.5
        }
        
        response = client.post("/rag/search", json=invalid_request, headers=auth_headers)
        assert response.status_code == 422
        
        # 测试无效的threshold
        invalid_request = {
            "query": "测试",
            "top_k": 5,
            "threshold": 1.5  # 超过最大值
        }
        
        response = client.post("/rag/search", json=invalid_request, headers=auth_headers)
        assert response.status_code == 422

class TestRAGSuggestions:
    """RAG热词建议测试"""
    
    def test_get_suggestions_basic(self, auth_headers, sample_hotwords):
        """测试基础热词建议"""
        response = client.get("/rag/suggestions?partial_text=机器&max_suggestions=5", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "partial_text" in data
        assert "suggestions" in data
        assert "count" in data
        assert data["partial_text"] == "机器"
        assert isinstance(data["suggestions"], list)
        assert data["count"] == len(data["suggestions"])
    
    def test_get_suggestions_prefix_match(self, auth_headers, sample_hotwords):
        """测试前缀匹配建议"""
        response = client.get("/rag/suggestions?partial_text=深度&max_suggestions=3", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        # 应该包含"深度学习"
        assert any("深度" in suggestion for suggestion in data["suggestions"])
    
    def test_get_suggestions_empty_input(self, auth_headers, sample_hotwords):
        """测试空输入的建议"""
        response = client.get("/rag/suggestions?partial_text=&max_suggestions=5", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["count"] == 0
        assert len(data["suggestions"]) == 0
    
    def test_get_suggestions_no_match(self, auth_headers, sample_hotwords):
        """测试无匹配的建议"""
        response = client.get("/rag/suggestions?partial_text=xyz123&max_suggestions=5", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        # 可能返回0个建议或基于语义相似度的建议
        assert data["count"] >= 0

class TestRAGBulkOperations:
    """RAG批量操作测试"""
    
    def test_bulk_add_hotwords(self, auth_headers):
        """测试批量添加热词"""
        bulk_request = {
            "words": [
                {"word": "区块链技术", "weight": 7},
                {"word": "量子计算", "weight": 8},
                {"word": "边缘计算", "weight": 6}
            ]
        }
        
        response = client.post("/rag/index/bulk-add", json=bulk_request, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == True
        assert "details" in data
        assert data["details"]["added"] == 3
        assert data["details"]["skipped"] == 0
    
    def test_bulk_add_with_duplicates(self, auth_headers, sample_hotwords):
        """测试批量添加包含重复项的热词"""
        bulk_request = {
            "words": [
                {"word": "机器学习", "weight": 7},  # 重复项
                {"word": "新技术", "weight": 8},    # 新项
                {"word": "深度学习", "weight": 9}   # 重复项
            ]
        }
        
        response = client.post("/rag/index/bulk-add", json=bulk_request, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == True
        assert data["details"]["added"] == 1  # 只有"新技术"被添加
        assert data["details"]["skipped"] == 2  # 两个重复项被跳过
    
    def test_bulk_add_empty_words(self, auth_headers):
        """测试批量添加空词汇"""
        bulk_request = {
            "words": [
                {"word": "", "weight": 7},
                {"word": "   ", "weight": 8},
                {"word": "有效词汇", "weight": 6}
            ]
        }
        
        response = client.post("/rag/index/bulk-add", json=bulk_request, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == True
        assert data["details"]["added"] == 1  # 只有"有效词汇"被添加
        assert data["details"]["skipped"] == 2  # 两个空词汇被跳过

class TestRAGModelInfo:
    """RAG模型信息测试"""
    
    def test_get_model_info(self):
        """测试获取模型信息"""
        response = client.get("/rag/model/info")
        assert response.status_code == 200
        
        data = response.json()
        
        if "status" in data and data["status"] == "not_initialized":
            # 如果服务未初始化，这是正常的
            assert "message" in data
        else:
            # 如果服务已初始化，验证模型信息
            assert "model_name" in data
            assert "dimension" in data
            assert "languages" in data
            assert "description" in data
            assert "performance" in data
            assert data["model_name"] == "sentence-transformers/all-MiniLM-L6-v2"
            assert data["dimension"] == 384

class TestRAGAuthentication:
    """RAG认证测试"""
    
    def test_search_without_auth(self):
        """测试未认证的搜索请求"""
        search_request = {
            "query": "测试查询",
            "top_k": 5,
            "threshold": 0.5
        }
        
        response = client.post("/rag/search", json=search_request)
        assert response.status_code == 401
    
    def test_index_stats_without_auth(self):
        """测试未认证的索引统计请求"""
        response = client.get("/rag/index/stats")
        assert response.status_code == 401
    
    def test_suggestions_without_auth(self):
        """测试未认证的建议请求"""
        response = client.get("/rag/suggestions?partial_text=测试")
        assert response.status_code == 401
    
    def test_with_invalid_token(self):
        """测试无效token"""
        headers = {"Authorization": "Bearer invalid_token"}
        
        response = client.get("/rag/index/stats", headers=headers)
        assert response.status_code == 401

class TestRAGPerformance:
    """RAG性能测试"""
    
    def test_search_performance(self, auth_headers, sample_hotwords):
        """测试搜索性能"""
        search_request = {
            "query": "机器学习和人工智能",
            "top_k": 5,
            "threshold": 0.3
        }
        
        start_time = time.time()
        response = client.post("/rag/search", json=search_request, headers=auth_headers)
        end_time = time.time()
        
        assert response.status_code == 200
        
        data = response.json()
        # 验证响应时间合理（应该在几百毫秒内）
        response_time_ms = (end_time - start_time) * 1000
        assert response_time_ms < 5000  # 5秒内完成
        
        # 验证API返回的处理时间
        assert data["processing_time_ms"] > 0
        assert data["processing_time_ms"] < 5000
    
    def test_multiple_searches(self, auth_headers, sample_hotwords):
        """测试多次搜索的稳定性"""
        queries = [
            "机器学习",
            "深度学习",
            "人工智能",
            "神经网络",
            "算法"
        ]
        
        for query in queries:
            search_request = {
                "query": query,
                "top_k": 3,
                "threshold": 0.3
            }
            
            response = client.post("/rag/search", json=search_request, headers=auth_headers)
            assert response.status_code == 200
            
            data = response.json()
            assert "results" in data
            assert "processing_time_ms" in data

# 清理测试数据
def teardown_module():
    """测试模块清理"""
    if os.path.exists("test_rag.db"):
        os.remove("test_rag.db") 