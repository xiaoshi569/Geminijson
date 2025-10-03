"""
浏览器自动化示例脚本
演示如何使用Python代码控制浏览器
"""
import asyncio
import websockets
import json
import time

class BrowserController:
    def __init__(self, server_url="ws://localhost:8765"):
        self.server_url = server_url
        self.ws = None
        self.responses = {}
        
    async def connect(self):
        """连接到WebSocket服务器"""
        self.ws = await websockets.connect(self.server_url)
        # 发送GUI连接标识
        await self.ws.send(json.dumps({"type": "gui_connect"}))
        print("✅ 已连接到服务器")
        
        # 等待服务器状态
        response = await self.ws.recv()
        data = json.loads(response)
        if data.get('type') == 'server_status':
            if data.get('browser_connected'):
                print("✅ 浏览器已连接")
            else:
                print("⚠️  浏览器未连接，请先启动浏览器插件")
    
    async def send_command(self, command, params=None):
        """发送命令到浏览器"""
        if params is None:
            params = {}
            
        message = {
            "command": command,
            "params": params
        }
        
        await self.ws.send(json.dumps(message))
        print(f"📤 发送命令: {command}")
        
        # 等待响应
        response = await self.ws.recv()
        data = json.loads(response)
        
        if data.get('type') == 'response':
            result = data.get('result', {})
            if result.get('success'):
                print(f"✅ 命令执行成功")
                return result
            else:
                print(f"❌ 命令执行失败: {result.get('message')}")
                return None
        
        return data
    
    async def open_url(self, url):
        """打开网页"""
        return await self.send_command("openTab", {"url": url})
    
    async def get_current_tab(self):
        """获取当前标签页"""
        return await self.send_command("getCurrentTab")
    
    async def click(self, selector, tab_id=None):
        """点击元素"""
        params = {"selector": selector}
        if tab_id:
            params["tabId"] = tab_id
        return await self.send_command("clickElement", params)
    
    async def fill_input(self, selector, value, tab_id=None):
        """填充输入框"""
        params = {"selector": selector, "value": value}
        if tab_id:
            params["tabId"] = tab_id
        return await self.send_command("fillInput", params)
    
    async def execute_js(self, code, tab_id=None):
        """执行JavaScript"""
        params = {"code": code}
        if tab_id:
            params["tabId"] = tab_id
        return await self.send_command("executeScript", params)
    
    async def get_page_content(self, tab_id=None):
        """获取页面内容"""
        params = {}
        if tab_id:
            params["tabId"] = tab_id
        return await self.send_command("getPageContent", params)
    
    async def close(self):
        """关闭连接"""
        if self.ws:
            await self.ws.close()
            print("👋 已断开连接")


async def example_baidu_search():
    """示例1：百度搜索自动化"""
    print("\n" + "="*50)
    print("示例1：百度搜索自动化")
    print("="*50 + "\n")
    
    controller = BrowserController()
    
    try:
        # 连接服务器
        await controller.connect()
        
        # 打开百度
        print("\n1️⃣ 打开百度首页...")
        await controller.open_url("https://www.baidu.com")
        await asyncio.sleep(2)  # 等待页面加载
        
        # 填充搜索框
        print("\n2️⃣ 填充搜索关键词...")
        await controller.fill_input("#kw", "Python自动化")
        await asyncio.sleep(1)
        
        # 点击搜索按钮
        print("\n3️⃣ 点击搜索按钮...")
        await controller.click("#su")
        await asyncio.sleep(2)
        
        # 获取页面标题
        print("\n4️⃣ 获取搜索结果页面信息...")
        result = await controller.execute_js("return document.title;")
        if result and 'data' in result:
            print(f"📄 页面标题: {result['data']}")
        
        print("\n✅ 自动化流程完成！")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
    finally:
        await controller.close()


async def example_multi_tab():
    """示例2：多标签页操作"""
    print("\n" + "="*50)
    print("示例2：多标签页操作")
    print("="*50 + "\n")
    
    controller = BrowserController()
    
    try:
        await controller.connect()
        
        # 打开多个网站
        websites = [
            "https://www.github.com",
            "https://www.stackoverflow.com",
            "https://www.python.org"
        ]
        
        print("\n1️⃣ 打开多个网站...")
        for url in websites:
            print(f"  📄 打开: {url}")
            await controller.open_url(url)
            await asyncio.sleep(1)
        
        # 获取所有标签页
        print("\n2️⃣ 获取所有标签页信息...")
        result = await controller.send_command("getAllTabs")
        if result and 'data' in result:
            tabs = result['data']
            print(f"\n📊 共有 {len(tabs)} 个标签页：")
            for i, tab in enumerate(tabs, 1):
                print(f"  {i}. {tab.get('title', 'N/A')[:50]}")
        
        print("\n✅ 多标签操作完成！")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
    finally:
        await controller.close()


async def example_page_analysis():
    """示例3：页面内容分析"""
    print("\n" + "="*50)
    print("示例3：页面内容分析")
    print("="*50 + "\n")
    
    controller = BrowserController()
    
    try:
        await controller.connect()
        
        # 打开网页
        print("\n1️⃣ 打开网页...")
        await controller.open_url("https://www.python.org")
        await asyncio.sleep(3)
        
        # 获取页面内容
        print("\n2️⃣ 分析页面内容...")
        result = await controller.get_page_content()
        
        if result and 'data' in result:
            page_data = result['data']
            print(f"\n📊 页面信息：")
            print(f"  标题: {page_data.get('title', 'N/A')}")
            print(f"  URL: {page_data.get('url', 'N/A')}")
            print(f"  文本长度: {len(page_data.get('text', ''))} 字符")
            print(f"  HTML长度: {len(page_data.get('html', ''))} 字符")
        
        # 执行自定义分析
        print("\n3️⃣ 执行自定义分析...")
        js_code = """
        return {
            links: document.querySelectorAll('a').length,
            images: document.querySelectorAll('img').length,
            headings: document.querySelectorAll('h1, h2, h3').length
        };
        """
        result = await controller.execute_js(js_code)
        
        if result and 'data' in result:
            stats = result['data']
            print(f"\n📈 页面统计：")
            print(f"  链接数: {stats.get('links', 0)}")
            print(f"  图片数: {stats.get('images', 0)}")
            print(f"  标题数: {stats.get('headings', 0)}")
        
        print("\n✅ 页面分析完成！")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
    finally:
        await controller.close()


async def main():
    """主函数"""
    print("""
    ╔══════════════════════════════════════════════════╗
    ║     🎮 浏览器自动化示例脚本                      ║
    ╚══════════════════════════════════════════════════╝
    
    请确保：
    1. ✅ WebSocket服务器已启动 (python server.py)
    2. ✅ 浏览器插件已安装并连接
    
    """)
    
    print("请选择要运行的示例：")
    print("1. 百度搜索自动化")
    print("2. 多标签页操作")
    print("3. 页面内容分析")
    print("4. 运行所有示例")
    
    choice = input("\n请输入选项 (1-4): ").strip()
    
    if choice == "1":
        await example_baidu_search()
    elif choice == "2":
        await example_multi_tab()
    elif choice == "3":
        await example_page_analysis()
    elif choice == "4":
        await example_baidu_search()
        await asyncio.sleep(2)
        await example_multi_tab()
        await asyncio.sleep(2)
        await example_page_analysis()
    else:
        print("❌ 无效选项")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 已退出")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        print("\n💡 提示: 请确保WebSocket服务器和浏览器插件都已启动")

