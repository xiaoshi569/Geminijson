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
from tkinter import messagebox, scrolledtext
import customtkinter as ctk

class BrowserControlGUI:
    def __init__(self):
        self.ws = None
        self.loop = None
        self.ws_thread = None
        self.is_connected = False
        self.browser_connected = False
        self.server_process = None
        self.server_running = False
        
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
        
        # 页面操作
        page_control = ctk.CTkFrame(left_panel)
        page_control.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            page_control,
            text="🎯 页面元素操作",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=5)
        
        self.selector_entry = ctk.CTkEntry(
            page_control,
            placeholder_text="CSS选择器 (例如: #search-input)"
        )
        self.selector_entry.pack(fill="x", padx=10, pady=5)
        
        self.value_entry = ctk.CTkEntry(
            page_control,
            placeholder_text="输入值 (用于填充输入框)"
        )
        self.value_entry.pack(fill="x", padx=10, pady=5)
        
        self.tabid_entry = ctk.CTkEntry(
            page_control,
            placeholder_text="标签页ID (留空则使用当前标签)"
        )
        self.tabid_entry.pack(fill="x", padx=10, pady=5)
        
        btn_frame2 = ctk.CTkFrame(page_control, fg_color="transparent")
        btn_frame2.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkButton(
            btn_frame2,
            text="👆 点击元素",
            command=self.click_element,
            fg_color="#9C27B0",
            hover_color="#7B1FA2"
        ).pack(side="left", expand=True, padx=2)
        
        ctk.CTkButton(
            btn_frame2,
            text="✍️ 填充输入",
            command=self.fill_input,
            fg_color="#E91E63",
            hover_color="#C2185B"
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
        
    def click_element(self):
        """点击元素"""
        selector = self.selector_entry.get().strip()
        if not selector:
            messagebox.showwarning("警告", "请输入CSS选择器")
            return
            
        tab_id = self.get_tab_id()
        self.send_command("clickElement", {"tabId": tab_id, "selector": selector})
        
    def fill_input(self):
        """填充输入框"""
        selector = self.selector_entry.get().strip()
        value = self.value_entry.get().strip()
        
        if not selector:
            messagebox.showwarning("警告", "请输入CSS选择器")
            return
            
        tab_id = self.get_tab_id()
        self.send_command("fillInput", {"tabId": tab_id, "selector": selector, "value": value})
        
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
        """获取标签页ID"""
        tab_id_str = self.tabid_entry.get().strip()
        if tab_id_str:
            try:
                return int(tab_id_str)
            except:
                pass
        return None
    
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
            
            if result.get('success'):
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

