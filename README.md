# 🎮 浏览器远程控制系统

一个强大的浏览器远程控制系统，通过Python GUI界面发送指令来操作浏览器。

## ✨ 功能特性

### 🌐 标签页控制
- 打开新网页
- 获取所有标签页信息
- 获取当前标签页信息
- 关闭指定标签页

### 🤖 自动化任务
- 登录流程自动化（开发中）
- 创建项目自动化（开发中）
- 创建OAuth自动化（开发中）
- 创建AIStudio密钥自动化（开发中）

### ⚡ 高级功能
- 执行自定义JavaScript代码
- 页面截图
- 实时日志显示
- WebSocket实时通信

## 📁 项目结构

```
goole/
├── browser-extension/      # 浏览器插件
│   ├── manifest.json       # 插件配置文件
│   ├── background.js       # 后台脚本
│   ├── content.js          # 内容脚本
│   ├── popup.html          # 弹出页面
│   └── popup.js            # 弹出页面脚本
├── server.py               # WebSocket服务器
├── gui.py                  # GUI控制界面
├── requirements.txt        # Python依赖
└── README.md              # 说明文档
```

## 🚀 快速开始

### 1. 安装Python依赖

```bash
pip install -r requirements.txt
```

### 2. 启动WebSocket服务器

```bash
python server.py
```

你会看到类似输出：
```
==================================================
🚀 浏览器控制服务器启动中...
==================================================
📡 WebSocket服务器地址: ws://localhost:8765
🌐 等待浏览器插件和GUI连接...
==================================================
```

### 3. 安装浏览器插件

#### Chrome/Edge浏览器：

1. 打开浏览器，访问 `chrome://extensions/` (Chrome) 或 `edge://extensions/` (Edge)
2. 开启右上角的"开发者模式"
3. 点击"加载已解压的扩展程序"
4. 选择 `browser-extension` 文件夹
5. 插件安装成功后，会显示"浏览器远程控制"图标

### 4. 启动GUI控制界面

```bash
python gui.py
```

## 🎨 使用说明

### GUI界面功能

1. **状态指示器**
   - 🟢 绿色：已连接
   - 🔴 红色：未连接

2. **标签页控制**
   - 输入网址后点击"🌐 打开网页"
   - 点击"📋 获取所有标签"查看所有打开的标签页
   - 点击"📍 当前标签信息"获取当前激活的标签页信息

3. **自动化任务**
   - 🔐 登录流程：自动化登录操作（开发中）
   - 📁 创建项目：自动创建项目流程（开发中）
   - 🔑 创建OAuth：自动创建OAuth配置（开发中）
   - 🎯 创建AIStudio密钥：自动创建AI密钥（开发中）

4. **高级操作**
   - 执行自定义JavaScript代码
   - 截取当前页面截图
   - 获取页面HTML内容

### 示例操作

#### 1. 打开网页
```
# 在GUI中：
1. URL输入框：https://www.baidu.com
2. 点击"🌐 打开网页"
3. 自动在浏览器中打开指定网页
```

#### 2. 执行自定义JavaScript
```javascript
// 在JavaScript输入框中：
const title = document.title;
const url = window.location.href;
alert(`当前页面：${title}\n地址：${url}`);
return {title, url};
```

## 🔧 技术架构

### 通信流程

```
┌─────────────┐          ┌──────────────┐          ┌─────────────┐
│   GUI界面   │ ◄──────► │ WebSocket    │ ◄──────► │ 浏览器插件  │
│  (Python)   │          │   服务器     │          │ (JavaScript)│
└─────────────┘          └──────────────┘          └─────────────┘
     ctk GUI                Python                    Chrome API
```

### 技术栈

- **前端（浏览器插件）**
  - Chrome Extension Manifest V3
  - WebSocket客户端
  - Chrome Tabs API
  - Chrome Scripting API

- **后端（Python）**
  - websockets - WebSocket服务器
  - asyncio - 异步IO处理
  - json - 消息序列化

- **GUI界面**
  - customtkinter - 现代化UI框架
  - threading - 多线程处理
  - asyncio - 异步WebSocket客户端

## 📋 支持的命令

| 命令 | 参数 | 说明 |
|------|------|------|
| `openTab` | `url` | 打开新标签页 |
| `closeTab` | `tabId` | 关闭指定标签页 |
| `getCurrentTab` | - | 获取当前标签页信息 |
| `getAllTabs` | - | 获取所有标签页 |
| `getPageContent` | `tabId` | 获取页面内容 |
| `executeScript` | `tabId, code` | 执行JavaScript |
| `screenshot` | - | 截取当前页面 |

## 🛠️ 高级配置

### 修改WebSocket端口

在以下文件中修改端口号（默认8765）：

1. `server.py`：
```python
async with websockets.serve(handle_client, "localhost", 8765):
```

2. `browser-extension/background.js`：
```javascript
let wsUrl = 'ws://localhost:8765';
```

3. `gui.py`：
```python
uri = "ws://localhost:8765"
```

### 自定义插件图标

将图标文件放入 `browser-extension/` 目录：
- `icon16.png` (16x16)
- `icon48.png` (48x48)
- `icon128.png` (128x128)

## 🎯 常见问题

### Q: 浏览器插件无法连接服务器？
A: 确保：
1. WebSocket服务器已启动（运行 `python server.py`）
2. 端口8765未被占用
3. 防火墙允许本地连接

### Q: GUI界面显示服务器未连接？
A: 检查：
1. 服务器是否运行
2. 端口配置是否一致
3. 查看控制台错误信息

### Q: 无法操作页面元素？
A: 检查：
1. CSS选择器是否正确
2. 标签页ID是否正确
3. 页面是否完全加载
4. 某些页面可能有CSP限制

## 📝 开发建议

### 添加新命令

1. 在 `background.js` 的 `handleCommand` 函数中添加新的case
2. 在 `gui.py` 中添加对应的按钮和方法
3. 在 `server.py` 中添加必要的消息处理（如需要）

### 调试技巧

1. **浏览器插件调试**
   - 打开 `chrome://extensions/`
   - 点击插件的"检查视图"查看控制台

2. **服务器调试**
   - 查看服务器控制台输出
   - 所有消息都会记录时间戳

3. **GUI调试**
   - 查看操作日志面板
   - 检查Python控制台错误

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📧 联系方式

如有问题，请提交Issue。

---

**享受远程控制浏览器的乐趣！** 🚀

