import React from 'react';
import { Layout, Typography, Input, Avatar, Dropdown, Badge } from 'antd';
import {
  BellOutlined, SettingOutlined,
  SearchOutlined, DownOutlined, DatabaseOutlined
} from '@ant-design/icons';

const { Header } = Layout;
const { Title, Text } = Typography;

const HeaderComponent: React.FC = () => {
  const userMenuItems = [
    { key: 'profile', label: '个人资料' },
    { key: 'settings', label: '账户设置' },
    { key: 'logout', label: '退出登录' }
  ];
  
  return (
    <Header style={{ 
      padding: '0 24px', 
      display: 'flex', 
      alignItems: 'center', 
      justifyContent: 'space-between',
      background: '#fff',
      borderBottom: '1px solid #e5e6eb',
      boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      zIndex: 1001,
      height: 80,
      lineHeight: '80px'
    }}>
      {/* Logo 和标题 */}
      <div style={{ display: 'flex', alignItems: 'center', height: '100%' }}>
        <div style={{ 
          width: 40, 
          height: 40, 
          borderRadius: 8, 
          backgroundColor: '#165DFF', 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center',
          marginRight: 12
        }}>
          <DatabaseOutlined style={{ color: 'white', fontSize: 20 }} />
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', height: '100%' }}>
          <Title level={4} style={{ margin: 0, color: '#1d2129', lineHeight: '1.2', marginBottom: 0 }}>大模型网关配置中心</Title>
          <Text style={{ fontSize: '12px', color: '#86909c', lineHeight: '1.2' }}>LLM Gateway Configuration</Text>
        </div>
      </div>
      
      {/* 搜索栏 */}
      <div style={{ flex: 1, maxWidth: 500, margin: '0 24px' }}>
        <Input 
          placeholder="搜索模型或策略..." 
          prefix={<SearchOutlined style={{ color: '#86909c' }} />}
          style={{ 
            borderRadius: 8,
            border: '1px solid #e5e6eb',
            boxShadow: 'none'
          }}
        />
      </div>
      
      {/* 用户菜单 */}
      <div style={{ display: 'flex', alignItems: 'center' }}>
        <Badge count={3} style={{ marginRight: 16 }}>
          <BellOutlined style={{ fontSize: 20, cursor: 'pointer', color: '#86909c' }} />
        </Badge>
        <SettingOutlined style={{ fontSize: 20, cursor: 'pointer', marginRight: 16, color: '#86909c' }} />
        <Dropdown menu={{ items: userMenuItems }}>
          <div style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
            <Avatar src="https://picsum.photos/id/1005/200/200" />
            <span style={{ margin: '0 8px', color: '#1d2129' }}>管理员</span>
            <DownOutlined style={{ color: '#86909c' }} />
          </div>
        </Dropdown>
      </div>
    </Header>
  );
};

export default HeaderComponent;