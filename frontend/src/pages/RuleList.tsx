import React, { useState, useEffect } from 'react'
import {
  Table,
  Button,
  Modal,
  Form,
  Input,
  Select,
  Space,
  Tag,
  message,
  Popconfirm,
  Card,
  Row,
  Col,
  InputNumber,
  Switch,
  Divider,
  Alert
} from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined, InfoCircleOutlined } from '@ant-design/icons'
import { namespaceAPI, namespaceRuleAPI, Namespace, NamespaceRule, NamespaceRuleCreate, NamespaceRuleUpdate, RuleType } from '../services/api'

const { Option } = Select
const { TextArea } = Input

const RuleList: React.FC = () => {
  const [namespaces, setNamespaces] = useState<Namespace[]>([])
  const [rules, setRules] = useState<NamespaceRule[]>([])
  const [ruleTypes, setRuleTypes] = useState<RuleType[]>([])
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [editingRule, setEditingRule] = useState<NamespaceRule | null>(null)
  const [selectedNamespace, setSelectedNamespace] = useState<number | null>(null)
  const [form] = Form.useForm()

  useEffect(() => {
    fetchNamespaces()
    fetchRuleTypes()
  }, [])

  useEffect(() => {
    if (selectedNamespace) {
      fetchRules(selectedNamespace)
    }
  }, [selectedNamespace])

  const fetchNamespaces = async () => {
    try {
      const response = await namespaceAPI.getAll()
      setNamespaces(response.data)
      if (response.data.length > 0 && !selectedNamespace) {
        setSelectedNamespace(response.data[0].namespace_id)
      }
    } catch (error) {
      message.error('获取命名空间列表失败')
      console.error('获取命名空间列表失败:', error)
    }
  }

  const fetchRuleTypes = async () => {
    try {
      const response = await namespaceRuleAPI.getTypes()
      setRuleTypes(response.data.rule_types)
    } catch (error) {
      message.error('获取规则类型失败')
      console.error('获取规则类型失败:', error)
    }
  }

  const fetchRules = async (namespaceId: number) => {
    setLoading(true)
    try {
      const response = await namespaceRuleAPI.getByNamespace(namespaceId)
      setRules(response.data)
    } catch (error) {
      message.error('获取规则列表失败')
      console.error('获取规则列表失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = () => {
    setEditingRule(null)
    setModalVisible(true)
    form.resetFields()
    form.setFieldsValue({
      namespace_id: selectedNamespace,
      priority: 1,
      status: 1
    })
  }

  const handleEdit = (record: NamespaceRule) => {
    setEditingRule(record)
    setModalVisible(true)
    form.setFieldsValue({
      namespace_id: record.namespace_id,
      rule_name: record.rule_name,
      rule_type: record.rule_type,
      rule_config: record.rule_config,
      priority: record.priority,
      status: record.status
    })
  }

  const handleDelete = async (id: number) => {
    try {
      await namespaceRuleAPI.delete(id)
      message.success('删除成功')
      if (selectedNamespace) {
        fetchRules(selectedNamespace)
      }
    } catch (error) {
      message.error('删除失败')
      console.error('删除失败:', error)
    }
  }

  const handleSubmit = async (values: any) => {
    try {
      if (editingRule) {
        await namespaceRuleAPI.update(editingRule.rule_id, values)
        message.success('更新成功')
      } else {
        await namespaceRuleAPI.create(values)
        message.success('创建成功')
      }
      setModalVisible(false)
      if (selectedNamespace) {
        fetchRules(selectedNamespace)
      }
    } catch (error) {
      message.error(editingRule ? '更新失败' : '创建失败')
      console.error('操作失败:', error)
    }
  }

  const renderRuleConfigFields = (ruleType: string) => {
    const ruleTypeConfig = ruleTypes.find(rt => rt.type === ruleType)
    if (!ruleTypeConfig) return null

    switch (ruleType) {
      case 'matcher':
        return (
          <>
            <Form.Item
              name={['rule_config', 'matcher_type']}
              label="匹配字段来源"
              rules={[{ required: true, message: '请选择匹配字段来源' }]}
            >
              <Select placeholder="选择匹配字段的来源">
                <Option value="header">报文头 (Header)</Option>
                <Option value="body">请求体 (Body)</Option>
                <Option value="query">查询参数 (Query)</Option>
                <Option value="path">路径参数 (Path)</Option>
              </Select>
            </Form.Item>
            <Form.Item
              name={['rule_config', 'match_field']}
              label="匹配字段名称"
              rules={[{ required: true, message: '请输入匹配字段名称' }]}
            >
              <Input placeholder="如：user_type, client_level, api_version" />
            </Form.Item>
            <Form.Item
              name={['rule_config', 'match_operator']}
              label="匹配操作符"
              rules={[{ required: true, message: '请选择匹配操作符' }]}
            >
              <Select placeholder="选择匹配方式">
                <Option value="eq">等于 (=)</Option>
                <Option value="ne">不等于 (≠)</Option>
                <Option value="gt">大于 (&gt;)</Option>
                <Option value="gte">大于等于 (≥)</Option>
                <Option value="lt">小于 (&lt;)</Option>
                <Option value="lte">小于等于 (≤)</Option>
                <Option value="contains">包含</Option>
                <Option value="regex">正则匹配</Option>
              </Select>
            </Form.Item>
            <Form.Item
              name={['rule_config', 'match_value']}
              label="匹配值"
              rules={[{ required: true, message: '请输入匹配值' }]}
            >
              <Input placeholder="如：VIP, premium, 2.0" />
            </Form.Item>
            <Form.Item
              name={['rule_config', 'action']}
              label="匹配动作"
              rules={[{ required: true, message: '请选择匹配动作' }]}
            >
              <Select placeholder="选择匹配成功时的动作">
                <Option value="allow">允许通过</Option>
                <Option value="deny">拒绝请求</Option>
              </Select>
            </Form.Item>
          </>
        )

      case 'token_limit':
        return (
          <>
            <Form.Item
              name={['rule_config', 'model_name']}
              label="模型名称"
              rules={[{ required: true, message: '请输入模型名称' }]}
            >
              <Input placeholder="如：gpt-3.5-turbo, gpt-4, claude-3" />
            </Form.Item>
            <Form.Item
              name={['rule_config', 'max_tokens']}
              label="最大Token数量"
              rules={[{ required: true, message: '请输入最大Token数量' }]}
            >
              <InputNumber min={1} max={100000} style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item
              name={['rule_config', 'time_window_enabled']}
              label="启用时间窗口"
              valuePropName="checked"
            >
              <Switch />
            </Form.Item>
            <Form.Item
              noStyle
              shouldUpdate={(prevValues, currentValues) => 
                prevValues.rule_config?.time_window_enabled !== currentValues.rule_config?.time_window_enabled
              }
            >
              {({ getFieldValue }) => {
                const timeWindowEnabled = getFieldValue(['rule_config', 'time_window_enabled'])
                return timeWindowEnabled ? (
                  <>
                    <Form.Item
                      name={['rule_config', 'time_window_minutes']}
                      label="时间窗口(分钟)"
                      rules={[{ required: true, message: '请输入时间窗口' }]}
                    >
                      <InputNumber min={1} max={1440} style={{ width: '100%' }} />
                    </Form.Item>
                    <Form.Item
                      name={['rule_config', 'max_tokens_per_window']}
                      label="窗口内最大Token数"
                      rules={[{ required: true, message: '请输入窗口内最大Token数' }]}
                    >
                      <InputNumber min={1} max={1000000} style={{ width: '100%' }} />
                    </Form.Item>
                  </>
                ) : null
              }}
            </Form.Item>
          </>
        )

      case 'concurrent_limit':
        return (
          <>
            <Form.Item
              name={['rule_config', 'max_concurrent']}
              label="最大并发连接数"
              rules={[{ required: true, message: '请输入最大并发连接数' }]}
            >
              <InputNumber min={1} max={10000} style={{ width: '100%' }} />
            </Form.Item>
          </>
        )

      case 'rate_limit':
        return (
          <>
            <Form.Item
              name={['rule_config', 'max_qps']}
              label="最大QPS"
              rules={[{ required: true, message: '请输入最大QPS' }]}
            >
              <InputNumber min={1} max={10000} style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item
              name={['rule_config', 'time_window_seconds']}
              label="时间窗口(秒)"
              rules={[{ required: true, message: '请输入时间窗口' }]}
            >
              <InputNumber min={1} max={3600} style={{ width: '100%' }} />
            </Form.Item>
          </>
        )

      default:
        return (
          <Form.Item
            name="rule_config"
            label="规则配置"
            rules={[{ required: true, message: '请输入规则配置' }]}
          >
            <TextArea rows={4} placeholder="请输入JSON格式的规则配置" />
          </Form.Item>
        )
    }
  }

  const renderRuleConfig = (rule: NamespaceRule) => {
    const config = rule.rule_config
    if (!config) return '-'

    switch (rule.rule_type) {
      case 'concurrent_limit':
        return `最大并发: ${config.max_concurrent}, 超时: ${config.timeout_seconds}s`
      case 'qps_limit':
        return `最大QPS: ${config.max_qps}, 时间窗口: ${config.time_window_seconds}s`
      case 'field_match':
        return `${config.match_field} ${config.match_operator} ${config.match_value} → ${config.action === 'allow' ? '允许' : '拒绝'}`
      default:
        return JSON.stringify(config)
    }
  }

  const getRuleTypeName = (type: string) => {
    const ruleType = ruleTypes.find(rt => rt.type === type)
    return ruleType ? ruleType.name : type
  }

  const getRuleConfigHelp = (ruleType: string) => {
    switch (ruleType) {
      case 'matcher':
        return (
          <Alert
            message="报文匹配规则配置说明"
            description={
              <div>
                <p><strong>用途：</strong>基于报文内容进行访问控制，允许或拒绝特定条件的请求</p>
                <p><strong>配置要点：</strong></p>
                <ul>
                  <li><strong>匹配字段来源：</strong>选择要匹配的字段来源（报文头、请求体、查询参数、路径参数）</li>
                  <li><strong>匹配字段名称：</strong>输入具体的字段名（如：user_type、client_level、api_version等）</li>
                  <li><strong>匹配操作符：</strong>选择匹配方式（等于、包含、正则匹配等）</li>
                  <li><strong>匹配值：</strong>输入要匹配的具体值</li>
                  <li><strong>匹配动作：</strong>选择匹配成功时的处理动作（允许通过或拒绝请求）</li>
                </ul>
                <p><strong>示例：</strong>当请求体中的user_type字段等于"VIP"时，允许请求通过；当api_version小于"2.0"时，拒绝请求</p>
              </div>
            }
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
          />
        )
      
      case 'token_limit':
        return (
          <Alert
            message="Token限制规则配置说明"
            description={
              <div>
                <p><strong>用途：</strong>限制请求的Token数量，防止过度消耗AI模型资源</p>
                <p><strong>配置要点：</strong></p>
                <ul>
                  <li><strong>模型名称：</strong>指定要限制的AI模型（如：gpt-3.5-turbo、gpt-4）</li>
                  <li><strong>最大Token数量：</strong>单次请求允许的最大Token数</li>
                  <li><strong>时间窗口：</strong>可选，启用后可在指定时间窗口内限制Token总量</li>
                  <li><strong>窗口内最大Token数：</strong>时间窗口内允许的最大Token总数</li>
                </ul>
                <p><strong>示例：</strong>限制gpt-3.5-turbo模型单次请求最多4000个Token，每小时最多100000个Token</p>
              </div>
            }
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
          />
        )
      
      case 'concurrent_limit':
        return (
          <Alert
            message="并发限制规则配置说明"
            description={
              <div>
                <p><strong>用途：</strong>限制同时处理的请求数量，防止系统过载</p>
                <p><strong>配置要点：</strong></p>
                <ul>
                  <li><strong>最大并发连接数：</strong>同时允许的最大请求数量</li>
                </ul>
                <p><strong>示例：</strong>限制该命名空间最多同时处理100个请求</p>
              </div>
            }
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
          />
        )
      
      case 'rate_limit':
        return (
          <Alert
            message="QPS限制规则配置说明"
            description={
              <div>
                <p><strong>用途：</strong>限制每秒请求数，控制API调用频率</p>
                <p><strong>配置要点：</strong></p>
                <ul>
                  <li><strong>最大QPS：</strong>每秒允许的最大请求数</li>
                  <li><strong>时间窗口：</strong>统计QPS的时间窗口（秒）</li>
                </ul>
                <p><strong>示例：</strong>限制每秒最多10个请求，在60秒时间窗口内统计</p>
              </div>
            }
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
          />
        )
      
      default:
        return null
    }
  }

  const columns = [
    {
      title: '规则名称',
      dataIndex: 'rule_name',
      key: 'rule_name',
      width: 200
    },
    {
      title: '规则类型',
      dataIndex: 'rule_type',
      key: 'rule_type',
      width: 150,
      render: (type: string) => {
        const colorMap: Record<string, string> = {
          matcher: 'purple',
          token_limit: 'orange',
          concurrent_limit: 'blue',
          rate_limit: 'green'
        }
        return (
          <Tag color={colorMap[type] || 'default'}>
            {getRuleTypeName(type)}
          </Tag>
        )
      }
    },
    {
      title: '规则配置',
      dataIndex: 'rule_config',
      key: 'rule_config',
      render: (_: any, record: NamespaceRule) => renderRuleConfig(record)
    },
    {
      title: '优先级',
      dataIndex: 'priority',
      key: 'priority',
      width: 100,
      sorter: (a: NamespaceRule, b: NamespaceRule) => a.priority - b.priority
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
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
      render: (_: any, record: NamespaceRule) => (
        <Space size="small">
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定要删除这个规则吗？"
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

  const currentNamespace = namespaces.find(ns => ns.namespace_id === selectedNamespace)

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ marginBottom: '16px' }}>
        <h2>命名空间规则管理</h2>
        <p>管理命名空间内的各种限制和匹配规则</p>
      </div>

      <Card style={{ marginBottom: '16px' }}>
        <Row gutter={16} align="middle">
          <Col>
            <span style={{ marginRight: '8px' }}>选择命名空间:</span>
          </Col>
          <Col>
            <Select
              value={selectedNamespace}
              onChange={setSelectedNamespace}
              style={{ width: 300 }}
              placeholder="请选择命名空间"
            >
              {namespaces.map(namespace => (
                <Option key={namespace.namespace_id} value={namespace.namespace_id}>
                  {namespace.namespace_name} ({namespace.namespace_code})
                </Option>
              ))}
            </Select>
          </Col>
          <Col>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={handleCreate}
              disabled={!selectedNamespace}
            >
              创建规则
            </Button>
          </Col>
        </Row>
      </Card>

      {currentNamespace && (
        <Alert
          message={`当前命名空间: ${currentNamespace.namespace_name} (${currentNamespace.namespace_code})`}
          description={currentNamespace.description}
          type="info"
          showIcon
          style={{ marginBottom: '16px' }}
        />
      )}

      <Card>
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

      {/* 规则创建/编辑模态框 */}
      <Modal
        title={editingRule ? '编辑规则' : '创建规则'}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
        >
          <Form.Item name="namespace_id" hidden>
            <Input />
          </Form.Item>

          <Form.Item
            name="rule_name"
            label="规则名称"
            rules={[{ required: true, message: '请输入规则名称' }]}
          >
            <Input placeholder="请输入规则名称" />
          </Form.Item>

          <Form.Item
            name="rule_type"
            label="规则类型"
            rules={[{ required: true, message: '请选择规则类型' }]}
          >
            <Select
              placeholder="请选择规则类型"
              onChange={() => form.setFieldsValue({ rule_config: {} })}
            >
              {ruleTypes.map(ruleType => (
                <Option key={ruleType.type} value={ruleType.type}>
                  {ruleType.name} - {ruleType.description}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            noStyle
            shouldUpdate={(prevValues, currentValues) => prevValues.rule_type !== currentValues.rule_type}
          >
            {({ getFieldValue }) => {
              const ruleType = getFieldValue('rule_type')
              return ruleType ? (
                <>
                  {getRuleConfigHelp(ruleType)}
                  {renderRuleConfigFields(ruleType)}
                </>
              ) : null
            }}
          </Form.Item>

          <Form.Item
            name="priority"
            label="优先级"
            rules={[{ required: true, message: '请输入优先级' }]}
          >
            <InputNumber min={1} max={100} style={{ width: '100%' }} />
          </Form.Item>
          <div style={{ color: '#666', fontSize: '12px', marginTop: '-8px', marginBottom: '16px' }}>
            数字越小优先级越高
          </div>

          <Form.Item
            name="status"
            label="状态"
            valuePropName="checked"
            initialValue={true}
          >
            <Switch checkedChildren="启用" unCheckedChildren="禁用" />
          </Form.Item>

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

        <Divider />

        <div style={{ background: '#f5f5f5', padding: '12px', borderRadius: '4px' }}>
          <h4><InfoCircleOutlined /> 规则类型说明：</h4>
          <ul style={{ margin: 0, paddingLeft: '20px' }}>
            <li><strong>报文匹配</strong>：基于报文内容进行访问控制，允许或拒绝特定条件的请求</li>
            <li><strong>Token限制</strong>：限制请求的Token数量，防止过度消耗AI模型资源</li>
            <li><strong>并发限制</strong>：限制同时处理的请求数量，防止系统过载</li>
            <li><strong>QPS限制</strong>：限制每秒处理的请求数量，控制API调用频率</li>
          </ul>
        </div>
      </Modal>
    </div>
  )
}

export default RuleList 