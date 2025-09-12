import React from 'react';
import { Menu } from 'antd';
import {
  DashboardOutlined, SwapOutlined, FilterOutlined,
  BarChartOutlined, HistoryOutlined, DatabaseOutlined,
  FileTextOutlined
} from '@ant-design/icons';
import { useLocation, useNavigate } from 'react-router-dom';

const Sidebar: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();

  const menuItems = [
    {
      key: '/',
      icon: <DashboardOutlined />,
      label: '总览',
      onClick: () => navigate('/')
    },
    {
      key: '/model-routing',
      icon: <SwapOutlined />,
      label: '模型路由',
      onClick: () => navigate('/model-routing')
    },
    {
      key: '/namespace',
      icon: <DatabaseOutlined />,
      label: '命名空间管理',
      onClick: () => navigate('/namespace')
    },
    {
      key: '/policy',
      icon: <FilterOutlined />,
      label: '策略配置',
      onClick: () => navigate('/policy')
    },
    {
      key: '/unified-config',
      icon: <FileTextOutlined />,
      label: '统一配置管理',
      onClick: () => navigate('/unified-config')
    },
    {
      key: '/monitoring',
      icon: <BarChartOutlined />,
      label: '流量监控',
      onClick: () => navigate('/monitoring')
    },
    {
      key: '/logs',
      icon: <HistoryOutlined />,
      label: '访问日志',
      onClick: () => navigate('/logs')
    }
  ];

  return (
    <div style={{ padding: '16px 0' }}>
      <div style={{ padding: '0 16px 16px', borderBottom: '1px solid #f0f0f0', marginBottom: '16px' }}>
        <div style={{ fontSize: '12px', fontWeight: 600, color: '#8c8c8c', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
          主菜单
        </div>
      </div>
      
      <Menu
        mode="inline"
        selectedKeys={[location.pathname]}
        style={{ 
          border: 'none', 
          backgroundColor: 'transparent',
          fontSize: '14px'
        }}
        items={menuItems}
      />
    </div>
  );
};

export default Sidebar;