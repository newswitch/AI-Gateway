import React, { useState, useEffect } from 'react';
import {
  Card, Row, Col, Button, Typography, Statistic, Tag, Space, Table,
  Select, Input, Badge, Progress, message
} from 'antd';
import {
  ReloadOutlined, SignalFilled, CheckCircleOutlined, ClockCircleOutlined,
  DashboardOutlined, ExclamationCircleOutlined, StopOutlined, SyncOutlined,
  DatabaseOutlined, ArrowUpOutlined, ArrowDownOutlined, BellOutlined,
  EyeOutlined, CheckOutlined, CloseOutlined
} from '@ant-design/icons';
import { trafficApi } from '../services/api';

const { Title, Text } = Typography;
const { Option } = Select;

interface Alert {
  id: string;
  title: string;
  level: 'urgent' | 'warning' | 'info' | 'error' | 'critical';
  message: string;
  namespace: string;
  rule: string;
  upstream: string;
  status: 'active' | 'resolved' | 'unresolved';
  createdAt: string;
  updatedAt: string;
}

const TrafficMonitoring: React.FC = () => {
  const [selectedNamespace, setSelectedNamespace] = useState('');
  const [selectedRule, setSelectedRule] = useState('');
  const [selectedUpstream, setSelectedUpstream] = useState('');
  const [selectedStatusCode, setSelectedStatusCode] = useState('');
  const [selectedMethod, setSelectedMethod] = useState('');
  const [isAlertModalVisible, setIsAlertModalVisible] = useState(false);
  const [currentAlert] = useState({
    title: '错误率突增警告',
    content: 'API /v1/chat/completions 5xx错误率超过阈值 1.5%',
    level: 'urgent'
  });
  const [loading, setLoading] = useState(false);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [_trafficMetrics, setTrafficMetrics] = useState<any>({});
  const [_alertStats, setAlertStats] = useState<any>({});

  // 数据加载函数
  const loadTrafficData = async () => {
    try {
      setLoading(true);
      const [metricsResponse, alertsResponse, statsResponse] = await Promise.all([
        trafficApi.getMetrics(),
        trafficApi.getAlerts(),
        trafficApi.getStats()
      ]);
      
      if (metricsResponse.code === 200) {
        setTrafficMetrics(metricsResponse.data || {});
      }
      if (alertsResponse.code === 200) {
        const data = alertsResponse.data?.items || alertsResponse.data || [];
        setAlerts(Array.isArray(data) ? data : []);
      }
      if (statsResponse.code === 200) {
        setAlertStats(statsResponse.data || {});
      }
    } catch (error) {
      message.error('加载流量监控数据失败');
      console.error('Load traffic data error:', error);
    } finally {
      setLoading(false);
    }
  };

  // 组件挂载时加载数据
  useEffect(() => {
    loadTrafficData();
  }, []);

  // 告警处理函数
  const handleAcknowledgeAlert = async (alertId: string) => {
    try {
      const response = await trafficApi.acknowledgeAlert(alertId);
      if (response.code === 200) {
        message.success('告警已确认');
        loadTrafficData();
      } else {
        message.error(response.message || '确认失败');
      }
    } catch (error) {
      message.error('确认告警失败');
      console.error('Acknowledge alert error:', error);
    }
  };

  const handleResolveAlert = async (alertId: string) => {
    try {
      const response = await trafficApi.resolveAlert(alertId);
      if (response.code === 200) {
        message.success('告警已解决');
        loadTrafficData();
      } else {
        message.error(response.message || '解决失败');
      }
    } catch (error) {
      message.error('解决告警失败');
      console.error('Resolve alert error:', error);
    }
  };

  // 刷新数据
  const handleRefresh = () => {
    loadTrafficData();
  };

  const getAlertLevelColor = (level: string) => {
    switch (level) {
      case 'critical': return 'red';
      case 'error': return 'red';
      case 'urgent': return 'red';
      case 'warning': return 'orange';
      case 'info': return 'blue';
      default: return 'default';
    }
  };

  const getAlertLevelText = (level: string) => {
    switch (level) {
      case 'critical': return '严重';
      case 'error': return '错误';
      case 'urgent': return '紧急';
      case 'warning': return '警告';
      case 'info': return '提示';
      default: return '未知';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'active': return '活跃';
      case 'resolved': return '已解决';
      case 'unresolved': return '未解决';
      default: return '未知';
    }
  };

  // 显示告警弹窗
  const showAlertModal = () => {
    setIsAlertModalVisible(true);
  };

  // 处理告警弹窗操作
  const handleAlertAction = (action: 'view' | 'ignore') => {
    if (action === 'view') {
      console.log('查看告警详情');
      // 这里可以跳转到告警详情页面或显示更多信息
    } else if (action === 'ignore') {
      console.log('忽略告警');
      setIsAlertModalVisible(false);
    }
  };

  // 模拟自动显示告警弹窗
  useEffect(() => {
    const timer = setTimeout(() => {
      showAlertModal();
    }, 2000); // 页面加载2秒后自动显示告警弹窗

    return () => clearTimeout(timer);
  }, []);

  // 告警表格列定义
  const alertColumns = [
    {
      title: '告警时间',
      dataIndex: 'createdAt',
      key: 'createdAt',
      render: (time: string) => <Text style={{ fontSize: '12px' }}>{time ? new Date(time).toLocaleString() : '-'}</Text>
    },
    {
      title: '告警级别',
      dataIndex: 'level',
      key: 'level',
      render: (level: string) => (
        <Tag color={getAlertLevelColor(level)}>{getAlertLevelText(level)}</Tag>
      )
    },
    {
      title: '告警标题',
      dataIndex: 'title',
      key: 'title',
      render: (title: string) => (
        <div style={{ maxWidth: 200 }}>
          <Text style={{ fontSize: '12px', fontWeight: 500 }}>{title}</Text>
        </div>
      )
    },
    {
      title: '告警内容',
      dataIndex: 'message',
      key: 'message',
      render: (message: string) => (
        <div style={{ maxWidth: 300 }}>
          <Text style={{ fontSize: '12px' }}>{message}</Text>
        </div>
      )
    },
    {
      title: '命名空间',
      dataIndex: 'namespace',
      key: 'namespace',
      render: (namespace: string) => <Text style={{ fontSize: '12px' }}>{namespace}</Text>
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <div 
            style={{ 
              width: 8, 
              height: 8, 
              borderRadius: '50%', 
              backgroundColor: status === 'resolved' ? '#52c41a' : 
                             status === 'active' ? '#ff4d4f' : '#8c8c8c',
              marginRight: 8 
            }} 
          />
          <Text style={{ 
            color: status === 'resolved' ? '#52c41a' : 
                   status === 'active' ? '#ff4d4f' : '#8c8c8c', 
            fontSize: '12px' 
          }}>
            {getStatusText(status)}
          </Text>
        </div>
      )
    },
    {
      title: '操作',
      key: 'actions',
      render: (_: any, record: Alert) => (
        <Space size="small">
          <Button type="link" icon={<EyeOutlined />} size="small">详情</Button>
          {record.status === 'active' && (
            <Button 
              type="link" 
              icon={<CheckOutlined />} 
              size="small"
              onClick={() => handleAcknowledgeAlert(record.id)}
            >
              确认
            </Button>
          )}
          {record.status === 'active' && (
            <Button 
              type="link" 
              icon={<CloseOutlined />} 
              size="small"
              onClick={() => handleResolveAlert(record.id)}
            >
              解决
            </Button>
          )}
        </Space>
      )
    }
  ];

  return (
    <div style={{ padding: '24px', backgroundColor: '#f5f5f5', minHeight: '100vh' }}>
      {/* 页面标题 */}
      <div style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <Title level={2} style={{ margin: 0, color: '#1d2129' }}>流量监控中心</Title>
            <Text style={{ color: '#4e5969', fontSize: '14px' }}>实时监控大模型网关的流量状况和请求分布</Text>
          </div>
          <Space>
            <Button type="primary" icon={<ReloadOutlined />} onClick={handleRefresh}>
              刷新数据
            </Button>
            <Select defaultValue="realtime" style={{ width: 120 }}>
              <Option value="realtime">实时监控</Option>
              <Option value="today">今日统计</Option>
              <Option value="week">本周统计</Option>
              <Option value="month">本月统计</Option>
            </Select>
          </Space>
        </div>
      </div>

      {/* 右上角告警弹窗 */}
      {isAlertModalVisible && (
        <div 
          style={{
            position: 'fixed',
            top: 100,
            right: 24,
            width: 350,
            backgroundColor: '#fff',
            borderRadius: 12,
            boxShadow: '0 8px 32px rgba(0, 0, 0, 0.15)',
            border: '1px solid #f0f0f0',
            borderLeft: '4px solid #f5222d',
            zIndex: 1000,
            animation: 'slideInRight 0.3s ease-out'
          }}
        >
          <div style={{ padding: '16px 20px' }}>
            {/* 头部 */}
            <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 12 }}>
              <div style={{ display: 'flex', alignItems: 'center' }}>
                <ExclamationCircleOutlined style={{ color: '#f5222d', fontSize: 18, marginRight: 8 }} />
                <Text strong style={{ color: '#1d2129', fontSize: '14px' }}>{currentAlert.title}</Text>
              </div>
              <Button 
                type="text" 
                size="small"
                icon={<CloseOutlined />}
                onClick={() => setIsAlertModalVisible(false)}
                style={{ 
                  padding: '2px 4px',
                  height: 'auto',
                  minWidth: 'auto',
                  color: '#8c8c8c'
                }}
              />
            </div>
            
            {/* 内容 */}
            <div style={{ marginBottom: 16 }}>
              <Text style={{ color: '#4e5969', fontSize: '13px', lineHeight: '1.5' }}>
                {currentAlert.content}
              </Text>
            </div>
            
            {/* 操作按钮 */}
            <div style={{ display: 'flex', gap: 8 }}>
              <Button 
                type="primary" 
                size="small"
                onClick={() => handleAlertAction('view')}
                style={{ borderRadius: 6 }}
              >
                查看详情
              </Button>
              <Button 
                size="small"
                onClick={() => handleAlertAction('ignore')}
                style={{ borderRadius: 6 }}
              >
                忽略
              </Button>
            </div>
          </div>
        </div>
      )}
      
      {/* 添加CSS动画样式 */}
      <style>
        {`
          @keyframes slideInRight {
            from {
              transform: translateX(100%);
              opacity: 0;
            }
            to {
              transform: translateX(0);
              opacity: 1;
            }
          }
        `}
      </style>

      {/* 维度筛选 */}
      <Card style={{ borderRadius: 12, boxShadow: '0 4px 20px rgba(0, 0, 0, 0.08)', marginBottom: 24 }}>
        <Title level={4} style={{ margin: 0, marginBottom: 16, color: '#1d2129' }}>维度筛选</Title>
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} lg={8} xl={6}>
            <Text style={{ display: 'block', marginBottom: 8, color: '#4e5969', fontSize: '12px' }}>命名空间</Text>
            <Select 
              value={selectedNamespace} 
              onChange={setSelectedNamespace} 
              placeholder="全部命名空间"
              style={{ width: '100%' }}
            >
              <Option value="">全部命名空间</Option>
              <Option value="default">default</Option>
              <Option value="prod">prod</Option>
              <Option value="test">test</Option>
              <Option value="dev">dev</Option>
            </Select>
          </Col>
          
          <Col xs={24} sm={12} lg={8} xl={6}>
            <Text style={{ display: 'block', marginBottom: 8, color: '#4e5969', fontSize: '12px' }}>规则</Text>
            <Select 
              value={selectedRule} 
              onChange={setSelectedRule} 
              placeholder="全部规则"
              style={{ width: '100%' }}
            >
              <Option value="">全部规则</Option>
              <Option value="rate_limit">限流规则</Option>
              <Option value="retry">重试规则</Option>
              <Option value="circuit_breaker">熔断规则</Option>
              <Option value="cache">缓存规则</Option>
            </Select>
          </Col>
          
          <Col xs={24} sm={12} lg={8} xl={6}>
            <Text style={{ display: 'block', marginBottom: 8, color: '#4e5969', fontSize: '12px' }}>上游服务</Text>
            <Select 
              value={selectedUpstream} 
              onChange={setSelectedUpstream} 
              placeholder="全部上游"
              style={{ width: '100%' }}
            >
              <Option value="">全部上游</Option>
              <Option value="gpt-4">gpt-4</Option>
              <Option value="gpt-3.5">gpt-3.5</Option>
              <Option value="chatglm">chatglm</Option>
              <Option value="llama">llama</Option>
            </Select>
          </Col>
          
          <Col xs={24} sm={12} lg={8} xl={6}>
            <Text style={{ display: 'block', marginBottom: 8, color: '#4e5969', fontSize: '12px' }}>状态码</Text>
            <Select 
              value={selectedStatusCode} 
              onChange={setSelectedStatusCode} 
              placeholder="全部状态码"
              style={{ width: '100%' }}
            >
              <Option value="">全部状态码</Option>
              <Option value="2xx">2xx (成功)</Option>
              <Option value="4xx">4xx (客户端错误)</Option>
              <Option value="5xx">5xx (服务端错误)</Option>
            </Select>
          </Col>
          
          <Col xs={24} sm={12} lg={8} xl={6}>
            <Text style={{ display: 'block', marginBottom: 8, color: '#4e5969', fontSize: '12px' }}>请求方法</Text>
            <Select 
              value={selectedMethod} 
              onChange={setSelectedMethod} 
              placeholder="全部方法"
              style={{ width: '100%' }}
            >
              <Option value="">全部方法</Option>
              <Option value="GET">GET</Option>
              <Option value="POST">POST</Option>
              <Option value="PUT">PUT</Option>
              <Option value="DELETE">DELETE</Option>
            </Select>
          </Col>
          
          <Col xs={24} sm={12} lg={8} xl={6}>
            <Text style={{ display: 'block', marginBottom: 8, color: '#4e5969', fontSize: '12px' }}>客户端IP</Text>
            <Input placeholder="输入客户端IP" />
          </Col>
          
          <Col xs={24} sm={12} lg={8} xl={6}>
            <Text style={{ display: 'block', marginBottom: 8, color: '#4e5969', fontSize: '12px' }}>API Key</Text>
            <Input placeholder="输入API Key" />
          </Col>
          
          <Col xs={24} sm={12} lg={8} xl={6}>
            <Text style={{ display: 'block', marginBottom: 8, color: '#4e5969', fontSize: '12px' }}>路径前缀</Text>
            <Input placeholder="如 /api/v1/" />
          </Col>
        </Row>
        
        <div style={{ marginTop: 16, display: 'flex', justifyContent: 'flex-end', gap: 12 }}>
          <Button>重置筛选</Button>
          <Button type="primary">应用筛选</Button>
        </div>
      </Card>

      {/* 指标卡片 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={8} xl={6}>
          <Card 
            style={{ 
              borderRadius: 12, 
              boxShadow: '0 4px 20px rgba(0, 0, 0, 0.08)',
              transition: 'all 0.3s ease',
              height: '100%'
            }}
            styles={{ body: { padding: '20px' } }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <Text style={{ color: '#4e5969', fontSize: '14px' }}>总请求</Text>
                <div style={{ marginTop: 8 }}>
                  <Statistic 
                    value={148523} 
                    valueStyle={{ fontSize: '24px', fontWeight: 'bold', color: '#1d2129' }}
                  />
                </div>
                <div style={{ marginTop: 12, display: 'flex', alignItems: 'center' }}>
                  <Tag color="green" icon={<ArrowUpOutlined />}>
                    较昨日增长 12.5%
                  </Tag>
                </div>
              </div>
              <div style={{ 
                width: 48, 
                height: 48, 
                borderRadius: 8, 
                backgroundColor: 'rgba(22, 93, 255, 0.1)', 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'center',
                color: '#165DFF'
              }}>
                <SignalFilled style={{ fontSize: 20 }} />
              </div>
            </div>
          </Card>
        </Col>

        <Col xs={24} sm={12} lg={8} xl={6}>
          <Card 
            style={{ 
              borderRadius: 12, 
              boxShadow: '0 4px 20px rgba(0, 0, 0, 0.08)',
              transition: 'all 0.3s ease',
              height: '100%'
            }}
            styles={{ body: { padding: '20px' } }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <Text style={{ color: '#4e5969', fontSize: '14px' }}>成功率</Text>
                <div style={{ marginTop: 8 }}>
                  <Statistic 
                    value="99.68%" 
                    valueStyle={{ fontSize: '24px', fontWeight: 'bold', color: '#1d2129' }}
                  />
                </div>
                <div style={{ marginTop: 12, display: 'flex', alignItems: 'center' }}>
                  <Tag color="red" icon={<ArrowDownOutlined />}>
                    较昨日下降 0.05%
                  </Tag>
                </div>
              </div>
              <div style={{ 
                width: 48, 
                height: 48, 
                borderRadius: 8, 
                backgroundColor: 'rgba(0, 180, 42, 0.1)', 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'center',
                color: '#00B42A'
              }}>
                <CheckCircleOutlined style={{ fontSize: 20 }} />
              </div>
            </div>
          </Card>
        </Col>

        <Col xs={24} sm={12} lg={8} xl={6}>
          <Card 
            style={{ 
              borderRadius: 12, 
              boxShadow: '0 4px 20px rgba(0, 0, 0, 0.08)',
              transition: 'all 0.3s ease',
              height: '100%'
            }}
            styles={{ body: { padding: '20px' } }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <Text style={{ color: '#4e5969', fontSize: '14px' }}>平均延迟</Text>
                <div style={{ marginTop: 8 }}>
                  <Statistic 
                    value="187ms" 
                    valueStyle={{ fontSize: '24px', fontWeight: 'bold', color: '#1d2129' }}
                  />
                </div>
                <div style={{ marginTop: 12, display: 'flex', alignItems: 'center' }}>
                  <Tag color="green" icon={<ArrowDownOutlined />}>
                    较昨日下降 12ms
                  </Tag>
                </div>
              </div>
              <div style={{ 
                width: 48, 
                height: 48, 
                borderRadius: 8, 
                backgroundColor: 'rgba(15, 198, 194, 0.1)', 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'center',
                color: '#0FC6C2'
              }}>
                <ClockCircleOutlined style={{ fontSize: 20 }} />
              </div>
            </div>
          </Card>
        </Col>

        <Col xs={24} sm={12} lg={8} xl={6}>
          <Card 
            style={{ 
              borderRadius: 12, 
              boxShadow: '0 4px 20px rgba(0, 0, 0, 0.08)',
              transition: 'all 0.3s ease',
              height: '100%'
            }}
            styles={{ body: { padding: '20px' } }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <Text style={{ color: '#4e5969', fontSize: '14px' }}>4xx / 5xx 错误</Text>
                <div style={{ marginTop: 8 }}>
                  <Statistic 
                    value="412 / 173" 
                    valueStyle={{ fontSize: '24px', fontWeight: 'bold', color: '#1d2129' }}
                  />
                </div>
                <div style={{ marginTop: 12, display: 'flex', alignItems: 'center' }}>
                  <Tag color="red" icon={<ArrowUpOutlined />}>
                    5xx 较昨日增长 24%
                  </Tag>
                </div>
              </div>
              <div style={{ 
                width: 48, 
                height: 48, 
                borderRadius: 8, 
                backgroundColor: 'rgba(245, 63, 63, 0.1)', 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'center',
                color: '#F53F3F'
              }}>
                <ExclamationCircleOutlined style={{ fontSize: 20 }} />
              </div>
            </div>
          </Card>
        </Col>

        <Col xs={24} sm={12} lg={8} xl={6}>
          <Card 
            style={{ 
              borderRadius: 12, 
              boxShadow: '0 4px 20px rgba(0, 0, 0, 0.08)',
              transition: 'all 0.3s ease',
              height: '100%'
            }}
            styles={{ body: { padding: '20px' } }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <Text style={{ color: '#4e5969', fontSize: '14px' }}>限流次数</Text>
                <div style={{ marginTop: 8 }}>
                  <Statistic 
                    value={1284} 
                    valueStyle={{ fontSize: '24px', fontWeight: 'bold', color: '#1d2129' }}
                  />
                </div>
                <div style={{ marginTop: 12, display: 'flex', alignItems: 'center' }}>
                  <Tag color="orange" icon={<ArrowUpOutlined />}>
                    较昨日增长 8.2%
                  </Tag>
                </div>
              </div>
              <div style={{ 
                width: 48, 
                height: 48, 
                borderRadius: 8, 
                backgroundColor: 'rgba(255, 125, 0, 0.1)', 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'center',
                color: '#FF7D00'
              }}>
                <StopOutlined style={{ fontSize: 20 }} />
              </div>
            </div>
          </Card>
        </Col>

        <Col xs={24} sm={12} lg={8} xl={6}>
          <Card 
            style={{ 
              borderRadius: 12, 
              boxShadow: '0 4px 20px rgba(0, 0, 0, 0.08)',
              transition: 'all 0.3s ease',
              height: '100%'
            }}
            styles={{ body: { padding: '20px' } }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <Text style={{ color: '#4e5969', fontSize: '14px' }}>重试次数</Text>
                <div style={{ marginTop: 8 }}>
                  <Statistic 
                    value={3521} 
                    valueStyle={{ fontSize: '24px', fontWeight: 'bold', color: '#1d2129' }}
                  />
                </div>
                <div style={{ marginTop: 12, display: 'flex', alignItems: 'center' }}>
                  <Tag color="green" icon={<ArrowDownOutlined />}>
                    较昨日下降 15.3%
                  </Tag>
                </div>
              </div>
              <div style={{ 
                width: 48, 
                height: 48, 
                borderRadius: 8, 
                backgroundColor: 'rgba(22, 93, 255, 0.1)', 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'center',
                color: '#165DFF'
              }}>
                <SyncOutlined style={{ fontSize: 20 }} />
              </div>
            </div>
          </Card>
        </Col>

        <Col xs={24} sm={12} lg={8} xl={6}>
          <Card 
            style={{ 
              borderRadius: 12, 
              boxShadow: '0 4px 20px rgba(0, 0, 0, 0.08)',
              transition: 'all 0.3s ease',
              height: '100%'
            }}
            styles={{ body: { padding: '20px' } }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <Text style={{ color: '#4e5969', fontSize: '14px' }}>熔断次数</Text>
                <div style={{ marginTop: 8 }}>
                  <Statistic 
                    value={42} 
                    valueStyle={{ fontSize: '24px', fontWeight: 'bold', color: '#1d2129' }}
                  />
                </div>
                <div style={{ marginTop: 12, display: 'flex', alignItems: 'center' }}>
                  <Tag color="red" icon={<ArrowUpOutlined />}>
                    较昨日增长 3 次
                  </Tag>
                </div>
              </div>
              <div style={{ 
                width: 48, 
                height: 48, 
                borderRadius: 8, 
                backgroundColor: 'rgba(245, 63, 63, 0.1)', 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'center',
                color: '#F53F3F'
              }}>
                <DashboardOutlined style={{ fontSize: 20 }} />
              </div>
            </div>
          </Card>
        </Col>

        <Col xs={24} sm={12} lg={8} xl={12}>
          <Card 
            style={{ 
              borderRadius: 12, 
              boxShadow: '0 4px 20px rgba(0, 0, 0, 0.08)',
              transition: 'all 0.3s ease',
              height: '100%'
            }}
            styles={{ body: { padding: '20px' } }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <Text style={{ color: '#4e5969', fontSize: '14px' }}>缓存命中率</Text>
                <div style={{ marginTop: 8 }}>
                  <Statistic 
                    value="68.4%" 
                    valueStyle={{ fontSize: '24px', fontWeight: 'bold', color: '#1d2129' }}
                  />
                </div>
                <div style={{ marginTop: 12, display: 'flex', alignItems: 'center' }}>
                  <Tag color="green" icon={<ArrowUpOutlined />}>
                    较昨日上升 3.2%
                  </Tag>
                </div>
              </div>
              <div style={{ 
                width: 48, 
                height: 48, 
                borderRadius: 8, 
                backgroundColor: 'rgba(0, 180, 42, 0.1)', 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'center',
                color: '#00B42A'
              }}>
                <DatabaseOutlined style={{ fontSize: 20 }} />
              </div>
            </div>
            <div style={{ marginTop: 16 }}>
              <Progress 
                percent={68.4} 
                strokeColor="#00B42A" 
                showInfo={false}
                size={8}
              />
            </div>
          </Card>
        </Col>
      </Row>

             {/* 趋势图 */}
       <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
         <Col xs={24} lg={12}>
           <Card 
             style={{ 
               borderRadius: 12,
               boxShadow: '0 4px 20px rgba(0, 0, 0, 0.08)',
               height: '100%'
             }}
             styles={{ body: { padding: '20px' } }}
           >
             <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
               <div style={{ display: 'flex', alignItems: 'center' }}>
                 <Title level={4} style={{ margin: 0, marginRight: 16, color: '#1d2129' }}>请求量/成功率/延迟趋势</Title>
                 <Badge 
                   status="processing" 
                   text={<Text style={{ color: '#00B42A', fontSize: '12px' }}>实时更新</Text>} 
                 />
               </div>
               <Space>
                 <Button type="primary" size="small">过去24小时</Button>
                 <Button size="small">过去7天</Button>
                 <Button size="small">过去30天</Button>
               </Space>
             </div>
             <div style={{ height: 280, backgroundColor: '#fafafa', borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
               <Text style={{ color: '#4e5969' }}>请求量/成功率/延迟趋势图表 - 需要集成 Chart.js</Text>
             </div>
           </Card>
         </Col>
         
         <Col xs={24} lg={12}>
           <Card 
             style={{ 
               borderRadius: 12,
               boxShadow: '0 4px 20px rgba(0, 0, 0, 0.08)',
               height: '100%'
             }}
             styles={{ body: { padding: '20px' } }}
           >
             <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
               <div style={{ display: 'flex', alignItems: 'center' }}>
                 <Title level={4} style={{ margin: 0, marginRight: 16, color: '#1d2129' }}>状态码分布趋势</Title>
                 <Badge 
                   status="processing" 
                   text={<Text style={{ color: '#00B42A', fontSize: '12px' }}>实时更新</Text>} 
                 />
               </div>
               <Space>
                 <Button type="primary" size="small">过去24小时</Button>
                 <Button size="small">过去7天</Button>
                 <Button size="small">过去30天</Button>
               </Space>
             </div>
             <div style={{ height: 280, backgroundColor: '#fafafa', borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
               <Text style={{ color: '#4e5969' }}>状态码分布趋势图表 - 需要集成 Chart.js</Text>
             </div>
           </Card>
         </Col>
       </Row>
       
       {/* Top N 大模型流量 */}
       <Card 
         style={{ 
           marginBottom: 24, 
           borderRadius: 12,
           boxShadow: '0 4px 20px rgba(0, 0, 0, 0.08)'
         }}
         styles={{ body: { padding: '20px' } }}
       >
         <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
           <div style={{ display: 'flex', alignItems: 'center' }}>
             <Title level={4} style={{ margin: 0, marginRight: 16, color: '#1d2129' }}>Top N 大模型流量</Title>
             <Badge 
               status="processing" 
               text={<Text style={{ color: '#00B42A', fontSize: '12px' }}>实时更新</Text>} 
             />
           </div>
           <Space>
             <Select defaultValue="10" style={{ width: 100 }}>
               <Option value="5">Top 5</Option>
               <Option value="10">Top 10</Option>
               <Option value="20">Top 20</Option>
               <Option value="50">Top 50</Option>
             </Select>
             <Button type="primary" size="small">过去24小时</Button>
             <Button size="small">过去7天</Button>
             <Button size="small">过去30天</Button>
           </Space>
         </div>
         <div style={{ height: 320, backgroundColor: '#fafafa', borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
           <Text style={{ color: '#4e5969' }}>Top N 大模型流量图表 - 需要集成 Chart.js</Text>
         </div>
       </Card>

      {/* 系统告警 */}
      <Card style={{ borderRadius: 12, boxShadow: '0 4px 20px rgba(0, 0, 0, 0.08)' }}>
        <div style={{ padding: '20px', borderBottom: '1px solid #e5e6eb', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Title level={4} style={{ margin: 0, color: '#1d2129' }}>系统告警</Title>
          <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
            <Select defaultValue="all" style={{ width: 120 }}>
              <Option value="all">全部级别</Option>
              <Option value="urgent">紧急</Option>
              <Option value="warning">警告</Option>
              <Option value="info">提示</Option>
            </Select>
            <Button type="link" icon={<BellOutlined />}>告警设置</Button>
          </div>
        </div>
        <Table 
          columns={alertColumns} 
          dataSource={alerts}
          loading={loading} 
          rowKey="id"
          pagination={{
            pageSize: 4,
            showSizeChanger: false,
            total: 24,
            showTotal: (total, range) => `显示 ${range[0]} 至 ${range[1]} 条，共 ${total} 条`
          }}
          style={{ borderRadius: 0 }}
        />
      </Card>
    </div>
  );
};

export default TrafficMonitoring;
