import React from 'react'
import { Layout, Menu, type MenuProps } from 'antd'
import { useNavigate, useLocation } from 'react-router-dom'
import {
  DashboardOutlined,
  AppstoreOutlined,
  SettingOutlined,
  ExperimentOutlined,
  CloudServerOutlined,
  ApiOutlined,
  ToolOutlined,
  MonitorOutlined
} from '@ant-design/icons'

const { Sider } = Layout

const Sidebar: React.FC = () => {
  const navigate = useNavigate()
  const location = useLocation()

  const menuItems: MenuProps['items'] = [
    {
      key: '/',
      icon: <DashboardOutlined />,
      label: '仪表盘'
    },
    {
      key: '/monitoring',
      icon: <MonitorOutlined />,
      label: '监控仪表盘'
    },
    {
      key: '/namespaces',
      icon: <AppstoreOutlined />,
      label: '命名空间管理'
    },
    {
      key: '/rules',
      icon: <SettingOutlined />,
      label: '规则管理'
    },
    {
      key: '/upstream-servers',
      icon: <CloudServerOutlined />,
      label: '上游服务器'
    },
    {
      key: '/proxy-rules',
      icon: <ApiOutlined />,
      label: '代理规则'
    },
    {
      key: '/nginx-configs',
      icon: <ToolOutlined />,
      label: 'Nginx配置'
    },
    {
      key: '/route-test',
      icon: <ExperimentOutlined />,
      label: '路由测试'
    }
  ]

  const handleMenuClick = ({ key }: { key: string }) => {
    navigate(key)
  }

  return (
    <Sider width={200} theme="light">
      <div style={{ 
        height: '64px', 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center',
        borderBottom: '1px solid #f0f0f0'
      }}>
        <h2 style={{ margin: 0, color: '#1890ff' }}>AI网关配置中心</h2>
      </div>
      <Menu
        mode="inline"
        selectedKeys={[location.pathname]}
        style={{ height: 'calc(100vh - 64px)', borderRight: 0 }}
        items={menuItems}
        onClick={handleMenuClick}
      />
    </Sider>
  )
}

export default Sidebar 