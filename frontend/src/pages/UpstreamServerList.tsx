import React, { useState, useEffect } from 'react'
import {
  Table,
  Button,
  Modal,
  Form,
  Input,
  Select,
  InputNumber,
  Switch,
  Space,
  Tag,
  message,
  Popconfirm,
  Card,
  Row,
  Col,
  Divider
} from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined, EyeOutlined } from '@ant-design/icons'
import { upstreamServerAPI, UpstreamServer, UpstreamServerCreate, UpstreamServerUpdate } from '../services/api'

const { Option } = Select
const { TextArea } = Input

const UpstreamServerList: React.FC = () => {
  const [servers, setServers] = useState<UpstreamServer[]>([])
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [editingServer, setEditingServer] = useState<UpstreamServer | null>(null)
  const [form] = Form.useForm()

  const serverTypeOptions = [
    { value: 'openai', label: 'OpenAI' },
    { value: 'azure', label: 'Azure OpenAI' },
    { value: 'claude', label: 'Claude' },
    { value: 'anthropic', label: 'Anthropic' },
    { value: 'custom', label: '自定义' }
  ]

  const fetchServers = async () => {
    setLoading(true)
    try {
      const response = await upstreamServerAPI.getAll()
      setServers(response.data)
    } catch (error) {
      message.error('获取上游服务器列表失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchServers()
  }, [])

  const handleCreate = () => {
    setEditingServer(null)
    form.resetFields()
    setModalVisible(true)
  }

  const handleEdit = (server: UpstreamServer) => {
    setEditingServer(server)
    form.setFieldsValue({
      ...server,
      model_config: server.model_config ? JSON.stringify(server.model_config, null, 2) : ''
    })
    setModalVisible(true)
  }

  const handleDelete = async (serverId: number) => {
    try {
      await upstreamServerAPI.delete(serverId)
      message.success('删除成功')
      fetchServers()
    } catch (error) {
      message.error('删除失败')
    }
  }

  const handleSubmit = async (values: any) => {
    try {
      const submitData = {
        ...values,
        model_config: values.model_config ? JSON.parse(values.model_config) : undefined
      }

      if (editingServer) {
        await upstreamServerAPI.update(editingServer.server_id, submitData)
        message.success('更新成功')
      } else {
        await upstreamServerAPI.create(submitData)
        message.success('创建成功')
      }

      setModalVisible(false)
      fetchServers()
    } catch (error) {
      message.error(editingServer ? '更新失败' : '创建失败')
    }
  }

  const columns = [
    {
      title: '服务器名称',
      dataIndex: 'server_name',
      key: 'server_name',
      width: 150
    },
    {
      title: '服务器类型',
      dataIndex: 'server_type',
      key: 'server_type',
      width: 120,
      render: (type: string) => {
        const colorMap: Record<string, string> = {
          openai: 'blue',
          azure: 'green',
          claude: 'purple',
          anthropic: 'orange',
          custom: 'default'
        }
        return <Tag color={colorMap[type]}>{type.toUpperCase()}</Tag>
      }
    },
    {
      title: '服务器地址',
      dataIndex: 'server_url',
      key: 'server_url',
      width: 200,
      ellipsis: true
    },
    {
      title: '负载均衡权重',
      dataIndex: 'load_balance_weight',
      key: 'load_balance_weight',
      width: 120
    },
    {
      title: '最大连接数',
      dataIndex: 'max_connections',
      key: 'max_connections',
      width: 120
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 80,
      render: (status: number) => (
        <Tag color={status === 1 ? 'green' : 'red'}>
          {status === 1 ? '启用' : '禁用'}
        </Tag>
      )
    },
    {
      title: '创建时间',
      dataIndex: 'create_time',
      key: 'create_time',
      width: 180,
      render: (time: string) => new Date(time).toLocaleString()
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      render: (_: any, record: UpstreamServer) => (
        <Space>
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定要删除这个上游服务器吗？"
            onConfirm={() => handleDelete(record.server_id)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="link" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      )
    }
  ]

  return (
    <div style={{ padding: '24px' }}>
      <Card title="上游服务器管理" extra={
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
          添加上游服务器
        </Button>
      }>
        <Table
          columns={columns}
          dataSource={servers}
          rowKey="server_id"
          loading={loading}
          pagination={{
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条记录`
          }}
        />
      </Card>

      <Modal
        title={editingServer ? '编辑上游服务器' : '添加上游服务器'}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
        width={800}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          initialValues={{
            load_balance_weight: 1,
            max_connections: 100,
            timeout_connect: 30,
            timeout_read: 300,
            timeout_write: 300,
            health_check_interval: 30,
            status: 1
          }}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="server_name"
                label="服务器名称"
                rules={[{ required: true, message: '请输入服务器名称' }]}
              >
                <Input placeholder="请输入服务器名称" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="server_type"
                label="服务器类型"
                rules={[{ required: true, message: '请选择服务器类型' }]}
              >
                <Select placeholder="请选择服务器类型">
                  {serverTypeOptions.map(option => (
                    <Option key={option.value} value={option.value}>
                      {option.label}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={24}>
              <Form.Item
                name="server_url"
                label="服务器地址"
                rules={[{ required: true, message: '请输入服务器地址' }]}
              >
                <Input placeholder="请输入服务器地址，如：https://api.openai.com/v1" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={24}>
              <Form.Item
                name="api_key"
                label="API密钥"
              >
                <Input.Password placeholder="请输入API密钥" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={24}>
              <Form.Item
                name="model_config"
                label="模型配置 (JSON格式)"
              >
                <TextArea
                  rows={4}
                  placeholder={`请输入JSON格式的模型配置，例如：
{
  "models": ["gpt-4", "gpt-3.5-turbo"],
  "default_model": "gpt-3.5-turbo"
}`}
                />
              </Form.Item>
            </Col>
          </Row>

          <Divider>连接配置</Divider>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                name="load_balance_weight"
                label="负载均衡权重"
                rules={[{ required: true, message: '请输入负载均衡权重' }]}
              >
                <InputNumber min={1} max={100} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="max_connections"
                label="最大连接数"
                rules={[{ required: true, message: '请输入最大连接数' }]}
              >
                <InputNumber min={1} max={10000} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="status"
                label="状态"
                valuePropName="checked"
              >
                <Switch checkedChildren="启用" unCheckedChildren="禁用" />
              </Form.Item>
            </Col>
          </Row>

          <Divider>超时配置</Divider>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                name="timeout_connect"
                label="连接超时(秒)"
                rules={[{ required: true, message: '请输入连接超时时间' }]}
              >
                <InputNumber min={1} max={300} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="timeout_read"
                label="读取超时(秒)"
                rules={[{ required: true, message: '请输入读取超时时间' }]}
              >
                <InputNumber min={1} max={3600} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="timeout_write"
                label="写入超时(秒)"
                rules={[{ required: true, message: '请输入写入超时时间' }]}
              >
                <InputNumber min={1} max={3600} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Divider>健康检查</Divider>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="health_check_url"
                label="健康检查URL"
              >
                <Input placeholder="请输入健康检查URL" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="health_check_interval"
                label="健康检查间隔(秒)"
                rules={[{ required: true, message: '请输入健康检查间隔' }]}
              >
                <InputNumber min={5} max={300} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                {editingServer ? '更新' : '创建'}
              </Button>
              <Button onClick={() => setModalVisible(false)}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default UpstreamServerList 