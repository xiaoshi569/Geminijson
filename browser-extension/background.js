// 浏览器插件后台脚本
let ws = null;
let wsUrl = 'ws://127.0.0.1:8765';  // 使用明确的IPv4地址
let reconnectInterval = 3000;
let isConnected = false;
let heartbeatInterval = null;

// 连接到WebSocket服务器
function connectWebSocket() {
  try {
    ws = new WebSocket(wsUrl);
    
    ws.onopen = () => {
      console.log('已连接到Python服务器');
      isConnected = true;
      chrome.storage.local.set({ connectionStatus: 'connected' });
      
      // 发送连接成功消息
      ws.send(JSON.stringify({
        type: 'connection',
        message: '浏览器插件已连接'
      }));
      
      // 启动心跳，每30秒发送一次ping
      if (heartbeatInterval) {
        clearInterval(heartbeatInterval);
      }
      heartbeatInterval = setInterval(() => {
        if (ws && ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: 'ping' }));
        }
      }, 30000);
    };
    
    ws.onmessage = async (event) => {
      console.log('收到消息:', event.data);
      try {
        const data = JSON.parse(event.data);
        await handleCommand(data);
      } catch (error) {
        console.error('处理消息错误:', error);
      }
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket错误:', error);
      isConnected = false;
      chrome.storage.local.set({ connectionStatus: 'error' });
    };
    
    ws.onclose = () => {
      console.log('WebSocket连接关闭，尝试重连...');
      isConnected = false;
      chrome.storage.local.set({ connectionStatus: 'disconnected' });
      
      // 清除心跳
      if (heartbeatInterval) {
        clearInterval(heartbeatInterval);
        heartbeatInterval = null;
      }
      
      // 自动重连
      setTimeout(connectWebSocket, reconnectInterval);
    };
  } catch (error) {
    console.error('连接失败:', error);
    setTimeout(connectWebSocket, reconnectInterval);
  }
}

// 处理来自Python的命令
async function handleCommand(data) {
  const { command, params } = data;
  let result = { success: false, message: '' };
  
  try {
    switch (command) {
      case 'openTab':
        // 打开新标签页
        const tab = await chrome.tabs.create({ url: params.url });
        result = { success: true, message: `已打开标签页: ${params.url}`, tabId: tab.id };
        break;
        
      case 'closeTab':
        // 关闭标签页
        await chrome.tabs.remove(params.tabId);
        result = { success: true, message: `已关闭标签页: ${params.tabId}` };
        break;
        
      case 'getCurrentTab':
        // 获取当前标签页信息
        const [currentTab] = await chrome.tabs.query({ active: true, currentWindow: true });
        result = { 
          success: true, 
          data: {
            id: currentTab.id,
            url: currentTab.url,
            title: currentTab.title
          }
        };
        break;
        
      case 'getAllTabs':
        // 获取所有标签页
        const tabs = await chrome.tabs.query({});
        result = { 
          success: true, 
          data: tabs.map(t => ({
            id: t.id,
            url: t.url,
            title: t.title
          }))
        };
        break;
        
      case 'executeScript':
        // 在指定标签页执行JavaScript代码
        const [scriptResult] = await chrome.scripting.executeScript({
          target: { tabId: params.tabId },
          func: new Function(params.code)
        });
        result = { success: true, data: scriptResult.result };
        break;
        
      case 'clickElement':
        // 点击页面元素
        let clickTabId = params.tabId;
        if (!clickTabId) {
          const [activeTab] = await chrome.tabs.query({ active: true, currentWindow: true });
          clickTabId = activeTab.id;
        }
        const clickResponse = await chrome.tabs.sendMessage(clickTabId, {
          action: 'clickElement',
          selector: params.selector
        });
        result = { success: true, message: `已点击元素: ${params.selector}` };
        break;
        
      case 'fillInput':
        // 填充输入框
        let fillTabId = params.tabId;
        if (!fillTabId) {
          const [activeTab] = await chrome.tabs.query({ active: true, currentWindow: true });
          fillTabId = activeTab.id;
        }
        const fillResponse = await chrome.tabs.sendMessage(fillTabId, {
          action: 'fillInput',
          selector: params.selector,
          value: params.value
        });
        result = { success: true, message: `已填充输入框: ${params.selector}` };
        break;
        
      case 'getPageContent':
        // 获取页面内容
        let contentTabId = params.tabId;
        if (!contentTabId) {
          const [activeTab] = await chrome.tabs.query({ active: true, currentWindow: true });
          contentTabId = activeTab.id;
        }
        const pageResult = await chrome.tabs.sendMessage(contentTabId, {
          action: 'getPageContent'
        });
        result = { success: true, data: pageResult };
        break;
        
      case 'screenshot':
        // 截图当前标签页
        const dataUrl = await chrome.tabs.captureVisibleTab();
        result = { success: true, data: dataUrl };
        break;
        
      default:
        result = { success: false, message: `未知命令: ${command}` };
    }
  } catch (error) {
    result = { success: false, message: error.message };
  }
  
  // 发送执行结果回Python服务器
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({
      type: 'response',
      command: command,
      result: result
    }));
  }
}

// 启动时连接
connectWebSocket();

// 监听来自content script的消息
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.type === 'fromContent') {
    // 转发到Python服务器
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(request));
    }
  }
  return true;
});

