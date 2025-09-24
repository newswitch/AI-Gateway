// import React from 'react'; // React 17+ 不需要显式导入
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Layout } from 'antd';
import HeaderComponent from './components/Header';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import ModelRouting from './pages/ModelRouting';
import NamespaceManagement from './pages/NamespaceManagement';
import PolicyConfiguration from './pages/PolicyConfiguration';
import UnifiedNginxConfig from './pages/UnifiedNginxConfig';
import TrafficMonitoring from './pages/TrafficMonitoring';
import AccessLogs from './pages/AccessLogs';
import 'antd/dist/reset.css';

const { Sider, Content } = Layout;

function App() {
  console.log('App组件开始渲染...');
  
  return (
    <Router>
      <Layout style={{ minHeight: '100vh', width: '100%', overflow: 'hidden' }}>
        <HeaderComponent />
        <Layout style={{ marginTop: 80, width: '100%', overflow: 'hidden' }}>
          <Sider
            width={256}
            style={{
              background: '#fff',
              borderRight: '1px solid #e5e6eb',
              position: 'fixed',
              height: 'calc(100vh - 80px)',
              top: 80,
              left: 0,
              overflow: 'auto'
            }}
          >
            <Sidebar />
          </Sider>
          <Content
            style={{
              marginLeft: 256,
              background: '#f5f5f5',
              minHeight: 'calc(100vh - 80px)',
              width: 'calc(100vw - 256px)',
              overflow: 'auto'
            }}
          >
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/model-routing" element={<ModelRouting />} />
              <Route path="/namespace" element={<NamespaceManagement />} />
              <Route path="/policy" element={<PolicyConfiguration />} />
              <Route path="/unified-config" element={<UnifiedNginxConfig />} />
              <Route path="/monitoring" element={<TrafficMonitoring />} />
              <Route path="/logs" element={<AccessLogs />} />
            </Routes>
          </Content>
        </Layout>
      </Layout>
    </Router>
  );
}

export default App;
