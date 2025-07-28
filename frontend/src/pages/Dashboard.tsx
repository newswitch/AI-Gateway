import * as React from 'react'
import { useState, useEffect } from 'react'
import { Card, Row, Col, Statistic, Table, Tag, Space, Button, message } from 'antd'
import { 
  AppstoreOutlined, 
  CheckCircleOutlined
} from '@ant-design/icons'
import { namespaceAPI, Namespace } from '../services/api'

const Dashboard: React.FC = () => {
  const [namespaces, setNamespaces] = useState<Namespace[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadDashboardData()
  }, [])

  const loadDashboardData = async () => {
    try {
      setLoading(true)
      const namespacesRes = await namespaceAPI.getAll()
      setNamespaces(namespacesRes.data)
    } catch (error) {
      message.error('加载仪表盘数据失败')
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  const columns = [
    {
      title: '命名空间代码',
      dataIndex: 'namespace_code',
      key: 'namespace_code',
    },
    {
      title: '命名空间名称',
      dataIndex: 'namespace_name',
      key: 'namespace_name',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: number) => (
        <Tag color={status === 1 ? 'green' : 'red'}>
          {status === 1 ? '启用' : '禁用'}
        </Tag>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'create_time',
      key: 'create_time',
      render: (time: string) => new Date(time).toLocaleString(),
    },
  ]

  return (
    <div>
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ margin: 0, fontSize: '24px', fontWeight: 600, color: '#262626' }}>仪表盘</h1>
        <p style={{ margin: '8px 0 0 0', color: '#8c8c8c', fontSize: '14px' }}>系统运行状态和关键指标概览</p>
      </div>

      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="命名空间总数"
              value={namespaces.length}
              prefix={<AppstoreOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="系统状态"
              value="正常"
              prefix={<CheckCircleOutlined style={{ color: '#52c41a' }} />}
            />
          </Card>
        </Col>
      </Row>

      {/* 操作按钮 */}
      <Row style={{ marginBottom: 24 }}>
        <Col>
          <Button onClick={loadDashboardData} loading={loading}>
            刷新
          </Button>
        </Col>
      </Row>

      {/* 命名空间列表 */}
      <Card title="最近创建的命名空间" extra={<Button type="link">查看全部</Button>}>
        <Table
          columns={columns}
          dataSource={namespaces.slice(0, 5)}
          rowKey="namespace_id"
          pagination={false}
          loading={loading}
        />
      </Card>
    </div>
  )
}

export default Dashboard 