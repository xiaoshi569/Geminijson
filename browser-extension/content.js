// Content Script - 在网页中执行的脚本

console.log('浏览器控制插件已加载');

// 监听来自background script的消息
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  const { action } = request;
  
  try {
    switch (action) {
      case 'clickElement':
        const clickElement = document.querySelector(request.selector);
        if (clickElement) {
          clickElement.click();
          sendResponse({ success: true });
        } else {
          sendResponse({ success: false, error: '未找到元素' });
        }
        break;
        
      case 'fillInput':
        const inputElement = document.querySelector(request.selector);
        if (inputElement) {
          inputElement.value = request.value;
          inputElement.dispatchEvent(new Event('input', { bubbles: true }));
          inputElement.dispatchEvent(new Event('change', { bubbles: true }));
          sendResponse({ success: true });
        } else {
          sendResponse({ success: false, error: '未找到输入框' });
        }
        break;
        
      case 'getPageContent':
        sendResponse({
          title: document.title,
          url: window.location.href,
          html: document.documentElement.outerHTML,
          text: document.body.innerText
        });
        break;
        
      case 'getElementText':
        const element = document.querySelector(request.selector);
        if (element) {
          sendResponse({ success: true, text: element.innerText });
        } else {
          sendResponse({ success: false, error: '未找到元素' });
        }
        break;
        
      default:
        sendResponse({ success: false, error: '未知操作' });
    }
  } catch (error) {
    sendResponse({ success: false, error: error.message });
  }
  
  return true;
});

// 可以向background发送页面信息
function sendPageInfo() {
  chrome.runtime.sendMessage({
    type: 'fromContent',
    data: {
      url: window.location.href,
      title: document.title
    }
  });
}

