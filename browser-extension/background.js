// 浏览器插件后台脚本
let ws = null;
let wsUrl = 'ws://127.0.0.1:8765';  // 使用明确的IPv4地址
let reconnectInterval = 1000;  // 缩短重连间隔到1秒
let reconnectTimer = null;
let isConnected = false;
let isConnecting = false;  // 连接锁，防止并发连接
let heartbeatInterval = null;
let reconnectAttempts = 0;
let maxReconnectInterval = 5000;  // 最大重连间隔5秒

// 连接到WebSocket服务器
function connectWebSocket() {
  // 如果正在连接或已连接，直接返回
  if (isConnecting) {
    console.log('⚠️ 连接正在进行中，跳过');
    return;
  }
  
  if (isConnected && ws && ws.readyState === WebSocket.OPEN) {
    console.log('✅ 已经连接，无需重连');
    return;
  }
  
  // 设置连接锁
  isConnecting = true;
  
  // 清除之前的重连定时器
  if (reconnectTimer) {
    clearTimeout(reconnectTimer);
    reconnectTimer = null;
  }
  
  try {
    // 如果已有连接且未关闭，先关闭
    if (ws && ws.readyState !== WebSocket.CLOSED) {
      ws.close();
    }
    
    console.log(`尝试连接到服务器... (第 ${reconnectAttempts + 1} 次)`);
    ws = new WebSocket(wsUrl);
    
    ws.onopen = () => {
      console.log('✅ 已连接到Python服务器');
      isConnected = true;
      isConnecting = false;  // 释放连接锁
      reconnectAttempts = 0;  // 重置重连次数
      chrome.storage.local.set({ connectionStatus: 'connected' });
      
      // 发送连接成功消息
      ws.send(JSON.stringify({
        type: 'connection',
        message: '浏览器插件已连接'
      }));
      
      // 启动心跳，每20秒发送一次ping
      if (heartbeatInterval) {
        clearInterval(heartbeatInterval);
      }
      heartbeatInterval = setInterval(() => {
        if (ws && ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: 'ping' }));
        }
      }, 20000);
    };
    
    ws.onmessage = async (event) => {
      try {
        const data = JSON.parse(event.data);
        await handleCommand(data);
      } catch (error) {
        console.error('处理消息错误:', error);
      }
    };
    
    ws.onerror = (error) => {
      console.warn('⚠️ WebSocket错误');
      isConnected = false;
      isConnecting = false;  // 释放连接锁
      chrome.storage.local.set({ connectionStatus: 'error' });
    };
    
    ws.onclose = () => {
      console.log('🔴 WebSocket连接关闭');
      isConnected = false;
      isConnecting = false;  // 释放连接锁
      chrome.storage.local.set({ connectionStatus: 'disconnected' });
      
      // 清除心跳
      if (heartbeatInterval) {
        clearInterval(heartbeatInterval);
        heartbeatInterval = null;
      }
      
      // 使用指数退避算法进行重连
      reconnectAttempts++;
      const delay = Math.min(reconnectInterval * Math.pow(1.5, Math.min(reconnectAttempts, 5)), maxReconnectInterval);
      console.log(`⏳ ${delay}ms 后重连...`);
      
      reconnectTimer = setTimeout(connectWebSocket, delay);
    };
  } catch (error) {
    console.error('连接失败:', error);
    isConnecting = false;  // 释放连接锁
    reconnectAttempts++;
    const delay = Math.min(reconnectInterval * Math.pow(1.5, Math.min(reconnectAttempts, 5)), maxReconnectInterval);
    reconnectTimer = setTimeout(connectWebSocket, delay);
  }
}

// 检查连接状态，如果断开则立即重连
function checkConnection() {
  if (!isConnected || !ws || ws.readyState !== WebSocket.OPEN) {
    console.log('🔄 检测到连接断开，立即重连');
    connectWebSocket();
  }
}

// 每10秒检查一次连接状态
setInterval(checkConnection, 10000);

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
        
      case 'getCookies':
        // 获取Google相关Cookie
        result = await this.getAllGoogleCookies();
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

