import React, { useState, useEffect } from 'react'
import {
  Table,
  Button,
  Modal,
  Form,
  Input,
  Select,
  Switch,
  Space,
  Tag,
  message,
  Popconfirm,
  Card,
  Row,
  Col,
  Tabs,
  InputNumber,
  Divider,
  Typography
} from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined, SettingOutlined } from '@ant-design/icons'
import { nginxConfigAPI, NginxConfig, NginxConfigCreate, NginxConfigUpdate } from '../services/api'

const { Option } = Select
const { TextArea } = Input
const { TabPane } = Tabs
const { Title, Text } = Typography

const NginxConfigList: React.FC = () => {
  const [configs, setConfigs] = useState<{ [key: string]: NginxConfig[] }>({})
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [editingConfig, setEditingConfig] = useState<NginxConfig | null>(null)
  const [activeTab, setActiveTab] = useState('global')
  const [form] = Form.useForm()

  const configTypes = [
    { key: 'global', label: '全局配置', description: '基础全局设置' },
    { key: 'http', label: 'HTTP配置', description: 'HTTP核心设置' },
    { key: 'server', label: '服务器配置', description: '服务器设置' }
  ]

  const fetchConfigs = async () => {
    setLoading(true)
    try {
      const configsData: { [key: string]: NginxConfig[] } = {}
      for (const type of configTypes) {
        const response = await nginxConfigAPI.getByType(type.key)
        configsData[type.key] = response.data
      }
      setConfigs(configsData)
    } catch (error) {
      message.error('获取nginx配置列表失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchConfigs()
  }, [])

  const handleCreate = () => {
    setEditingConfig(null)
    form.resetFields()
    form.setFieldsValue({ config_type: activeTab })
    setModalVisible(true)
  }

  const handleEdit = (config: NginxConfig) => {
    setEditingConfig(config)
    // 解析配置值到表单字段
    const configValue = config.config_value || {}
    form.setFieldsValue({
      ...config,
      ...configValue
    })
    setModalVisible(true)
  }

  const handleDelete = async (configId: number) => {
    try {
      await nginxConfigAPI.delete(configId)
      message.success('删除成功')
      fetchConfigs()
    } catch (error) {
      message.error('删除失败')
    }
  }

  const handleSubmit = async (values: any) => {
    try {
      const { config_type, config_name, description, status, ...configValue } = values
      
      const submitData = {
        config_type,
        config_name,
        description,
        status: status ? 1 : 0,
        config_value: configValue
      }

      if (editingConfig) {
        await nginxConfigAPI.update(editingConfig.config_id, submitData)
        message.success('更新成功')
      } else {
        await nginxConfigAPI.create(submitData)
        message.success('创建成功')
      }

      setModalVisible(false)
      fetchConfigs()
    } catch (error) {
      message.error(editingConfig ? '更新失败' : '创建失败')
    }
  }

  // 渲染全局配置表单
  const renderGlobalForm = () => (
    <>
      <Row gutter={16}>
        <Col span={12}>
          <Form.Item
            name="worker_processes"
            label="工作进程数"
            rules={[{ required: true, message: '请输入工作进程数' }]}
          >
            <Input placeholder="auto 或数字" />
          </Form.Item>
        </Col>
        <Col span={12}>
          <Form.Item
            name="error_log"
            label="错误日志路径"
            rules={[{ required: true, message: '请输入错误日志路径' }]}
          >
            <Input placeholder="/var/log/nginx/error.log warn" />
          </Form.Item>
        </Col>
      </Row>
      <Row gutter={16}>
        <Col span={12}>
          <Form.Item
            name="pid"
            label="PID文件路径"
            rules={[{ required: true, message: '请输入PID文件路径' }]}
          >
            <Input placeholder="/var/run/nginx.pid" />
          </Form.Item>
        </Col>
        <Col span={12}>
          <Form.Item
            name="worker_connections"
            label="工作进程连接数"
            rules={[{ required: true, message: '请输入连接数' }]}
          >
            <InputNumber min={1} max={65535} style={{ width: '100%' }} placeholder="1024" />
          </Form.Item>
        </Col>
      </Row>
    </>
  )

  // 渲染HTTP配置表单
  const renderHttpForm = () => (
    <>
      <Row gutter={16}>
        <Col span={12}>
          <Form.Item
            name="client_max_body_size"
            label="最大上传文件大小"
            rules={[{ required: true, message: '请输入最大文件大小' }]}
          >
            <Input placeholder="100m" />
          </Form.Item>
        </Col>
        <Col span={12}>
          <Form.Item
            name="proxy_connect_timeout"
            label="连接超时时间"
            rules={[{ required: true, message: '请输入连接超时时间' }]}
          >
            <Input placeholder="900s" />
          </Form.Item>
        </Col>
      </Row>
      <Row gutter={16}>
        <Col span={12}>
          <Form.Item
            name="proxy_read_timeout"
            label="读取超时时间"
            rules={[{ required: true, message: '请输入读取超时时间' }]}
          >
            <Input placeholder="1800s" />
          </Form.Item>
        </Col>
        <Col span={12}>
          <Form.Item
            name="keepalive_timeout"
            label="Keep-Alive超时"
            rules={[{ required: true, message: '请输入Keep-Alive超时' }]}
          >
            <Input placeholder="180s" />
          </Form.Item>
        </Col>
      </Row>
      <Row gutter={16}>
        <Col span={12}>
          <Form.Item
            name="proxy_buffers"
            label="代理缓冲区"
          >
            <Input placeholder="4 256k" />
          </Form.Item>
        </Col>
        <Col span={12}>
          <Form.Item
            name="proxy_buffer_size"
            label="代理缓冲区大小"
          >
            <Input placeholder="256k" />
          </Form.Item>
        </Col>
      </Row>
      <Row gutter={16}>
        <Col span={12}>
          <Form.Item
            name="keepalive_requests"
            label="Keep-Alive请求数"
          >
            <InputNumber min={1} style={{ width: '100%' }} placeholder="100" />
          </Form.Item>
        </Col>
        <Col span={12}>
          <Form.Item
            name="sendfile"
            label="Sendfile"
          >
            <Select placeholder="选择sendfile设置">
              <Option value="on">开启</Option>
              <Option value="off">关闭</Option>
            </Select>
          </Form.Item>
        </Col>
      </Row>
    </>
  )

  // 渲染服务器配置表单
  const renderServerForm = () => (
    <>
      <Row gutter={16}>
        <Col span={12}>
          <Form.Item
            name="listen"
            label="监听端口"
            rules={[{ required: true, message: '请输入监听端口' }]}
          >
            <InputNumber min={1} max={65535} style={{ width: '100%' }} placeholder="8080" />
          </Form.Item>
        </Col>
        <Col span={12}>
          <Form.Item
            name="server_name"
            label="服务器名称"
            rules={[{ required: true, message: '请输入服务器名称' }]}
          >
            <Input placeholder="example.com www.example.com" />
          </Form.Item>
        </Col>
      </Row>
      <Row gutter={16}>
        <Col span={12}>
          <Form.Item
            name="access_log"
            label="访问日志路径"
          >
            <Input placeholder="/var/log/nginx/access.log main" />
          </Form.Item>
        </Col>
        <Col span={12}>
          <Form.Item
            name="proxy_cache"
            label="代理缓存"
          >
            <Select placeholder="选择代理缓存设置">
              <Option value="on">开启</Option>
              <Option value="off">关闭</Option>
            </Select>
          </Form.Item>
        </Col>
      </Row>
      <Row gutter={16}>
        <Col span={12}>
          <Form.Item
            name="proxy_buffering"
            label="代理缓冲"
          >
            <Select placeholder="选择代理缓冲设置">
              <Option value="on">开启</Option>
              <Option value="off">关闭</Option>
            </Select>
          </Form.Item>
        </Col>
      </Row>
    </>
  )

  const columns = [
    {
      title: '配置名称',
      dataIndex: 'config_name',
      key: 'config_name',
      width: 150
    },
    {
      title: '配置值',
      dataIndex: 'config_value',
      key: 'config_value',
      width: 400,
      render: (value: any) => {
        if (!value) return '-'
        if (typeof value === 'object') {
          return (
            <div style={{ maxHeight: '100px', overflow: 'auto' }}>
              {Object.entries(value).map(([key, val]) => (
                <div key={key} style={{ fontSize: '12px', marginBottom: '2px' }}>
                  <Text strong>{key}:</Text> {String(val)}
                </div>
              ))}
            </div>
          )
        }
        return String(value)
      }
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      width: 200,
      ellipsis: true
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
      render: (_: any, record: NginxConfig) => (
        <Space>
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定要删除这个配置吗？"
            onConfirm={() => handleDelete(record.config_id)}
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

  const renderFormByType = () => {
    switch (activeTab) {
      case 'global':
        return renderGlobalForm()
      case 'http':
        return renderHttpForm()
      case 'server':
        return renderServerForm()
      default:
        return null
    }
  }

  return (
    <div style={{ padding: '24px' }}>
      <Card 
        title={
          <Space>
            <SettingOutlined />
            <span>Nginx配置管理</span>
          </Space>
        }
      >
        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          {configTypes.map(type => (
            <TabPane tab={type.label} key={type.key}>
              <div style={{ marginBottom: '16px' }}>
                <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
                  添加{type.label}
                </Button>
                <Text type="secondary" style={{ marginLeft: '12px' }}>
                  {type.description}
                </Text>
              </div>
              <Table
                columns={columns}
                dataSource={configs[type.key] || []}
                rowKey="config_id"
                loading={loading}
                pagination={{
                  showSizeChanger: true,
                  showQuickJumper: true,
                  showTotal: (total) => `共 ${total} 条记录`
                }}
              />
            </TabPane>
          ))}
        </Tabs>
      </Card>

      <Modal
        title={
          <Space>
            <SettingOutlined />
            <span>{editingConfig ? '编辑' : '添加'}{configTypes.find(t => t.key === activeTab)?.label}</span>
          </Space>
        }
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
        width={800}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="config_type"
                label="配置类型"
                rules={[{ required: true, message: '请选择配置类型' }]}
              >
                <Select placeholder="请选择配置类型" disabled>
                  {configTypes.map(type => (
                    <Option key={type.key} value={type.key}>
                      {type.label}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="config_name"
                label="配置名称"
                rules={[{ required: true, message: '请输入配置名称' }]}
              >
                <Input placeholder="请输入配置名称" />
              </Form.Item>
            </Col>
          </Row>

          <Divider orientation="left">配置参数</Divider>
          
          {renderFormByType()}

          <Row gutter={16}>
            <Col span={24}>
              <Form.Item
                name="description"
                label="配置描述"
              >
                <Input placeholder="请输入配置描述" />
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
                {editingConfig ? '更新' : '创建'}
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

export default NginxConfigList 