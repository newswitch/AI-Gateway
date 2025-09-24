import React from 'react';

const AppSimple: React.FC = () => {
  console.log('AppSimple组件正在渲染...');
  
  return (
    <div style={{ 
      padding: '20px', 
      backgroundColor: '#f0f0f0', 
      minHeight: '100vh',
      fontSize: '18px'
    }}>
      <h1 style={{ color: 'red' }}>简单测试页面</h1>
      <p style={{ color: 'blue' }}>如果您能看到这个页面，说明React基本功能正常。</p>
      <p style={{ color: 'green' }}>当前时间: {new Date().toLocaleString()}</p>
      <button 
        onClick={() => {
          console.log('按钮被点击了！');
          alert('按钮工作正常！');
        }}
        style={{ 
          padding: '10px 20px', 
          backgroundColor: '#1890ff', 
          color: 'white', 
          border: 'none', 
          borderRadius: '4px',
          cursor: 'pointer',
          fontSize: '16px'
        }}
      >
        点击测试
      </button>
    </div>
  );
};

export default AppSimple;
