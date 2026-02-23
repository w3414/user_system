from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import json
import os
import shutil
from datetime import datetime

app = FastAPI(title="用户管理系统", version="2.0")

# 用户数据模型
class User(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool = True

class UserCreate(BaseModel):
    username: str
    email: str
    full_name: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool = True

# 数据文件路径
DATA_FILE = "users_data.json"

def load_users():
    """从文件加载用户数据"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                users = []
                for user_dict in data:
                    users.append(User(**user_dict))
                return users
            except json.JSONDecodeError:
                return []
    return []

def save_users(users):
    """保存用户数据到文件"""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        users_dict = [user.dict() for user in users]
        json.dump(users_dict, f, ensure_ascii=False, indent=2)

def get_next_id(users):
    """获取下一个可用的用户ID"""
    if not users:
        return 1
    return max(user.id for user in users) + 1

# 加载初始数据
users_db = load_users()

@app.get("/")
def read_root():
    return {
        "message": "欢迎使用用户管理系统增强版",
        "version": "2.0",
        "total_users": len(users_db),
        "endpoints": [gi
            {"method": "GET", "path": "/", "description": "首页"},
            {"method": "GET", "path": "/users", "description": "获取用户列表（支持分页和搜索）"},
            {"method": "POST", "path": "/users", "description": "创建新用户"},
            {"method": "GET", "path": "/users/{user_id}", "description": "根据ID获取用户"},
            {"method": "PUT", "path": "/users/{user_id}", "description": "更新用户信息"},
            {"method": "DELETE", "path": "/users/{user_id}", "description": "删除用户"},
            {"method": "GET", "path": "/stats", "description": "获取统计信息"},
            {"method": "POST", "path": "/backup", "description": "创建数据备份"}
        ]
    }

@app.get("/users")
def get_all_users(skip: int = 0, limit: int = 100, search: Optional[str] = None):
    """获取用户列表，支持分页和搜索"""
    result = users_db
    
    # 搜索功能
    if search:
        search = search.lower()
        result = [
            user for user in users_db
            if (search in user.username.lower() or
                search in user.email.lower() or
                (user.full_name and search in user.full_name.lower()) or
                (user.phone and search in user.phone))
        ]
    
    # 分页功能
    paginated_users = result[skip:skip + limit]
    
    return {
        "total": len(result),
        "skip": skip,
        "limit": limit,
        "users": paginated_users
    }

@app.get("/users/{user_id}")
def get_user(user_id: int):
    for user in users_db:
        if user.id == user_id:
            return user
    raise HTTPException(status_code=404, detail="用户不存在")

@app.post("/users")
def create_user(user_data: UserCreate):
    # 检查用户名是否已存在
    for user in users_db:
        if user.username == user_data.username:
            raise HTTPException(status_code=400, detail="用户名已存在")
        if user.email == user_data.email:
            raise HTTPException(status_code=400, detail="邮箱已存在")
    
    # 创建新用户
    new_id = get_next_id(users_db)
    new_user = User(
        id=new_id,
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        phone=user_data.phone,
        is_active=user_data.is_active
    )
    
    users_db.append(new_user)
    save_users(users_db)
    return {"message": "用户创建成功", "user": new_user}

@app.put("/users/{user_id}")
def update_user(user_id: int, user_data: UserCreate):
    for i, user in enumerate(users_db):
        if user.id == user_id:
            # 检查新用户名是否被其他人使用
            for other_user in users_db:
                if other_user.id != user_id and other_user.username == user_data.username:
                    raise HTTPException(status_code=400, detail="用户名已被其他用户使用")
                if other_user.id != user_id and other_user.email == user_data.email:
                    raise HTTPException(status_code=400, detail="邮箱已被其他用户使用")
            
            # 更新用户信息
            users_db[i] = User(
                id=user_id,
                username=user_data.username,
                email=user_data.email,
                full_name=user_data.full_name,
                phone=user_data.phone,
                is_active=user_data.is_active
            )
            save_users(users_db)
            return {"message": "用户更新成功", "user": users_db[i]}
    
    raise HTTPException(status_code=404, detail="用户不存在")

@app.delete("/users/{user_id}")
def delete_user(user_id: int):
    for i, user in enumerate(users_db):
        if user.id == user_id:
            deleted_user = users_db.pop(i)
            save_users(users_db)
            return {"message": "用户删除成功", "user": deleted_user}
    
    raise HTTPException(status_code=404, detail="用户不存在")

@app.get("/users/search/{keyword}")
def search_users(keyword: str):
    results = []
    for user in users_db:
        if (keyword.lower() in user.username.lower() or 
            keyword.lower() in user.email.lower() or
            (user.full_name and keyword.lower() in user.full_name.lower())):
            results.append(user)
    return results

@app.get("/users/active")
def get_active_users():
    return [user for user in users_db if user.is_active]

@app.get("/stats")
def get_stats():
    """获取系统统计信息"""
    total_users = len(users_db)
    active_users = sum(1 for user in users_db if user.is_active)
    
    # 按邮箱域名统计
    domain_stats = {}
    for user in users_db:
        domain = user.email.split('@')[-1]
        domain_stats[domain] = domain_stats.get(domain, 0) + 1
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "inactive_users": total_users - active_users,
        "email_domains": domain_stats,
        "created_date": datetime.now().isoformat()
    }

@app.post("/backup")
def create_backup():
    """创建数据备份"""
    if not os.path.exists("backups"):
        os.makedirs("backups")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"backups/users_backup_{timestamp}.json"
    
    # 复制当前数据文件
    shutil.copy2(DATA_FILE, backup_file)
    
    # 获取所有备份文件
    backups = []
    if os.path.exists("backups"):
        for file in os.listdir("backups"):
            if file.startswith("users_backup_"):
                file_path = os.path.join("backups", file)
                backups.append({
                    "name": file,
                    "size": os.path.getsize(file_path),
                    "created": datetime.fromtimestamp(os.path.getctime(file_path)).isoformat()
                })
    
    return {
        "message": "备份创建成功",
        "backup_file": backup_file,
        "total_backups": len(backups),
        "backups": sorted(backups, key=lambda x: x["created"], reverse=True)
    }

@app.get("/health")
def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "users_count": len(users_db),
        "data_file_exists": os.path.exists(DATA_FILE)
    }

if __name__ == "__main__":
    import uvicorn
    print("=" * 50)
    print("用户管理系统增强版启动中...")
    print(f"当前用户数量: {len(users_db)}")
    print(f"数据文件: {DATA_FILE}")
    print("访问 http://localhost:8000 查看首页")
    print("访问 http://localhost:8000/docs 查看API文档")
    print("=" * 50)
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)