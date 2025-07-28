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
  Divider,
  Typography
} from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined, ApiOutlined } from '@ant-design/icons'
import { proxyRuleAPI, upstreamServerAPI, ProxyRule, ProxyRuleCreate, ProxyRuleUpdate, UpstreamServer } from '../services/api'

const { Option } = Select
const { Text } = Typography

const ProxyRuleList: React.FC = () => {
  const [rules, setRules] = useState<ProxyRule[]>([])
  const [servers, setServers] = useState<UpstreamServer[]>([])
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [editingRule, setEditingRule] = useState<ProxyRule | null>(null)
  const [form] = Form.useForm()

  const ruleTypeOptions = [
    { value: 'path_match', label: '路径匹配' },
    { value: 'header_match', label: '请求头匹配' },
    { value: 'model_match', label: '模型匹配' }
  ]

  const fetchRules = async () => {
    setLoading(true)
    try {
      const response = await proxyRuleAPI.getAll()
      setRules(response.data)
    } catch (error) {
      message.error('获取代理规则列表失败')
    } finally {
      setLoading(false)
    }
  }

  const fetchServers = async () => {
    try {
      const response = await upstreamServerAPI.getAll()
      setServers(response.data)
    } catch (error) {
      message.error('获取上游服务器列表失败')
    }
  }

  useEffect(() => {
    fetchRules()
    fetchServers()
  }, [])

  const handleCreate = () => {
    setEditingRule(null)
    form.resetFields()
    setModalVisible(true)
  }

  const handleEdit = (rule: ProxyRule) => {
    setEditingRule(rule)
    form.setFieldsValue({
      ...rule,
      add_headers: rule.add_headers ? JSON.stringify(rule.add_headers, null, 2) : ''
    })
    setModalVisible(true)
  }

  const handleDelete = async (ruleId: number) => {
    try {
      await proxyRuleAPI.delete(ruleId)
      message.success('删除成功')
      fetchRules()
    } catch (error) {
      message.error('删除失败')
    }
  }

  const handleSubmit = async (values: any) => {
    try {
      const submitData = {
        ...values,
        add_headers: values.add_headers ? JSON.parse(values.add_headers) : undefined
      }

      if (editingRule) {
        await proxyRuleAPI.update(editingRule.rule_id, submitData)
        message.success('更新成功')
      } else {
        await proxyRuleAPI.create(submitData)
        message.success('创建成功')
      }

      setModalVisible(false)
      fetchRules()
    } catch (error) {
      message.error(editingRule ? '更新失败' : '创建失败')
    }
  }

  const getServerName = (serverId: number) => {
    const server = servers.find(s => s.server_id === serverId)
    return server ? server.server_name : `服务器${serverId}`
  }

  const columns = [
    {
      title: '规则名称',
      dataIndex: 'rule_name',
      key: 'rule_name',
      width: 150
    },
    {
      title: '规则类型',
      dataIndex: 'rule_type',
      key: 'rule_type',
      width: 120,
      render: (type: string) => {
        const colorMap: Record<string, string> = {
          path_match: 'blue',
          header_match: 'green',
          model_match: 'purple'
        }
        const labelMap: Record<string, string> = {
          path_match: '路径匹配',
          header_match: '请求头匹配',
          model_match: '模型匹配'
        }
        return <Tag color={colorMap[type]}>{labelMap[type]}</Tag>
      }
    },
    {
      title: '匹配模式',
      dataIndex: 'match_pattern',
      key: 'match_pattern',
      width: 200,
      ellipsis: true
    },
    {
      title: '目标服务器',
      dataIndex: 'target_server_id',
      key: 'target_server_id',
      width: 150,
      render: (serverId: number) => getServerName(serverId)
    },
    {
      title: '路径重写',
      dataIndex: 'rewrite_path',
      key: 'rewrite_path',
      width: 150,
      ellipsis: true
    },
    {
      title: '优先级',
      dataIndex: 'priority',
      key: 'priority',
      width: 80
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
      title: '操作',
      key: 'action',
      width: 120,
      render: (_: any, record: ProxyRule) => (
        <Space>
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定要删除这个代理规则吗？"
            onConfirm={() => handleDelete(record.rule_id)}
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
      <Card 
        title={
          <Space>
            <ApiOutlined />
            <span>代理规则管理</span>
          </Space>
        }
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
            添加代理规则
          </Button>
        }
      >
        <Table
          columns={columns}
          dataSource={rules}
          rowKey="rule_id"
          loading={loading}
          pagination={{
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条记录`
          }}
        />
      </Card>

      <Modal
        title={
          <Space>
            <ApiOutlined />
            <span>{editingRule ? '编辑' : '添加'}代理规则</span>
          </Space>
        }
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
        width={700}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          initialValues={{
            priority: 100,
            status: 1
          }}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="rule_name"
                label="规则名称"
                rules={[{ required: true, message: '请输入规则名称' }]}
              >
                <Input placeholder="如：DS1-5B聊天接口代理" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="rule_type"
                label="规则类型"
                rules={[{ required: true, message: '请选择规则类型' }]}
              >
                <Select placeholder="请选择规则类型">
                  {ruleTypeOptions.map(option => (
                    <Option key={option.value} value={option.value}>
                      {option.label}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="match_pattern"
                label="匹配模式"
                rules={[{ required: true, message: '请输入匹配模式' }]}
              >
                <Input placeholder="如：/ds1_5b/v1/chat/completions" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="target_server_id"
                label="目标服务器"
                rules={[{ required: true, message: '请选择目标服务器' }]}
              >
                <Select placeholder="请选择目标服务器">
                  {servers.map(server => (
                    <Option key={server.server_id} value={server.server_id}>
                      {server.server_name}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="rewrite_path"
                label="路径重写"
              >
                <Input placeholder="如：/v1/chat/completions（可选）" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="priority"
                label="优先级"
                rules={[{ required: true, message: '请输入优先级' }]}
              >
                <InputNumber min={1} max={100} style={{ width: '100%' }} placeholder="100" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="status"
                label="状态"
                valuePropName="checked"
                initialValue={true}
              >
                <Switch checkedChildren="启用" unCheckedChildren="禁用" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                {editingRule ? '更新' : '创建'}
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

export default ProxyRuleList 