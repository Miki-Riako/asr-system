## 用户认证API说明

### 注册
POST /auth/register
- 参数：username, password
- 返回：用户信息

### 登录
POST /auth/login
- 参数：username, password
- 返回：access_token（JWT令牌）

### 获取当前用户
GET /auth/me
- Header: Authorization: Bearer <access_token>
- 返回：当前用户信息

## 本地运行
1. 安装依赖：pip install -r requirements.txt
2. 启动服务：uvicorn app.main:app --reload
3. 访问API文档：http://localhost:8000/docs 