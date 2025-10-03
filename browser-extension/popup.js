// Popup界面脚本

document.addEventListener('DOMContentLoaded', () => {
  updateStatus();
  
  // 每秒更新一次状态
  setInterval(updateStatus, 1000);
});

function updateStatus() {
  chrome.storage.local.get(['connectionStatus'], (result) => {
    const statusDiv = document.getElementById('status');
    const status = result.connectionStatus || 'disconnected';
    
    statusDiv.className = 'status ' + status;
    
    if (status === 'connected') {
      statusDiv.textContent = '✅ 已连接到Python服务器';
    } else if (status === 'error') {
      statusDiv.textContent = '❌ 连接错误';
    } else {
      statusDiv.textContent = '⏳ 未连接';
    }
  });
}

