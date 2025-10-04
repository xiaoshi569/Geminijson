"""
现代化GUI界面 - 使用CustomTkinter
用于控制浏览器插件
"""
import asyncio
import json
import threading
import websockets
import subprocess
import sys
import os
import time
from tkinter import messagebox, scrolledtext
from typing import Optional
import customtkinter as ctk
from project_api import GoogleCloudProjectAPI
from oauth_api import GoogleOAuthAPI

class BrowserControlGUI:
    def __init__(self):
        self.ws = None
        self.loop = None
        self.ws_thread = None
        self.is_connected = False
        self.browser_connected = False
        self.server_process = None
        self.server_running = False
        
        # 项目创建相关
        self.project_api = GoogleCloudProjectAPI()
        self.oauth_api = GoogleOAuthAPI()
        self.pending_commands = {}  # 存储待响应的命令
        
        # 设置主题
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # 创建主窗口
        self.root = ctk.CTk()
        self.root.title("🎮 浏览器远程控制中心")
        self.root.geometry("900x700")
        
        self.setup_ui()
        
        # 延迟启动服务器（等待UI完全加载）
        self.root.after(500, self.auto_start_server)
        
    def setup_ui(self):
        """设置UI界面"""
        
        # 标题区域
        title_frame = ctk.CTkFrame(self.root)
        title_frame.pack(fill="x", padx=20, pady=20)
        
        title_label = ctk.CTkLabel(
            title_frame,
            text="🚀 浏览器远程控制中心",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=10)
        
        # 服务器控制区域
        server_control_frame = ctk.CTkFrame(title_frame)
        server_control_frame.pack(fill="x", pady=5)
        
        self.server_btn = ctk.CTkButton(
            server_control_frame,
            text="🚀 启动服务器",
            command=self.toggle_server,
            fg_color="#4CAF50",
            hover_color="#388E3C",
            width=150
        )
        self.server_btn.pack(side="left", padx=20, pady=5)
        
        self.server_port_label = ctk.CTkLabel(
            server_control_frame,
            text="端口: 8765",
            font=ctk.CTkFont(size=11)
        )
        self.server_port_label.pack(side="left", padx=10)
        
        self.show_log_btn = ctk.CTkButton(
            server_control_frame,
            text="📋 查看服务器日志",
            command=self.show_server_log,
            fg_color="#607D8B",
            hover_color="#455A64",
            width=120
        )
        self.show_log_btn.pack(side="left", padx=10)
        
        # 状态指示器
        self.status_frame = ctk.CTkFrame(title_frame)
        self.status_frame.pack(fill="x", pady=10)
        
        self.server_status = ctk.CTkLabel(
            self.status_frame,
            text="🔴 WebSocket: 未连接",
            font=ctk.CTkFont(size=12)
        )
        self.server_status.pack(side="left", padx=20)
        
        self.browser_status = ctk.CTkLabel(
            self.status_frame,
            text="🔴 浏览器: 未连接",
            font=ctk.CTkFont(size=12)
        )
        self.browser_status.pack(side="left", padx=20)
        
        # 主内容区域
        content_frame = ctk.CTkFrame(self.root)
        content_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # 左侧控制面板
        left_panel = ctk.CTkFrame(content_frame)
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # 标签页控制
        tab_control = ctk.CTkFrame(left_panel)
        tab_control.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            tab_control,
            text="📑 标签页控制",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=5)
        
        self.url_entry = ctk.CTkEntry(
            tab_control,
            placeholder_text="输入网址 (例如: https://www.baidu.com)"
        )
        self.url_entry.pack(fill="x", padx=10, pady=5)
        
        btn_frame1 = ctk.CTkFrame(tab_control, fg_color="transparent")
        btn_frame1.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkButton(
            btn_frame1,
            text="🌐 打开网页",
            command=self.open_tab,
            fg_color="#2196F3",
            hover_color="#1976D2"
        ).pack(side="left", expand=True, padx=2)
        
        ctk.CTkButton(
            btn_frame1,
            text="📋 获取所有标签",
            command=self.get_all_tabs,
            fg_color="#4CAF50",
            hover_color="#388E3C"
        ).pack(side="left", expand=True, padx=2)
        
        ctk.CTkButton(
            btn_frame1,
            text="📍 当前标签信息",
            command=self.get_current_tab,
            fg_color="#FF9800",
            hover_color="#F57C00"
        ).pack(side="left", expand=True, padx=2)
        
        # 自动化任务控制
        task_control = ctk.CTkFrame(left_panel)
        task_control.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            task_control,
            text="🤖 自动化任务",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=5)
        
        btn_frame2 = ctk.CTkFrame(task_control, fg_color="transparent")
        btn_frame2.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkButton(
            btn_frame2,
            text="🔐 登录流程",
            command=self.task_login,
            fg_color="#9C27B0",
            hover_color="#7B1FA2"
        ).pack(side="left", expand=True, padx=2)
        
        ctk.CTkButton(
            btn_frame2,
            text="📁 创建项目",
            command=self.task_create_project,
            fg_color="#E91E63",
            hover_color="#C2185B"
        ).pack(side="left", expand=True, padx=2)
        
        btn_frame3 = ctk.CTkFrame(task_control, fg_color="transparent")
        btn_frame3.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkButton(
            btn_frame3,
            text="🔑 创建OAuth",
            command=self.task_create_oauth,
            fg_color="#3F51B5",
            hover_color="#303F9F"
        ).pack(side="left", expand=True, padx=2)
        
        ctk.CTkButton(
            btn_frame3,
            text="🎯 创建AIStudio密钥",
            command=self.task_create_aistudio,
            fg_color="#009688",
            hover_color="#00796B"
        ).pack(side="left", expand=True, padx=2)
        
        # 高级操作
        advanced_control = ctk.CTkFrame(left_panel)
        advanced_control.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            advanced_control,
            text="⚡ 高级操作",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=5)
        
        btn_frame3 = ctk.CTkFrame(advanced_control, fg_color="transparent")
        btn_frame3.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkButton(
            btn_frame3,
            text="📄 获取页面内容",
            command=self.get_page_content,
            fg_color="#00BCD4",
            hover_color="#0097A7"
        ).pack(side="left", expand=True, padx=2)
        
        ctk.CTkButton(
            btn_frame3,
            text="📸 截图",
            command=self.screenshot,
            fg_color="#FF5722",
            hover_color="#E64A19"
        ).pack(side="left", expand=True, padx=2)
        
        # 自定义JavaScript
        js_control = ctk.CTkFrame(left_panel)
        js_control.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(
            js_control,
            text="💻 自定义JavaScript",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=5)
        
        self.js_text = ctk.CTkTextbox(js_control, height=100)
        self.js_text.pack(fill="both", expand=True, padx=10, pady=5)
        self.js_text.insert("1.0", "// 例如: alert('Hello from Python!');\nreturn document.title;")
        
        ctk.CTkButton(
            js_control,
            text="▶️ 执行JavaScript",
            command=self.execute_script,
            fg_color="#607D8B",
            hover_color="#455A64"
        ).pack(padx=10, pady=5)
        
        # 右侧日志面板
        right_panel = ctk.CTkFrame(content_frame)
        right_panel.pack(side="right", fill="both", expand=True)
        
        ctk.CTkLabel(
            right_panel,
            text="📝 操作日志",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=10)
        
        self.log_text = ctk.CTkTextbox(right_panel)
        self.log_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        ctk.CTkButton(
            right_panel,
            text="🗑️ 清空日志",
            command=self.clear_log,
            fg_color="#795548",
            hover_color="#5D4037"
        ).pack(padx=10, pady=10)
        
    def log(self, message):
        """添加日志"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert("end", f"[{timestamp}] {message}\n")
        self.log_text.see("end")
        
    def clear_log(self):
        """清空日志"""
        self.log_text.delete("1.0", "end")
        
    def send_command(self, command, params={}):
        """发送命令到浏览器"""
        if not self.is_connected:
            messagebox.showerror("错误", "未连接到服务器")
            return
            
        if not self.browser_connected:
            messagebox.showwarning("警告", "浏览器插件未连接")
            return
            
        message = {
            "command": command,
            "params": params
        }
        
        asyncio.run_coroutine_threadsafe(
            self.ws.send(json.dumps(message)),
            self.loop
        )
        
        self.log(f"📤 发送命令: {command}")
        
    def open_tab(self):
        """打开新标签页"""
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("警告", "请输入网址")
            return
            
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        self.send_command("openTab", {"url": url})
        
    def get_all_tabs(self):
        """获取所有标签页"""
        self.send_command("getAllTabs")
        
    def get_current_tab(self):
        """获取当前标签页信息"""
        self.send_command("getCurrentTab")
        
    def task_login(self):
        """自动化登录流程"""
        self.log("🔐 登录流程功能开发中...")
        messagebox.showinfo("提示", "登录流程功能正在开发中\n敬请期待！")
        
    def task_create_project(self):
        """自动化创建项目"""
        self.log("🚀 启动智能项目创建流程...")
        
        # 在新线程中执行，避免阻塞UI
        threading.Thread(target=self._create_project_workflow, daemon=True).start()
        
    def task_create_oauth(self):
        """自动化创建OAuth（照搬参考项目）"""
        self.log("🔑 启动OAuth创建流程...")
        threading.Thread(target=self._create_oauth_workflow, daemon=True).start()
        
    def task_create_aistudio(self):
        """自动化创建AIStudio密钥"""
        self.log("🎯 创建AIStudio密钥功能开发中...")
        messagebox.showinfo("提示", "创建AIStudio密钥功能正在开发中\n敬请期待！")
        
    def get_page_content(self):
        """获取页面内容"""
        tab_id = self.get_tab_id()
        self.send_command("getPageContent", {"tabId": tab_id})
        
    def screenshot(self):
        """截图"""
        self.send_command("screenshot")
        
    def execute_script(self):
        """执行自定义JavaScript"""
        code = self.js_text.get("1.0", "end-1c").strip()
        if not code:
            messagebox.showwarning("警告", "请输入JavaScript代码")
            return
            
        tab_id = self.get_tab_id()
        self.send_command("executeScript", {"tabId": tab_id, "code": code})
        
    def get_tab_id(self):
        """获取标签页ID（用于高级操作）"""
        # 高级操作可能需要指定tabId，这里返回None表示使用当前标签页
        return None
    
    # ========== 项目创建相关方法 ==========
    
    def _create_project_workflow(self):
        """完整的项目创建工作流"""
        try:
            # 步骤1: 获取Cookie
            self.log("📋 步骤1: 获取浏览器Cookie...")
            cookies = self._get_cookies_sync()
            
            if not cookies:
                self.log("❌ Cookie获取失败")
                self.root.after(0, lambda: messagebox.showerror("错误", "无法获取Cookie\n请确保:\n1. 浏览器插件已连接\n2. 已登录Google账号\n3. 已访问Google Cloud Console"))
                return
            
            # 设置Cookie到API
            if not self.project_api.set_cookies(cookies):
                self.log("❌ Cookie设置失败")
                return
            
            # 检查关键Cookie
            if 'SAPISID' not in self.project_api.cookies:
                self.log("❌ 缺少关键Cookie: SAPISID")
                self.root.after(0, lambda: messagebox.showerror("错误", "Cookie不完整\n请访问 https://console.cloud.google.com/\n并确保已登录"))
                return
            
            self.log(f"✅ Cookie获取成功 ({len(self.project_api.cookies)} 个)")
            
            # 步骤2: 生成项目信息
            self.log("📋 步骤2: 生成项目信息...")
            import random
            project_id = self.project_api.generate_project_id()
            project_name = f"Project{random.randint(1000, 9999)}"
            self.log(f"   项目名称: {project_name}")
            self.log(f"   项目ID: {project_id}")
            
            # 步骤3: 创建项目
            self.log("📋 步骤3: 调用API创建项目...")
            self.log("⏳ 请稍等，正在处理...")
            
            success, message, project_id, project_number = self.project_api.create_project(project_name, project_id)
            
            if success:
                self.log(f"✅ {message}")
                
                if not project_id:
                    self.log("⚠️ 未能从响应中提取项目ID")
                
                if project_number:
                    self.log(f"✅ 项目编号: {project_number}")
                else:
                    # 如果响应中没有，尝试查询
                    if project_id:
                        self.log("📋 步骤4: 查询项目编号...")
                        self.log("⏳ 等待项目创建完成...")
                        # 增加重试次数和初始等待时间，项目创建需要时间
                        project_number = self.project_api.get_project_number(project_id, max_retries=6, initial_delay=15)
                        
                        if project_number:
                            self.log(f"✅ 项目编号: {project_number}")
                        else:
                            project_number = "待查询"
                            self.log("⚠️ 暂时无法获取项目编号")
                    else:
                        project_number = "未知"
                        self.log("⚠️ 无法查询项目编号（缺少项目ID）")
                
                # 保存到文件
                if project_id:
                    self._save_project(project_id, project_number or "待查询")
                
                    self.log("=" * 50)
                    self.log("🎉 项目创建成功！")
                    self.log(f"📦 项目ID: {project_id}")
                    self.log(f"🔢 项目编号: {project_number or '待查询'}")
                    self.log("🌐 访问: https://console.cloud.google.com/")
                    self.log("=" * 50)
                else:
                    self.log("⚠️ 项目可能已创建，但未能获取完整信息")
                    self.log("💡 请访问 https://console.cloud.google.com/ 查看")
            else:
                self.log(f"❌ 创建失败: {message}")
                self.root.after(0, lambda: messagebox.showerror("失败", f"项目创建失败\n\n{message}"))
                
        except Exception as e:
            self.log(f"❌ 项目创建流程出错: {str(e)}")
            self.root.after(0, lambda: messagebox.showerror("错误", f"创建项目时出错:\n{str(e)}"))
    
    def _get_cookies_sync(self, timeout=10) -> Optional[str]:
        """同步获取Cookie（阻塞等待）"""
        try:
            # 生成命令ID
            command_id = f"getCookies_{int(time.time() * 1000)}"
            
            # 准备接收响应
            response_event = threading.Event()
            response_data = {'cookies': None}
            
            def handle_cookie_response(data):
                if data.get('command') == 'getCookies':
                    result = data.get('result', {})
                    if result.get('success'):
                        response_data['cookies'] = result.get('cookies')
                    response_event.set()
            
            # 临时注册响应处理器
            self.pending_commands[command_id] = handle_cookie_response
            
            # 发送命令
            self.send_command("getCookies", {})
            
            # 等待响应
            if response_event.wait(timeout):
                return response_data['cookies']
            else:
                self.log("⏱️ 获取Cookie超时")
                return None
                
        except Exception as e:
            self.log(f"获取Cookie出错: {e}")
            return None
        finally:
            # 清理
            if command_id in self.pending_commands:
                del self.pending_commands[command_id]
    
    def _save_project(self, project_id: str, project_number: str):
        """保存项目到文件（覆盖模式）"""
        try:
            with open('projects.txt', 'w', encoding='utf-8') as f:
                f.write(f"{project_id}({project_number})\n")
            self.log(f"💾 项目信息已保存到 projects.txt")
        except Exception as e:
            self.log(f"保存项目信息失败: {e}")
    
    def _create_oauth_workflow(self):
        """OAuth创建的完整工作流（照搬参考项目）"""
        try:
            # 步骤1: 获取Cookie
            self.log("📋 步骤1: 获取浏览器Cookie...")
            cookies = self._get_cookies_sync()
            
            if not cookies:
                self.log("❌ Cookie获取失败")
                self.root.after(0, lambda: messagebox.showerror("错误", "无法获取Cookie\n请确保:\n1. 浏览器插件已连接\n2. 已登录Google账号\n3. 已访问Google Cloud Console"))
                return
            
            # 设置Cookie到OAuth API
            if not self.oauth_api.set_cookies(cookies):
                self.log("❌ Cookie设置失败")
                return
            
            self.log(f"✅ Cookie获取成功")
            
            # 步骤2: 读取项目信息
            self.log("📋 步骤2: 读取项目信息...")
            project_info = self._read_project_from_file()
            
            if not project_info:
                self.log("❌ 无法读取项目信息")
                self.root.after(0, lambda: messagebox.showerror("错误", "无法从projects.txt读取项目信息\n请先创建项目"))
                return
            
            project_id = project_info.get('project_id')
            project_number = project_info.get('project_number')
            
            if not project_id or not project_number:
                self.log("❌ 项目信息不完整")
                return
            
            self.log(f"✅ 使用项目: {project_id} (编号: {project_number})")
            
            # 步骤3: 获取用户邮箱（优先从文件读取）
            self.log("📋 步骤3: 获取用户邮箱...")
            
            # 先从账号.txt读取
            account_email, auxiliary_email = self._read_email_from_file()
            
            # 优先使用辅助邮箱，如果没有则使用账号邮箱
            user_email = auxiliary_email if auxiliary_email else account_email
            developer_email = auxiliary_email if auxiliary_email else account_email
            
            # 如果文件读取失败，尝试从API获取
            if not user_email:
                self.log("   尝试从API获取邮箱...")
                user_email = self.oauth_api.get_current_user_email()
                developer_email = user_email
            
            if not user_email:
                self.log("❌ 无法获取用户邮箱")
                self.root.after(0, lambda: messagebox.showerror("错误", "无法获取用户邮箱\n请确保:\n1. 账号.txt文件存在且格式正确\n2. 或已登录Google账号"))
                return
            
            self.log(f"✅ 支持邮箱: {user_email}")
            if developer_email != user_email:
                self.log(f"✅ 开发者邮箱: {developer_email}")
            
            # 步骤4: 创建OAuth Brand（不检查，直接创建，如果已存在会忽略错误）
            self.log("📋 步骤4: 创建OAuth同意屏幕...")
            # 使用账号邮箱作为支持邮箱，辅助邮箱（或账号邮箱）作为开发者邮箱
            brand_created, operation_name = self.oauth_api.create_oauth_brand(
                project_number, 
                project_id, 
                account_email if account_email else user_email,  # 支持邮箱
                developer_email  # 开发者邮箱
            )
            
            # 无论Brand创建成功或失败（可能已存在），都继续创建Client
            if brand_created:
                if operation_name:
                    self.log(f"✅ OAuth同意屏幕创建已启动（异步操作）")
                    # Brand创建是异步的，等待5秒让其完成
                    self.log("⏳ 等待5秒让同意屏幕完全创建...")
                    time.sleep(5)
                else:
                    self.log("✅ OAuth同意屏幕已存在（跳过等待）")
            else:
                # Brand创建失败，通常是已存在，无需等待
                self.log("⚠️ OAuth同意屏幕可能已存在，继续创建客户端...")
            
            # 步骤5: 创建OAuth Client
            self.log("📋 步骤5: 创建OAuth Web客户端...")
            client_created, client_info = self.oauth_api.create_oauth_client(project_number, project_id)
            
            if not client_created or not client_info:
                self.log("❌ OAuth客户端创建失败")
                self.root.after(0, lambda: messagebox.showerror("失败", "OAuth客户端创建失败"))
                return
            
            # 保存OAuth凭证
            self._save_oauth_client(client_info)
            
            self.log("=" * 50)
            self.log("🎉 OAuth客户端创建成功！")
            self.log(f"📦 客户端ID: {client_info['client_id']}")
            if client_info.get('client_secret'):
                self.log(f"🔑 客户端密钥: {client_info['client_secret'][:20]}...")
            self.log(f"📝 显示名称: {client_info.get('display_name', '')}")
            self.log(f"💾 凭证已保存到: oauth_client.txt 和 oauth_client.json")
            self.log(f"🔗 管理页面: https://console.cloud.google.com/apis/credentials?project={project_id}")
            self.log("=" * 50)
            
        except Exception as e:
            self.log(f"❌ OAuth创建流程出错: {str(e)}")
            self.root.after(0, lambda: messagebox.showerror("错误", f"创建OAuth时出错:\n{str(e)}"))
    
    def _read_project_from_file(self):
        """从projects.txt读取项目信息（照搬参考项目）"""
        try:
            if not os.path.exists('projects.txt'):
                self.log("⚠️ projects.txt文件不存在")
                return None
            
            with open('projects.txt', 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            if not content:
                self.log("⚠️ projects.txt文件为空")
                return None
            
            # 解析格式: project-id(project-number)
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                if '(' in line and ')' in line:
                    try:
                        project_id = line.split('(')[0].strip()
                        project_number = line.split('(')[1].split(')')[0].strip()
                        
                        if project_id and project_number:
                            self.log(f"📋 从文件读取: {project_id} ({project_number})")
                            return {
                                'project_id': project_id,
                                'project_number': project_number
                            }
                    except:
                        continue
            
            self.log("⚠️ 无法解析projects.txt中的项目信息")
            return None
            
        except Exception as e:
            self.log(f"读取项目文件失败: {e}")
            return None
    
    def _read_email_from_file(self):
        """从账号.txt读取邮箱信息
        文件格式: 账号邮箱|密码|辅助邮箱
        返回: (账号邮箱, 辅助邮箱)
        """
        try:
            if not os.path.exists('账号.txt'):
                self.log("⚠️ 账号.txt文件不存在")
                return None, None
            
            with open('账号.txt', 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            if not content:
                self.log("⚠️ 账号.txt文件为空")
                return None, None
            
            # 解析格式: 账号邮箱|密码|辅助邮箱
            parts = content.split('|')
            
            if len(parts) < 1:
                self.log("⚠️ 账号.txt格式错误")
                return None, None
            
            account_email = parts[0].strip() if len(parts) > 0 else None
            auxiliary_email = parts[2].strip() if len(parts) > 2 else None
            
            self.log(f"📧 从文件读取邮箱:")
            if account_email:
                self.log(f"   账号邮箱: {account_email}")
            if auxiliary_email:
                self.log(f"   辅助邮箱: {auxiliary_email}")
            
            return account_email, auxiliary_email
            
        except Exception as e:
            self.log(f"读取邮箱文件失败: {e}")
            return None, None
    
    def _save_oauth_client(self, client_info: dict):
        """保存OAuth凭证到文件（同时保存人类可读格式和JSON格式）"""
        try:
            # 保存人类可读格式
            with open('oauth_client.txt', 'w', encoding='utf-8') as f:
                f.write(f"客户端ID: {client_info['client_id']}\n")
                f.write(f"客户端密钥: {client_info['client_secret']}\n")
                f.write(f"显示名称: {client_info.get('display_name', '')}\n")
                f.write(f"创建时间: {client_info.get('creation_time', '')}\n")
                f.write(f"重定向URI: {', '.join(client_info.get('redirect_uris', []))}\n")
            
            # 同时保存JSON格式（便于程序读取）
            with open('oauth_client.json', 'w', encoding='utf-8') as f:
                json.dump(client_info, f, indent=2, ensure_ascii=False)
            
            self.log(f"💾 OAuth凭证已保存到 oauth_client.txt 和 oauth_client.json")
        except Exception as e:
            self.log(f"保存OAuth凭证失败: {e}")
    
    def show_screenshot_dialog(self, data_url):
        """显示截图对话框"""
        try:
            import base64
            from io import BytesIO
            from PIL import Image, ImageTk
            
            # 解析base64图片
            img_data = data_url.split(',')[1]
            img_bytes = base64.b64decode(img_data)
            img = Image.open(BytesIO(img_bytes))
            
            # 创建对话框
            dialog = ctk.CTkToplevel(self.root)
            dialog.title("📸 页面截图")
            dialog.geometry("800x600")
            
            # 调整图片大小以适应窗口
            max_size = (750, 500)
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # 转换为Tkinter可用的格式
            photo = ImageTk.PhotoImage(img)
            
            # 显示图片
            from tkinter import Label
            label = Label(dialog, image=photo)
            label.image = photo  # 保持引用
            label.pack(padx=10, pady=10)
            
            # 保存按钮
            def save_screenshot():
                from tkinter import filedialog
                filepath = filedialog.asksaveasfilename(
                    defaultextension=".png",
                    filetypes=[("PNG图片", "*.png"), ("所有文件", "*.*")]
                )
                if filepath:
                    img.save(filepath)
                    self.log(f"💾 截图已保存: {filepath}")
            
            ctk.CTkButton(
                dialog,
                text="💾 保存图片",
                command=save_screenshot
            ).pack(pady=10)
            
        except Exception as e:
            messagebox.showerror("错误", f"显示截图失败: {e}")
    
    def show_page_content_dialog(self, page_data):
        """显示页面内容对话框"""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("📄 页面内容")
        dialog.geometry("800x600")
        
        # 标题和URL
        info_frame = ctk.CTkFrame(dialog)
        info_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            info_frame,
            text=f"标题: {page_data.get('title', 'N/A')}",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=5, pady=2)
        
        ctk.CTkLabel(
            info_frame,
            text=f"URL: {page_data.get('url', 'N/A')}",
            font=ctk.CTkFont(size=11)
        ).pack(anchor="w", padx=5, pady=2)
        
        # 标签页选择器
        tabview = ctk.CTkTabview(dialog)
        tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 文本内容标签
        tab1 = tabview.add("文本内容")
        text_box = ctk.CTkTextbox(tab1)
        text_box.pack(fill="both", expand=True)
        text_box.insert("1.0", page_data.get('text', ''))
        
        # HTML源码标签
        tab2 = tabview.add("HTML源码")
        html_box = ctk.CTkTextbox(tab2)
        html_box.pack(fill="both", expand=True)
        html_box.insert("1.0", page_data.get('html', ''))
        
    async def websocket_client(self):
        """WebSocket客户端"""
        uri = "ws://localhost:8765"
        
        while True:
            try:
                async with websockets.connect(uri) as ws:
                    self.ws = ws
                    self.is_connected = True
                    
                    # 发送GUI连接标识
                    await ws.send(json.dumps({"type": "gui_connect"}))
                    
                    self.root.after(0, lambda: self.server_status.configure(
                        text="🟢 WebSocket: 已连接"
                    ))
                    self.root.after(0, lambda: self.log("✅ 已连接到服务器"))
                    
                    # 接收消息
                    async for message in ws:
                        data = json.loads(message)
                        self.root.after(0, lambda d=data: self.handle_message(d))
                        
            except Exception as e:
                self.is_connected = False
                self.root.after(0, lambda: self.server_status.configure(
                    text="🔴 WebSocket: 未连接"
                ))
                if self.server_running:
                    self.root.after(0, lambda: self.log(f"❌ 连接失败，3秒后重试..."))
                await asyncio.sleep(3)
                
    def handle_message(self, data):
        """处理来自服务器的消息"""
        msg_type = data.get('type')
        
        if msg_type == 'browser_connected':
            self.browser_connected = True
            self.browser_status.configure(text="🟢 浏览器: 已连接")
            self.log("✅ 浏览器插件已连接")
            
        elif msg_type == 'browser_disconnected':
            self.browser_connected = False
            self.browser_status.configure(text="🔴 浏览器: 未连接")
            self.log("❌ 浏览器插件已断开")
            
        elif msg_type == 'server_status':
            self.browser_connected = data.get('browser_connected', False)
            if self.browser_connected:
                self.browser_status.configure(text="🟢 浏览器: 已连接")
            
        elif msg_type == 'response':
            result = data.get('result', {})
            command = data.get('command', '')
            
            # 检查是否有待处理的命令回调
            for cmd_id, callback in list(self.pending_commands.items()):
                if command in cmd_id or command == data.get('command'):
                    try:
                        callback(data)
                    except:
                        pass
            
            if result.get('success'):
                # 对于getCookies命令，只记录不显示详情
                if command == 'getCookies':
                    self.log(f"✅ {command} 成功")
                    return
                
                self.log(f"✅ {command} 成功")
                
                # 显示详细结果
                if 'data' in result:
                    result_data = result['data']
                    
                    # 特殊处理大数据命令
                    if command == 'screenshot':
                        # 截图返回base64，只显示摘要
                        if isinstance(result_data, str) and result_data.startswith('data:image'):
                            data_size = len(result_data)
                            self.log(f"📸 截图成功，大小: {data_size} 字符 ({data_size/1024:.1f}KB)")
                            self.show_screenshot_dialog(result_data)
                        else:
                            self.log(f"📊 数据: {str(result_data)[:200]}")
                            
                    elif command == 'getPageContent':
                        # 页面内容可能很大，只显示摘要
                        if isinstance(result_data, dict):
                            title = result_data.get('title', 'N/A')
                            url = result_data.get('url', 'N/A')
                            html_size = len(result_data.get('html', ''))
                            text_size = len(result_data.get('text', ''))
                            self.log(f"📄 页面: {title}")
                            self.log(f"   URL: {url}")
                            self.log(f"   HTML大小: {html_size} 字符 ({html_size/1024:.1f}KB)")
                            self.log(f"   文本大小: {text_size} 字符 ({text_size/1024:.1f}KB)")
                            self.show_page_content_dialog(result_data)
                        else:
                            self.log(f"📊 数据: {str(result_data)[:200]}")
                            
                    else:
                        # 其他命令，限制显示长度
                        data_str = json.dumps(result_data, ensure_ascii=False, indent=2)
                        if len(data_str) > 500:
                            self.log(f"📊 数据预览: {data_str[:500]}...")
                            self.log(f"   (数据过大，仅显示前500字符)")
                        else:
                            self.log(f"📊 数据: {data_str}")
                            
                elif 'message' in result:
                    self.log(f"💬 {result['message']}")
            else:
                self.log(f"❌ {command} 失败: {result.get('message', '未知错误')}")
                
    def toggle_server(self):
        """启动/停止服务器"""
        if self.server_running:
            self.stop_server()
        else:
            self.start_server()
    
    def auto_start_server(self):
        """自动启动服务器（启动时调用）"""
        self.log("🚀 正在自动启动服务器...")
        self.start_server()
    
    def start_server(self):
        """启动WebSocket服务器"""
        try:
            # 检查server.py是否存在
            if not os.path.exists('server.py'):
                messagebox.showerror("错误", "找不到server.py文件")
                return
            
            # 启动服务器进程（后台运行，隐藏窗口）
            if sys.platform == 'win32':
                # 使用pythonw.exe后台运行，或使用隐藏窗口的方式
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
                self.server_process = subprocess.Popen(
                    [sys.executable, 'server.py'],
                    startupinfo=startupinfo,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            else:
                self.server_process = subprocess.Popen(
                    [sys.executable, 'server.py']
                )
            
            self.server_running = True
            self.server_btn.configure(
                text="🛑 停止服务器",
                fg_color="#F44336",
                hover_color="#D32F2F"
            )
            self.log("✅ WebSocket服务器已启动（后台运行）")
            self.log("⏳ 等待服务器初始化...")
            
            # 延迟2秒后连接WebSocket
            self.root.after(2000, self.start_websocket)
            
        except Exception as e:
            messagebox.showerror("错误", f"启动服务器失败: {e}")
            self.log(f"❌ 启动服务器失败: {e}")
    
    def stop_server(self):
        """停止WebSocket服务器"""
        if self.server_process:
            self.server_process.terminate()
            self.server_process = None
        
        self.server_running = False
        self.is_connected = False
        
        # 只在窗口未被销毁时更新UI
        try:
            self.server_btn.configure(
                text="🚀 启动服务器",
                fg_color="#4CAF50",
                hover_color="#388E3C"
            )
            self.server_status.configure(text="🔴 WebSocket: 未连接")
            self.browser_status.configure(text="🔴 浏览器: 未连接")
            self.log("🛑 WebSocket服务器已停止")
        except:
            pass  # 窗口已关闭，忽略UI更新错误
    
    def show_server_log(self):
        """显示服务器日志"""
        if not self.server_process:
            messagebox.showinfo("提示", "服务器未运行")
            return
        
        messagebox.showinfo("提示", 
            "服务器在后台运行，无日志输出\n\n"
            "状态检查：\n"
            f"- 进程ID: {self.server_process.pid}\n"
            f"- 运行状态: {'运行中' if self.server_process.poll() is None else '已停止'}\n"
            f"- 连接状态: {'已连接' if self.is_connected else '未连接'}"
        )
    
    def start_websocket(self):
        """启动WebSocket连接线程"""
        def run_loop():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_until_complete(self.websocket_client())
            
        self.ws_thread = threading.Thread(target=run_loop, daemon=True)
        self.ws_thread.start()
        
    def run(self):
        """运行GUI"""
        # 设置窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()
    
    def on_closing(self):
        """窗口关闭时的处理"""
        # 停止服务器
        if self.server_running and self.server_process:
            self.server_process.terminate()
            self.server_process = None
        # 销毁窗口
        self.root.destroy()

if __name__ == "__main__":
    app = BrowserControlGUI()
    app.run()

