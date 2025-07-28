import React, { useState, useEffect } from 'react'
import {
  Card,
  Form,
  Input,
  Button,
  Space,
  Row,
  Col,
  Divider,
  Alert,
  Table,
  Tag,
  Descriptions,
  message,
  Tabs,
  Typography
} from 'antd'
import { SendOutlined, CheckCircleOutlined, CloseCircleOutlined, InfoCircleOutlined } from '@ant-design/icons'
import { routeAPI, namespaceAPI, RouteTestRequest, RouteTestResponse, RuleValidationRequest, RuleValidationResponse, Namespace } from '../services/api'

const { TextArea } = Input
const { Title, Text } = Typography
const { TabPane } = Tabs

const RouteTest: React.FC = () => {
  const [routeForm] = Form.useForm()
  const [validationForm] = Form.useForm()
  const [namespaces, setNamespaces] = useState<Namespace[]>([])
  const [routeResult, setRouteResult] = useState<RouteTestResponse | null>(null)
  const [validationResult, setValidationResult] = useState<RuleValidationResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [validationLoading, setValidationLoading] = useState(false)

  useEffect(() => {
    fetchNamespaces()
  }, [])

  const fetchNamespaces = async () => {
    try {
      const response = await namespaceAPI.getAll()
      setNamespaces(response.data)
    } catch (error) {
      message.error('获取命名空间列表失败')
      console.error('获取命名空间列表失败:', error)
    }
  }

  const handleRouteTest = async (values: any) => {
    setLoading(true)
    try {
      const requestData: RouteTestRequest = {
        headers: values.headers ? JSON.parse(values.headers) : {},
        query_params: values.query_params ? JSON.parse(values.query_params) : {},
        body: values.body ? JSON.parse(values.body) : {},
        path: values.path || ''
      }

      const response = await routeAPI.routeToNamespace(requestData)
      setRouteResult(response.data)
      message.success('路由测试完成')
    } catch (error) {
      message.error('路由测试失败')
      console.error('路由测试失败:', error)
      setRouteResult(null)
    } finally {
      setLoading(false)
    }
  }

  const handleValidationTest = async (values: any) => {
    setValidationLoading(true)
    try {
      const requestData: RuleValidationRequest = {
        namespace_id: values.namespace_id,
        headers: values.headers ? JSON.parse(values.headers) : {},
        query_params: values.query_params ? JSON.parse(values.query_params) : {},
        body: values.body ? JSON.parse(values.body) : {},
        path: values.path || ''
      }

      const response = await routeAPI.validateNamespaceRules(values.namespace_id, requestData)
      setValidationResult(response.data)
      message.success('规则验证完成')
    } catch (error) {
      message.error('规则验证失败')
      console.error('规则验证失败:', error)
      setValidationResult(null)
    } finally {
      setValidationLoading(false)
    }
  }

  const renderRouteResult = () => {
    if (!routeResult) return null

    return (
      <Card title="路由测试结果" style={{ marginTop: '16px' }}>
        <Descriptions bordered>
          <Descriptions.Item label="是否匹配" span={3}>
            <Tag color={routeResult.matched ? 'green' : 'red'} icon={routeResult.matched ? <CheckCircleOutlined /> : <CloseCircleOutlined />}>
              {routeResult.matched ? '匹配成功' : '未匹配'}
            </Tag>
          </Descriptions.Item>
          {routeResult.matched && (
            <>
              <Descriptions.Item label="命名空间ID">{routeResult.namespace_id}</Descriptions.Item>
              <Descriptions.Item label="命名空间代码">{routeResult.namespace_code}</Descriptions.Item>
              <Descriptions.Item label="命名空间名称">{routeResult.namespace_name}</Descriptions.Item>
              <Descriptions.Item label="路由规则ID">{routeResult.route_id}</Descriptions.Item>
            </>
          )}
        </Descriptions>
      </Card>
    )
  }

  const renderValidationResult = () => {
    if (!validationResult) return null

    const ruleColumns = [
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
            concurrent_limit: 'blue',
            qps_limit: 'green',
            field_match: 'orange'
          }
          return (
            <Tag color={colorMap[type] || 'default'}>
              {type}
            </Tag>
          )
        }
      },
      {
        title: '验证结果',
        dataIndex: 'passed',
        key: 'passed',
        width: 120,
        render: (passed: boolean) => (
          <Tag color={passed ? 'green' : 'red'} icon={passed ? <CheckCircleOutlined /> : <CloseCircleOutlined />}>
            {passed ? '通过' : '失败'}
          </Tag>
        )
      },
      {
        title: '详细信息',
        dataIndex: 'details',
        key: 'details',
        render: (details: any) => {
          if (!details) return '-'
          return (
            <div>
              {Object.entries(details).map(([key, value]) => (
                <div key={key}>
                  <Text strong>{key}:</Text> {String(value)}
                </div>
              ))}
            </div>
          )
        }
      }
    ]

    return (
      <Card title="规则验证结果" style={{ marginTop: '16px' }}>
        <Descriptions bordered style={{ marginBottom: '16px' }}>
          <Descriptions.Item label="命名空间" span={2}>
            {validationResult.namespace_name} ({validationResult.namespace_code})
          </Descriptions.Item>
          <Descriptions.Item label="最终结果">
            <Tag color={validationResult.allowed ? 'green' : 'red'} icon={validationResult.allowed ? <CheckCircleOutlined /> : <CloseCircleOutlined />}>
              {validationResult.allowed ? '允许通过' : '拒绝请求'}
            </Tag>
          </Descriptions.Item>
        </Descriptions>

        <Divider />

        <h4>规则验证详情：</h4>
        <Table
          columns={ruleColumns}
          dataSource={validationResult.rules}
          rowKey="rule_id"
          pagination={false}
          size="small"
        />
      </Card>
    )
  }

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ marginBottom: '16px' }}>
        <Title level={2}>路由测试工具</Title>
        <Text type="secondary">测试报文路由和命名空间规则验证</Text>
      </div>

      <Tabs defaultActiveKey="route">
        <TabPane tab="路由测试" key="route">
          <Card title="报文路由测试">
            <Alert
              message="路由测试说明"
              description="输入报文内容，测试会被路由到哪个命名空间。系统会根据配置的路由规则进行匹配。"
              type="info"
              showIcon
              style={{ marginBottom: '16px' }}
            />

            <Form
              form={routeForm}
              layout="vertical"
              onFinish={handleRouteTest}
            >
              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    name="headers"
                    label="请求头 (JSON格式)"
                  >
                    <TextArea
                      rows={4}
                      placeholder={`{
  "channelcode": "wechat001",
  "user_id": "VIP123",
  "client_type": "mobile"
}`}
                    />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    name="query_params"
                    label="查询参数 (JSON格式)"
                  >
                    <TextArea
                      rows={4}
                      placeholder={`{
  "app_id": "wx_app_001",
  "version": "1.0"
}`}
                    />
                  </Form.Item>
                </Col>
              </Row>

              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    name="body"
                    label="请求体 (JSON格式)"
                  >
                    <TextArea
                      rows={4}
                      placeholder={`{
  "message": "Hello World",
  "data": {
    "user_id": "VIP123"
  }
}`}
                    />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    name="path"
                    label="请求路径"
                  >
                    <Input placeholder="/api/v1/chat" />
                  </Form.Item>
                </Col>
              </Row>

              <Form.Item>
                <Space>
                  <Button
                    type="primary"
                    icon={<SendOutlined />}
                    htmlType="submit"
                    loading={loading}
                  >
                    测试路由
                  </Button>
                  <Button onClick={() => routeForm.resetFields()}>
                    清空
                  </Button>
                </Space>
              </Form.Item>
            </Form>

            {renderRouteResult()}
          </Card>
        </TabPane>

        <TabPane tab="规则验证" key="validation">
          <Card title="命名空间规则验证">
            <Alert
              message="规则验证说明"
              description="选择命名空间并输入报文内容，验证该命名空间内的所有规则是否通过。"
              type="info"
              showIcon
              style={{ marginBottom: '16px' }}
            />

            <Form
              form={validationForm}
              layout="vertical"
              onFinish={handleValidationTest}
            >
              <Row gutter={16}>
                <Col span={8}>
                  <Form.Item
                    name="namespace_id"
                    label="选择命名空间"
                    rules={[{ required: true, message: '请选择命名空间' }]}
                  >
                    <Input.Group compact>
                      <Input
                        style={{ width: '100%' }}
                        placeholder="请选择命名空间"
                        disabled
                        value={namespaces.find(ns => ns.namespace_id === validationForm.getFieldValue('namespace_id'))?.namespace_name || ''}
                      />
                    </Input.Group>
                  </Form.Item>
                </Col>
                <Col span={16}>
                  <Form.Item label="命名空间选择">
                    <Space wrap>
                      {namespaces.map(namespace => (
                        <Button
                          key={namespace.namespace_id}
                          type={validationForm.getFieldValue('namespace_id') === namespace.namespace_id ? 'primary' : 'default'}
                          onClick={() => validationForm.setFieldsValue({ namespace_id: namespace.namespace_id })}
                        >
                          {namespace.namespace_name} ({namespace.namespace_code})
                        </Button>
                      ))}
                    </Space>
                  </Form.Item>
                </Col>
              </Row>

              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    name="headers"
                    label="请求头 (JSON格式)"
                  >
                    <TextArea
                      rows={4}
                      placeholder={`{
  "channelcode": "wechat001",
  "user_id": "VIP123"
}`}
                    />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    name="query_params"
                    label="查询参数 (JSON格式)"
                  >
                    <TextArea
                      rows={4}
                      placeholder={`{
  "app_id": "wx_app_001"
}`}
                    />
                  </Form.Item>
                </Col>
              </Row>

              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    name="body"
                    label="请求体 (JSON格式)"
                  >
                    <TextArea
                      rows={4}
                      placeholder={`{
  "message": "Hello World",
  "user_id": "VIP123"
}`}
                    />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    name="path"
                    label="请求路径"
                  >
                    <Input placeholder="/api/v1/chat" />
                  </Form.Item>
                </Col>
              </Row>

              <Form.Item>
                <Space>
                  <Button
                    type="primary"
                    icon={<CheckCircleOutlined />}
                    htmlType="submit"
                    loading={validationLoading}
                  >
                    验证规则
                  </Button>
                  <Button onClick={() => validationForm.resetFields()}>
                    清空
                  </Button>
                </Space>
              </Form.Item>
            </Form>

            {renderValidationResult()}
          </Card>
        </TabPane>
      </Tabs>
    </div>
  )
}

export default RouteTest 