// 获取所有Google相关域名的Cookie
async function getAllGoogleCookies() {
  try {
    console.log('开始获取Google相关域名的所有Cookie...');
    
    // Google相关的所有域名
    const googleDomains = [
      '.google.com',
      'google.com',
      '.accounts.google.com',
      'accounts.google.com',
      '.console.cloud.google.com',
      'console.cloud.google.com',
      '.googleapis.com',
      'googleapis.com',
      '.gstatic.com',
      'gstatic.com'
    ];
    
    let allCookies = [];
    let cookieMap = new Map(); // 用于去重
    
    // 从所有Google域名获取Cookie
    for (const domain of googleDomains) {
      try {
        const cookies = await chrome.cookies.getAll({ domain: domain });
        console.log(`域名 ${domain} 找到 ${cookies.length} 个Cookie`);
        
        // 添加到总列表，使用Map去重
        cookies.forEach(cookie => {
          const key = `${cookie.name}_${cookie.domain}`;
          if (!cookieMap.has(key)) {
            cookieMap.set(key, cookie);
            allCookies.push(cookie);
          }
        });
      } catch (domainError) {
        console.warn(`获取域名 ${domain} Cookie失败:`, domainError.message);
      }
    }
    
    console.log(`总共找到 ${allCookies.length} 个唯一Cookie`);
    
    // 检查关键Cookie
    const criticalCookies = ['SAPISID', 'SSID', 'SID', 'APISID', 'HSID'];
    const foundCritical = [];
    
    allCookies.forEach(cookie => {
      if (criticalCookies.includes(cookie.name)) {
        foundCritical.push(cookie.name);
        console.log(`找到关键Cookie: ${cookie.name}`);
      }
    });
    
    // 将Cookie格式化为字符串
    let cookieString = '';
    allCookies.forEach(cookie => {
      if (cookieString) cookieString += '; ';
      cookieString += `${cookie.name}=${cookie.value}`;
    });
    
    console.log('Cookie字符串长度:', cookieString.length);
    console.log('找到的关键Cookie:', foundCritical.join(', '));
    
    return {
      success: true,
      cookies: cookieString,
      cookieCount: allCookies.length,
      criticalCookies: foundCritical,
      message: `成功获取 ${allCookies.length} 个Cookie`
    };
    
  } catch (error) {
    console.error('获取Cookie出错:', error);
    return {
      success: false,
      message: `获取Cookie失败: ${error.message}`
    };
  }
}

// ===== 多重触发机制，确保任何情况下都能连接 =====

// 1. 启动时立即连接
connectWebSocket();

// 2. 浏览器启动完成时连接
chrome.runtime.onStartup.addListener(() => {
  console.log('🚀 浏览器启动，尝试连接...');
  connectWebSocket();
});

// 3. 插件安装或更新时连接
chrome.runtime.onInstalled.addListener(() => {
  console.log('🔧 插件已安装/更新，尝试连接...');
  connectWebSocket();
});

// 4. 有标签页激活时检查连接（用户开始使用浏览器）
// 使用节流，避免频繁触发
let lastTabCheck = 0;
chrome.tabs.onActivated.addListener(() => {
  const now = Date.now();
  if (!isConnected && !isConnecting && (now - lastTabCheck) > 2000) {
    lastTabCheck = now;
    console.log('👆 标签页激活，检查连接...');
    checkConnection();
  }
});

// 5. 新建标签页时检查连接
chrome.tabs.onCreated.addListener(() => {
  const now = Date.now();
  if (!isConnected && !isConnecting && (now - lastTabCheck) > 2000) {
    lastTabCheck = now;
    console.log('➕ 新建标签页，检查连接...');
    checkConnection();
  }
});

// 6. Service Worker唤醒时检查连接
// Service Worker可能会休眠，醒来时需要重新连接
self.addEventListener('activate', () => {
  console.log('⚡ Service Worker激活，检查连接...');
  checkConnection();
});

// 7. 保持Service Worker活跃（防止休眠导致断连）
// 每分钟执行一次轻量级任务
chrome.alarms.create('keepAlive', { periodInMinutes: 1 });
chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === 'keepAlive') {
    // 检查连接状态
    if (!isConnected) {
      console.log('⏰ 定时检查，尝试重连...');
      checkConnection();
    }
  }
});

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

