import React from 'react'
import { Routes, Route } from 'react-router-dom'
import { Layout } from 'antd'
import Header from './components/Header'
import Sidebar from './components/Sidebar'
import Dashboard from './pages/Dashboard'
import MonitoringDashboard from './pages/MonitoringDashboard'
import NamespaceList from './pages/NamespaceList'
import RuleList from './pages/RuleList'
import UpstreamServerList from './pages/UpstreamServerList'
import ProxyRuleList from './pages/ProxyRuleList'
import NginxConfigList from './pages/NginxConfigList'
import RouteTest from './pages/RouteTest'
 


const { Content } = Layout

function App() {
  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sidebar />
      <Layout>
        <Header />
        <Content style={{ margin: '0', background: '#f5f5f5' }}>
                  <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/monitoring" element={<MonitoringDashboard />} />
          <Route path="/namespaces" element={<NamespaceList />} />
          <Route path="/rules" element={<RuleList />} />
          <Route path="/upstream-servers" element={<UpstreamServerList />} />
          <Route path="/proxy-rules" element={<ProxyRuleList />} />
          <Route path="/nginx-configs" element={<NginxConfigList />} />
          <Route path="/route-test" element={<RouteTest />} />
          
        </Routes>
        </Content>
      </Layout>
    </Layout>
  )
}

export default App 