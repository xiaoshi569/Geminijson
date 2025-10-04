# 🔑 创建OAuth功能使用说明

## ✨ 功能概述

自动从projects.txt读取项目信息，创建OAuth同意屏幕和Web应用客户端，完全照搬参考项目的实现。

## 🚀 快速开始

### 1. 前置条件

✅ **已创建项目**  
- 必须先使用"创建项目"功能
- `projects.txt`中有项目ID和编号
- 格式：`project-id(project-number)`

✅ **已配置账号文件**  
- 创建`账号.txt`文件
- 格式：`账号邮箱|密码|辅助邮箱`
- 示例：`user@gmail.com|password123|backup@hotmail.com`
- 说明：
  - 账号邮箱：作为OAuth同意屏幕的支持邮箱
  - 辅助邮箱：作为开发者邮箱（如果没有，使用账号邮箱）

✅ **已登录Google账号**（可选）  
- 如果`账号.txt`不存在，会尝试从浏览器API获取
- 浏览器中已登录Google账号
- 已访问 https://console.cloud.google.com/

✅ **浏览器插件已连接**  
- GUI界面显示：🟢 浏览器: 已连接

### 2. 使用步骤

1. **启动系统**
   ```bash
   python gui.py
   ```

2. **点击"创建OAuth"按钮**
   - 在"🤖 自动化任务"区域
   - 点击"🔑 创建OAuth"

3. **系统自动执行**
   ```
   ✅ 步骤1: 获取浏览器Cookie
   ✅ 步骤2: 读取项目信息（从projects.txt）
   ✅ 步骤3: 获取用户邮箱（优先从账号.txt读取）
      - 优先从账号.txt读取邮箱
      - 支持邮箱：账号邮箱
      - 开发者邮箱：辅助邮箱（如果没有则使用账号邮箱）
      - 如果账号.txt不存在，尝试从API获取
   ✅ 步骤4: 检查OAuth同意屏幕
   ✅ 步骤5: 创建OAuth同意屏幕（如需要）
   ✅ 步骤6: 创建OAuth Web客户端
   ✅ 保存凭证到oauth_client.txt
   ```

4. **获取OAuth凭证**
   - 打开 `oauth_client.txt`
   - 查看客户端ID和密钥

## 📋 工作流程详解

### 步骤1: 读取项目信息

从`projects.txt`自动读取：
```
projectwabju-574079(261664217751)
```

解析为：
- 项目ID: `projectwabju-574079`
- 项目编号: `261664217751`

### 步骤2: 获取用户邮箱

通过两种方法获取：
1. Google OAuth2 UserInfo API
2. Google Console GraphQL API

用于创建OAuth同意屏幕的支持邮箱。

### 步骤3: 检查OAuth Brand

检查项目是否已有OAuth同意屏幕：
- 如果存在：跳过创建
- 如果不存在：创建新的

### 步骤4: 创建OAuth同意屏幕

**参数（照搬参考项目）：**
- 应用名称：随机生成（智能助手、数据分析平台等）
- 支持邮箱：当前用户邮箱
- 可见性：EXTERNAL（外部）
- 发布状态：TESTING（测试中）

### 步骤5: 创建OAuth Web客户端

**参数（照搬参考项目）：**
- 客户端类型：WEB
- 显示名称：Web客户端
- 重定向URI：http://localhost
- Brand ID：项目编号

### 步骤6: 保存凭证

保存到`oauth_client.txt`：
```
客户端ID: 123456789.apps.googleusercontent.com
客户端密钥: GOCSPX-xxxxxxxxxxxxx
重定向URI: http://localhost
```

## 📊 输出文件

### oauth_client.txt

```
客户端ID: 123456789-xxxxxxx.apps.googleusercontent.com
客户端密钥: GOCSPX-xxxxxxxxxxxxxxxx
重定向URI: http://localhost
```

**用途：**
- 调用Google API
- 实现OAuth2.0授权流程
- 获取用户授权令牌

## ⚠️ 常见问题

### Q1: "无法从projects.txt读取项目信息"

**原因：**
- `projects.txt`不存在
- 文件为空
- 格式不正确

**解决：**
1. 先运行"创建项目"功能
2. 确认`projects.txt`存在且格式正确：
   ```
   project-id(project-number)
   ```

### Q2: "无法获取当前用户邮箱"

**原因：**
- `账号.txt`文件不存在或格式错误
- 未登录Google账号
- Cookie已过期

**解决：**
1. **首选方案：创建账号.txt文件**
   ```
   格式：账号邮箱|密码|辅助邮箱
   示例：user@gmail.com|password123|backup@hotmail.com
   
   注意：
   - 使用 | 分隔符
   - 如果没有辅助邮箱，可以省略或留空
   - 示例：user@gmail.com|password123|
   ```

2. **备选方案：使用API获取**
   - 访问 https://console.cloud.google.com/
   - 确保已登录
   - 刷新浏览器插件
   - 重试创建OAuth

### Q3: "OAuth同意屏幕创建失败"

**原因：**
- 项目配额限制
- 权限不足
- API未启用

**解决：**
1. 访问 https://console.cloud.google.com/apis/credentials/consent
2. 手动检查OAuth同意屏幕设置
3. 确认项目权限

### Q4: "OAuth客户端创建失败"

**原因：**
- OAuth同意屏幕未配置
- 客户端数量达到上限

**解决：**
1. 手动访问 https://console.cloud.google.com/apis/credentials
2. 检查现有客户端
3. 删除不需要的客户端后重试

## 🎯 核心API（照搬参考项目）

### 1. 检查Brand是否存在

```python
url = "https://cloudconsole-pa.clients6.google.com/v3/entityServices/OauthEntityService/schemas/OAUTH_GRAPHQL:batchGraphql"

GraphQL操作：ListBrands
查询：projects/{project_number}的所有Brand
```

### 2. 创建OAuth Brand

```python
GraphQL操作：CreateBrandInfo
参数：
- projectNumber: 项目编号
- displayName: 应用名称
- supportEmail: 支持邮箱
- visibility: EXTERNAL
- publishState: TESTING
```

### 3. 创建OAuth Client

```python
GraphQL操作：CreateClient
参数：
- parent: projects/{project_number}
- clientType: WEB
- displayName: Web客户端
- redirectUris: ["http://localhost"]
```

## 🔗 相关链接

- **Google Cloud Console:** https://console.cloud.google.com/
- **API凭据管理:** https://console.cloud.google.com/apis/credentials
- **OAuth同意屏幕:** https://console.cloud.google.com/apis/credentials/consent
- **API库:** https://console.cloud.google.com/apis/library

## 💡 最佳实践

1. **先创建项目再创建OAuth**
   - 确保`projects.txt`有效
   - 项目状态正常

2. **保管好OAuth凭证**
   - `oauth_client.txt`包含敏感信息
   - 不要上传到公开仓库
   - 定期更换密钥

3. **测试OAuth流程**
   - 使用生成的客户端ID
   - 实现OAuth2.0授权流程
   - 获取访问令牌

4. **监控API配额**
   - OAuth客户端数量有限
   - 定期清理不用的客户端

## 🎓 技术实现

完全照搬参考项目（goolejson/automation_gui.py）的实现：
- ✅ `_get_projects_from_file()` - 读取项目
- ✅ `_get_current_user_email()` - 获取邮箱
- ✅ `_check_oauth_brand_exists()` - 检查Brand
- ✅ `_create_oauth_brand()` - 创建Brand
- ✅ `_create_oauth_client()` - 创建Client

**零猜测，100%复用参考项目的真实实现！**

---

**祝使用愉快！** 🎉

