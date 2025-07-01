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

### 数据库迁移操作

1. 生成迁移脚本（如有模型变更）：
   ```
   alembic revision --autogenerate -m "描述"
   ```
2. 应用迁移到数据库：
   ```
   alembic upgrade head
   ```
3. 回滚迁移（如需）：
   ```
   alembic downgrade -1
   ```

### CI/CD 说明

- 本项目已集成 GitHub Actions 自动化流程，包含后端依赖安装、代码风格检查、数据库迁移、自动化测试，前端依赖安装、代码风格检查、构建等环节。
- 每次 push 或 PR 到 main 分支时自动触发。
- 详见 `.github/workflows/ci.yml`. 