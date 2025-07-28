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
  Descriptions,
  Divider
} from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined, SettingOutlined } from '@ant-design/icons'
import { namespaceAPI, namespaceRouteAPI, Namespace, NamespaceCreate, NamespaceUpdate, NamespaceRoute, NamespaceRouteCreate } from '../services/api'

const { Option } = Select
const { TextArea } = Input

const NamespaceList: React.FC = () => {
  const [namespaces, setNamespaces] = useState<Namespace[]>([])
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [routeModalVisible, setRouteModalVisible] = useState(false)
  const [editingNamespace, setEditingNamespace] = useState<Namespace | null>(null)
  const [editingRoute, setEditingRoute] = useState<NamespaceRoute | null>(null)
  const [currentNamespace, setCurrentNamespace] = useState<Namespace | null>(null)
  const [form] = Form.useForm()
  const [routeForm] = Form.useForm()

  // 匹配字段来源选项
  const matcherTypes = [
    { value: 'header', label: '报文头 (Header)' },
    { value: 'body', label: '请求体 (Body)' },
    { value: 'query', label: '查询参数 (Query)' },
    { value: 'path', label: '路径参数 (Path)' }
  ]

  // 匹配操作符选项
  const matchOperators = [
    { value: 'eq', label: '等于 (=)' },
    { value: 'ne', label: '不等于 (≠)' },
    { value: 'gt', label: '大于 (>)' },
    { value: 'gte', label: '大于等于 (≥)' },
    { value: 'lt', label: '小于 (<)' },
    { value: 'lte', label: '小于等于 (≤)' },
    { value: 'contains', label: '包含' },
    { value: 'regex', label: '正则匹配' }
  ]

  useEffect(() => {
    fetchNamespaces()
  }, [])

  const fetchNamespaces = async () => {
    setLoading(true)
    try {
      const response = await namespaceAPI.getAll()
      setNamespaces(response.data)
    } catch (error) {
      message.error('获取命名空间列表失败')
      console.error('获取命名空间列表失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = () => {
    setEditingNamespace(null)
    setModalVisible(true)
    form.resetFields()
  }

  const handleEdit = (record: Namespace) => {
    setEditingNamespace(record)
    setModalVisible(true)
    form.setFieldsValue({
      namespace_code: record.namespace_code,
      namespace_name: record.namespace_name,
      description: record.description,
      status: record.status
    })
  }

  const handleDelete = async (id: number) => {
    try {
      await namespaceAPI.delete(id)
      message.success('删除成功')
      fetchNamespaces()
    } catch (error) {
      message.error('删除失败')
      console.error('删除失败:', error)
    }
  }

  const handleSubmit = async (values: any) => {
    try {
      if (editingNamespace) {
        await namespaceAPI.update(editingNamespace.namespace_id, values)
        message.success('更新成功')
      } else {
        await namespaceAPI.create(values)
        message.success('创建成功')
      }
      setModalVisible(false)
      fetchNamespaces()
    } catch (error) {
      message.error(editingNamespace ? '更新失败' : '创建失败')
      console.error('操作失败:', error)
    }
  }

  const handleRouteConfig = async (namespace: Namespace) => {
    setCurrentNamespace(namespace)
    try {
      const response = await namespaceRouteAPI.getByNamespace(namespace.namespace_id)
      if (response.data) {
        setEditingRoute(response.data)
        routeForm.setFieldsValue({
          matcher_type: response.data.matcher_type || 'header',
          match_field: response.data.match_field,
          match_operator: response.data.match_operator,
          match_value: response.data.match_value
        })
      } else {
        setEditingRoute(null)
        routeForm.resetFields()
        routeForm.setFieldsValue({
          namespace_id: namespace.namespace_id,
          matcher_type: 'header' // 默认选择报文头
        })
      }
    } catch (error) {
      // 如果没有路由规则，创建新的
      setEditingRoute(null)
      routeForm.resetFields()
      routeForm.setFieldsValue({
        namespace_id: namespace.namespace_id,
        matcher_type: 'header' // 默认选择报文头
      })
    }
    setRouteModalVisible(true)
  }

  const handleRouteSubmit = async (values: any) => {
    try {
      await namespaceRouteAPI.createOrUpdate(currentNamespace!.namespace_id, values)
      message.success('路由规则保存成功')
      setRouteModalVisible(false)
    } catch (error) {
      message.error('路由规则保存失败')
      console.error('保存路由规则失败:', error)
    }
  }

  const handleDeleteRoute = async () => {
    try {
      await namespaceRouteAPI.delete(currentNamespace!.namespace_id)
      message.success('路由规则删除成功')
      setRouteModalVisible(false)
    } catch (error) {
      message.error('路由规则删除失败')
      console.error('删除路由规则失败:', error)
    }
  }

  const columns = [
    {
      title: '命名空间代码',
      dataIndex: 'namespace_code',
      key: 'namespace_code',
      width: 150
    },
    {
      title: '命名空间名称',
      dataIndex: 'namespace_name',
      key: 'namespace_name',
      width: 200
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true
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
      width: 200,
      render: (_: any, record: Namespace) => (
        <Space size="small">
          <Button
            type="link"
            icon={<SettingOutlined />}
            onClick={() => handleRouteConfig(record)}
          >
            路由配置
          </Button>
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定要删除这个命名空间吗？"
            onConfirm={() => handleDelete(record.namespace_id)}
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
      <div style={{ marginBottom: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2>命名空间管理</h2>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
          创建命名空间
        </Button>
      </div>

      <Card>
        <Table
          columns={columns}
          dataSource={namespaces}
          rowKey="namespace_id"
          loading={loading}
          pagination={{
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条记录`
          }}
        />
      </Card>

      {/* 命名空间创建/编辑模态框 */}
      <Modal
        title={editingNamespace ? '编辑命名空间' : '创建命名空间'}
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
          <Form.Item
            name="namespace_code"
            label="命名空间代码"
            rules={[
              { required: true, message: '请输入命名空间代码' },
              { pattern: /^[a-zA-Z0-9_-]+$/, message: '只能包含字母、数字、下划线和连字符' }
            ]}
          >
            <Input placeholder="如：wechat, alipay" disabled={!!editingNamespace} />
          </Form.Item>

          <Form.Item
            name="namespace_name"
            label="命名空间名称"
            rules={[{ required: true, message: '请输入命名空间名称' }]}
          >
            <Input placeholder="如：微信服务、支付宝服务" />
          </Form.Item>

          <Form.Item
            name="description"
            label="描述"
          >
            <TextArea rows={3} placeholder="请输入描述信息" />
          </Form.Item>

          <Form.Item
            name="status"
            label="状态"
            initialValue={1}
          >
            <Select>
              <Option value={1}>启用</Option>
              <Option value={0}>禁用</Option>
            </Select>
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                {editingNamespace ? '更新' : '创建'}
              </Button>
              <Button onClick={() => setModalVisible(false)}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 路由规则配置模态框 */}
      <Modal
        title={`路由规则配置 - ${currentNamespace?.namespace_name}`}
        open={routeModalVisible}
        onCancel={() => setRouteModalVisible(false)}
        footer={null}
        width={700}
      >
        {currentNamespace && (
          <div>
            <Descriptions title="命名空间信息" bordered size="small" style={{ marginBottom: '16px' }}>
              <Descriptions.Item label="命名空间代码">{currentNamespace.namespace_code}</Descriptions.Item>
              <Descriptions.Item label="命名空间名称">{currentNamespace.namespace_name}</Descriptions.Item>
              <Descriptions.Item label="描述">{currentNamespace.description}</Descriptions.Item>
            </Descriptions>

            <Divider />

            <Form
              form={routeForm}
              layout="vertical"
              onFinish={handleRouteSubmit}
            >
              <Form.Item name="namespace_id" hidden>
                <Input />
              </Form.Item>

              <Form.Item
                name="matcher_type"
                label="匹配字段来源"
                rules={[{ required: true, message: '请选择匹配字段来源' }]}
              >
                <Select placeholder="选择匹配字段的来源">
                  {matcherTypes.map(type => (
                    <Option key={type.value} value={type.value}>
                      {type.label}
                    </Option>
                  ))}
                </Select>
              </Form.Item>

              <Form.Item
                name="match_field"
                label="匹配字段名称"
                rules={[{ required: true, message: '请输入匹配字段名称' }]}
              >
                <Input placeholder="如：channelcode, app_id, user_id, Content-Type" />
              </Form.Item>

              <Form.Item
                name="match_operator"
                label="匹配操作符"
                rules={[{ required: true, message: '请选择匹配操作符' }]}
              >
                <Select placeholder="选择匹配方式">
                  {matchOperators.map(operator => (
                    <Option key={operator.value} value={operator.value}>
                      {operator.label}
                    </Option>
                  ))}
                </Select>
              </Form.Item>

              <Form.Item
                name="match_value"
                label="匹配值"
                rules={[{ required: true, message: '请输入匹配值' }]}
              >
                <Input placeholder="如：wechat001, VIP123" />
              </Form.Item>

              <Form.Item>
                <Space>
                  <Button type="primary" htmlType="submit">
                    {editingRoute ? '更新路由规则' : '创建路由规则'}
                  </Button>
                  {editingRoute && (
                    <Popconfirm
                      title="确定要删除这个路由规则吗？"
                      onConfirm={handleDeleteRoute}
                      okText="确定"
                      cancelText="取消"
                    >
                      <Button danger>删除路由规则</Button>
                    </Popconfirm>
                  )}
                  <Button onClick={() => setRouteModalVisible(false)}>
                    取消
                  </Button>
                </Space>
              </Form.Item>
            </Form>

            <Divider />

            <div style={{ background: '#f5f5f5', padding: '12px', borderRadius: '4px' }}>
              <h4>路由规则说明：</h4>
              <p>• 每个命名空间只能配置一个路由规则</p>
              <p>• 当报文匹配此规则时，会被路由到对应的命名空间</p>
              <p>• 匹配字段来源支持：报文头(Header)、请求体(Body)、查询参数(Query)、路径参数(Path)</p>
              <p>• 匹配操作符支持：等于(=)、不等于(≠)、大于(&gt;)、大于等于(≥)、小于(&lt;)、小于等于(≤)、包含、正则匹配</p>
              <p>• 匹配字段名称示例：channelcode、app_id、user_id、Content-Type、Authorization等</p>
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}

export default NamespaceList 