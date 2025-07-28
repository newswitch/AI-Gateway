import React, { useState, useEffect } from 'react'
import { Card, Row, Col, Statistic, Progress, Select, Table, Spin, Alert, Tabs } from 'antd'
import { 
  UserOutlined, 
  ApiOutlined, 
  ClockCircleOutlined, 
  ExclamationCircleOutlined,
  ReloadOutlined
} from '@ant-design/icons'
import { namespaceMonitoringAPI, NamespaceUsageOverview, NamespaceMonitoring } from '../services/api'

const { Option } = Select
const { TabPane } = Tabs

const MonitoringDashboard: React.FC = () => {
  const [loading, setLoading] = useState(false)
  const [overview, setOverview] = useState<NamespaceUsageOverview | null>(null)
  const [selectedNamespace, setSelectedNamespace] = useState<number | null>(null)
  const [monitoringData, setMonitoringData] = useState<NamespaceMonitoring | null>(null)
  const [timeWindow, setTimeWindow] = useState<string>('30m')
  const [error, setError] = useState<string>('')

  // 获取概览数据
  const fetchOverview = async () => {
    setLoading(true)
    setError('')
    try {
      const response = await namespaceMonitoringAPI.getUsageOverview()
      const data = response.data
      setOverview(data)
      if (data.namespaces.length > 0 && !selectedNamespace) {
        setSelectedNamespace(data.namespaces[0].namespace_id)
      }
    } catch (err) {
      setError('获取概览数据失败')
      console.error('获取概览数据失败:', err)
    } finally {
      setLoading(false)
    }
  }

  // 获取监控数据
  const fetchMonitoringData = async () => {
    if (!selectedNamespace) return
    
    setLoading(true)
    setError('')
    try {
      const response = await namespaceMonitoringAPI.getMonitoring(selectedNamespace, 'all')
      const data = response.data
      setMonitoringData(data)
    } catch (err) {
      setError('获取监控数据失败')
      console.error('获取监控数据失败:', err)
    } finally {
      setLoading(false)
    }
  }

  // 初始化数据
  useEffect(() => {
    fetchOverview()
  }, [])

  // 当选择的命名空间改变时，获取监控数据
  useEffect(() => {
    if (selectedNamespace) {
      fetchMonitoringData()
    }
  }, [selectedNamespace])

  // 自动刷新数据
  useEffect(() => {
    const interval = setInterval(() => {
      fetchOverview()
      if (selectedNamespace) {
        fetchMonitoringData()
      }
    }, 30000) // 每30秒刷新一次

    return () => clearInterval(interval)
  }, [selectedNamespace])

  // 渲染使用情况卡片
  const renderUsageCard = (namespace: any) => {
    const { usage } = namespace
    const { metrics } = usage

    return (
      <Card 
        key={namespace.namespace_id}
        title={namespace.namespace_name}
        extra={
          <span style={{ color: '#666', fontSize: '12px' }}>
            {namespace.namespace_code}
          </span>
        }
        style={{ marginBottom: 16 }}
        hoverable
        onClick={() => setSelectedNamespace(namespace.namespace_id)}
      >
        <Row gutter={16}>
          {metrics.token_usage && (
            <Col span={8}>
              <Statistic
                title="Token使用量"
                value={metrics.token_usage.current_usage}
                suffix={`/ ${metrics.token_usage.max_limit}`}
                valueStyle={{ fontSize: '16px' }}
              />
              <Progress
                percent={Math.min(metrics.token_usage.usage_percentage, 100)}
                size="small"
                status={metrics.token_usage.usage_percentage > 80 ? 'exception' : 'normal'}
              />
            </Col>
          )}
          
          {metrics.qps_usage && (
            <Col span={8}>
              <Statistic
                title="QPS使用量"
                value={metrics.qps_usage.current_usage}
                suffix={`/ ${metrics.qps_usage.max_limit}`}
                valueStyle={{ fontSize: '16px' }}
              />
              <Progress
                percent={Math.min(metrics.qps_usage.usage_percentage, 100)}
                size="small"
                status={metrics.qps_usage.usage_percentage > 80 ? 'exception' : 'normal'}
              />
            </Col>
          )}
          
          {metrics.concurrent_usage && (
            <Col span={8}>
              <Statistic
                title="并发连接数"
                value={metrics.concurrent_usage.current_usage}
                suffix={`/ ${metrics.concurrent_usage.max_limit}`}
                valueStyle={{ fontSize: '16px' }}
              />
              <Progress
                percent={Math.min(metrics.concurrent_usage.usage_percentage, 100)}
                size="small"
                status={metrics.concurrent_usage.usage_percentage > 80 ? 'exception' : 'normal'}
              />
            </Col>
          )}
        </Row>
      </Card>
    )
  }

  // 渲染时间序列图表（简化版本，使用表格显示）
  const renderTimelineTable = (data: any[], title: string) => {
    if (!data || data.length === 0) {
      return <div style={{ textAlign: 'center', padding: '20px', color: '#999' }}>暂无数据</div>
    }

    const columns = [
      {
        title: '时间',
        dataIndex: 'time',
        key: 'time',
        width: 100,
      },
      {
        title: '使用量',
        dataIndex: 'usage',
        key: 'usage',
        width: 100,
      },
    ]

    return (
      <div>
        <h4>{title}</h4>
        <Table
          dataSource={data}
          columns={columns}
          pagination={false}
          size="small"
          scroll={{ y: 200 }}
        />
      </div>
    )
  }

  // 渲染监控详情
  const renderMonitoringDetail = () => {
    if (!monitoringData || !selectedNamespace) {
      return <div style={{ textAlign: 'center', padding: '20px', color: '#999' }}>请选择命名空间查看详情</div>
    }

    const { metrics } = monitoringData
    const selectedNamespaceData = overview?.namespaces.find(n => n.namespace_id === selectedNamespace)

    return (
      <div>
        <Card 
          title={`${selectedNamespaceData?.namespace_name} - 实时监控`}
          extra={
            <Select 
              value={timeWindow} 
              onChange={setTimeWindow}
              style={{ width: 120 }}
            >
              <Option value="15m">15分钟</Option>
              <Option value="30m">30分钟</Option>
              <Option value="1h">1小时</Option>
              <Option value="6h">6小时</Option>
              <Option value="24h">24小时</Option>
            </Select>
          }
        >
          <Tabs defaultActiveKey="token">
            {metrics.token_timeline && (
              <TabPane tab="Token使用量趋势" key="token">
                <Card title="Token使用量时间序列" size="small">
                  {renderTimelineTable(metrics.token_timeline, 'Token使用量')}
                </Card>
              </TabPane>
            )}
            
            {metrics.qps_timeline && (
              <TabPane tab="QPS趋势" key="qps">
                <Card title="QPS时间序列" size="small">
                  {renderTimelineTable(metrics.qps_timeline, 'QPS')}
                </Card>
              </TabPane>
            )}
            
            {metrics.concurrent_timeline && (
              <TabPane tab="并发连接趋势" key="concurrent">
                <Card title="并发连接数时间序列" size="small">
                  {renderTimelineTable(metrics.concurrent_timeline, '并发连接数')}
                </Card>
              </TabPane>
            )}
          </Tabs>
        </Card>
      </div>
    )
  }

  // 渲染统计卡片
  const renderStatistics = () => {
    if (!overview) return null

    const totalNamespaces = overview.total_namespaces
    const activeNamespaces = overview.namespaces.filter(n => 
      n.usage.metrics.token_usage || n.usage.metrics.qps_usage || n.usage.metrics.concurrent_usage
    ).length

    const highUsageNamespaces = overview.namespaces.filter(n => {
      const { metrics } = n.usage
      return (
        (metrics.token_usage && metrics.token_usage.usage_percentage > 80) ||
        (metrics.qps_usage && metrics.qps_usage.usage_percentage > 80) ||
        (metrics.concurrent_usage && metrics.concurrent_usage.usage_percentage > 80)
      )
    }).length

    return (
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="总命名空间数"
              value={totalNamespaces}
              prefix={<UserOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="活跃命名空间"
              value={activeNamespaces}
              prefix={<ApiOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="高使用率命名空间"
              value={highUsageNamespaces}
              prefix={<ExclamationCircleOutlined />}
              valueStyle={{ color: highUsageNamespaces > 0 ? '#cf1322' : '#3f8600' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="监控时间窗口"
              value={timeWindow}
              prefix={<ClockCircleOutlined />}
            />
          </Card>
        </Col>
      </Row>
    )
  }

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2>命名空间使用情况监控</h2>
        <ReloadOutlined 
          onClick={fetchOverview} 
          style={{ fontSize: '18px', cursor: 'pointer' }}
          spin={loading}
        />
      </div>

      {error && (
        <Alert
          message="错误"
          description={error}
          type="error"
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}

      {renderStatistics()}

      <Row gutter={24}>
        <Col span={12}>
          <Card title="命名空间使用情况概览" loading={loading}>
            {overview?.namespaces.map(renderUsageCard)}
          </Card>
        </Col>
        <Col span={12}>
          {renderMonitoringDetail()}
        </Col>
      </Row>
    </div>
  )
}

export default MonitoringDashboard 