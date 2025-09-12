import React from 'react';

const Test: React.FC = () => {
  console.log('Test组件正在渲染...');
  
  return (
    <div style={{ padding: '24px', backgroundColor: '#f0f0f0', minHeight: '100vh' }}>
      <h1 style={{ color: 'red', fontSize: '24px' }}>测试页面</h1>
      <p style={{ color: 'blue', fontSize: '16px' }}>如果您能看到这个页面，说明前端基本功能正常。</p>
      <p style={{ color: 'green', fontSize: '14px' }}>当前时间: {new Date().toLocaleString()}</p>
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
          cursor: 'pointer'
        }}
      >
        点击测试
      </button>
    </div>
  );
};

export default Test;
