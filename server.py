"""
WebSocket服务器 - 连接浏览器插件和GUI界面
"""
import asyncio
import websockets
import json
from datetime import datetime

# 存储连接的客户端
browser_clients = set()
gui_clients = set()

async def handle_client(websocket, path):
    """处理客户端连接"""
    client_type = None
    
    try:
        # 等待客户端发送身份标识
        async for message in websocket:
            data = json.loads(message)
            
            # 首次连接时确定客户端类型
            if client_type is None:
                if data.get('type') == 'gui_connect':
                    client_type = 'gui'
                    gui_clients.add(websocket)
                    print(f"[{get_time()}] GUI客户端已连接")
                    
                    # 通知GUI当前浏览器连接状态
                    await websocket.send(json.dumps({
                        'type': 'server_status',
                        'browser_connected': len(browser_clients) > 0
                    }))
                    
                elif data.get('type') == 'connection':
                    client_type = 'browser'
                    browser_clients.add(websocket)
                    print(f"[{get_time()}] 浏览器插件已连接")
                    
                    # 通知所有GUI客户端浏览器已连接
                    await broadcast_to_gui({
                        'type': 'browser_connected',
                        'message': '浏览器已连接'
                    })
                    
                continue
            
            # 根据客户端类型处理消息
            if client_type == 'gui':
                # GUI发送的命令，转发给浏览器
                print(f"[{get_time()}] GUI命令: {data.get('command')}")
                await broadcast_to_browsers(data)
                
            elif client_type == 'browser':
                # 浏览器发送的响应，转发给GUI
                print(f"[{get_time()}] 浏览器响应: {data.get('type')}")
                await broadcast_to_gui(data)
                
    except websockets.exceptions.ConnectionClosed:
        print(f"[{get_time()}] 客户端断开连接")
    except Exception as e:
        print(f"[{get_time()}] 错误: {e}")
    finally:
        # 清理连接
        if client_type == 'gui' and websocket in gui_clients:
            gui_clients.remove(websocket)
            print(f"[{get_time()}] GUI客户端已断开")
        elif client_type == 'browser' and websocket in browser_clients:
            browser_clients.remove(websocket)
            print(f"[{get_time()}] 浏览器插件已断开")
            
            # 通知所有GUI客户端浏览器已断开
            await broadcast_to_gui({
                'type': 'browser_disconnected',
                'message': '浏览器已断开'
            })

async def broadcast_to_browsers(message):
    """向所有浏览器客户端广播消息"""
    if browser_clients:
        message_str = json.dumps(message) if isinstance(message, dict) else message
        await asyncio.gather(
            *[client.send(message_str) for client in browser_clients],
            return_exceptions=True
        )

async def broadcast_to_gui(message):
    """向所有GUI客户端广播消息"""
    if gui_clients:
        message_str = json.dumps(message) if isinstance(message, dict) else message
        await asyncio.gather(
            *[client.send(message_str) for client in gui_clients],
            return_exceptions=True
        )

def get_time():
    """获取当前时间字符串"""
    return datetime.now().strftime("%H:%M:%S")

async def main():
    """启动WebSocket服务器"""
    print("=" * 50)
    print("🚀 浏览器控制服务器启动中...")
    print("=" * 50)
    print(f"📡 WebSocket服务器地址: ws://localhost:8765")
    print(f"🌐 等待浏览器插件和GUI连接...")
    print("=" * 50)
    
    async with websockets.serve(handle_client, "localhost", 8765):
        await asyncio.Future()  # 永久运行

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n服务器已停止")

