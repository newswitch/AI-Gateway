import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.tsx';
import './index.css';

console.log('main.tsx 开始执行...');
console.log('React版本:', React.version);
console.log('根元素:', document.getElementById('root'));

// 等待DOM加载完成
document.addEventListener('DOMContentLoaded', () => {
  console.log('DOM加载完成');
  
  try {
    const rootElement = document.getElementById('root');
    if (!rootElement) {
      throw new Error('找不到root元素');
    }
    
    console.log('开始创建React根节点...');
    const root = ReactDOM.createRoot(rootElement);
    console.log('ReactDOM.createRoot 成功');
    
    root.render(
      <React.StrictMode>
        <App />
      </React.StrictMode>
    );
    console.log('App组件渲染成功');
  } catch (error) {
    console.error('React渲染错误:', error);
  }
});