import React, { useState, useEffect } from 'react';
import {
  Card, Row, Col, Button, Typography, Statistic, Tag, Space,
  Select, Modal, Form, Input, Switch, InputNumber, Tabs,
  message, Table, Divider
} from 'antd';
import {
  PlusOutlined, EditOutlined, DeleteOutlined,
  CloudOutlined, LinkOutlined,
  DownloadOutlined, SaveOutlined, SyncOutlined
} from '@ant-design/icons';
import { upstreamApi, locationApi } from '../services/api';

// 路径重写配置接口
interface PathRewriteConfig {
  enabled: boolean;
  from: string;
  to: string;
}

// 路由规则接口
interface LocationRule {
  id?: string;
  path: string;
  upstream: string;
  proxy_cache?: boolean;
  proxy_buffering?: boolean;
  proxy_pass: string;
  is_regex?: boolean;
  path_rewrite?: PathRewriteConfig;
  limit_req?: {
    enabled: boolean;
    zone: string;
    burst: number;
    nodelay: boolean;
  };
  sse_support?: boolean;
  chunked_transfer?: boolean;
}

const { Title, Text } = Typography;
const { Option } = Select;
// TabPane已弃用，使用items属性
const { TextArea } = Input;

interface UpstreamServer {
  id?: string;
  name: string;
  servers: Array<{
    address: string;
    port: number;
    weight?: number;
  }>;
  keepalive?: number;
  health_check?: {
    enabled: boolean;
    path: string;
    interval: number;
  };
}



const ModelRouting: React.FC = () => {
  const [activeTab, setActiveTab] = useState('upstreams');
  const [upstreams, setUpstreams] = useState<UpstreamServer[]>([]);
  const [locations, setLocations] = useState<LocationRule[]>([]);
  const [isUpstreamModalVisible, setIsUpstreamModalVisible] = useState(false);
  const [isLocationModalVisible, setIsLocationModalVisible] = useState(false);
  const [editingUpstream, setEditingUpstream] = useState<UpstreamServer | null>(null);
  const [editingLocation, setEditingLocation] = useState<LocationRule | null>(null);
  const [upstreamForm] = Form.useForm();
  const [locationForm] = Form.useForm();
  // const [loading, setLoading] = useState(false);

  // 数据加载函数
  const loadUpstreams = async () => {
    try {
      // setLoading(true);
      const response = await upstreamApi.getUpstreams();
      if (response.code === 200) {
        // API返回格式: {data: {items: [...]}}
        const data = response.data?.items || response.data || [];
        setUpstreams(Array.isArray(data) ? data : []);
      } else {
        message.error('加载Upstream服务器失败');
      }
    } catch (error: any) {
      message.error('加载Upstream服务器失败');
      console.error('Load upstreams error:', error);
      // 确保在错误情况下设置空数组
      setUpstreams([]);
    } finally {
      // setLoading(false);
    }
  };

  const loadLocations = async () => {
    try {
      // setLoading(true);
      const response = await locationApi.getLocations();
      if (response.code === 200) {
        // API返回格式: {data: {items: [...]}}
        const data = response.data?.items || response.data || [];
        setLocations(Array.isArray(data) ? data : []);
      } else {
        message.error('加载Location规则失败');
      }
    } catch (error: any) {
      message.error('加载Location规则失败');
      console.error('Load locations error:', error);
      // 确保在错误情况下设置空数组
      setLocations([]);
    } finally {
      // setLoading(false);
    }
  };

  // 组件挂载时加载数据
  useEffect(() => {
    loadUpstreams();
    loadLocations();
  }, []);


  // 生成Nginx配置片段
  const generateUpstreamConfig = () => {
    let config = '';
    if (!Array.isArray(upstreams)) {
      return '// 没有可用的上游服务器配置';
    }
    upstreams.forEach(upstream => {
      config += `    upstream ${upstream.name} {\n`;
      upstream.servers.forEach(server => {
        config += `        server ${server.address}:${server.port};\n`;
      });
      if (upstream.keepalive) {
        config += `        keepalive ${upstream.keepalive};\n`;
      }
      config += `    }\n\n`;
    });
    return config;
  };

  const generateLocationConfig = () => {
    let config = '';
    if (!Array.isArray(locations)) {
      return '// 没有可用的Location规则配置';
    }
    locations.forEach(location => {
      config += `        location ${location.path} {\n`;
      if (location.proxy_cache === false) {
        config += `            proxy_cache off;\n`;
      }
      if (location.proxy_buffering === false) {
        config += `            proxy_buffering off;\n`;
      }
      // 添加路径重写规则
      if (location.path_rewrite?.enabled && location.path_rewrite.from && location.path_rewrite.to) {
        config += `            rewrite ^${location.path_rewrite.from}(.*)$ ${location.path_rewrite.to}$1 last;\n`;
      }
      config += `            proxy_pass ${location.proxy_pass};\n`;
      config += `        }\n\n`;
    });
    return config;
  };

  // Upstream管理
  const handleAddUpstream = () => {
    setEditingUpstream({
      name: '',
      servers: [{ address: '', port: 80 }],
      keepalive: 64,
      health_check: { enabled: false, path: '/health', interval: 30 }
    });
    setIsUpstreamModalVisible(true);
  };

  const handleEditUpstream = (upstream: UpstreamServer) => {
    setEditingUpstream({ ...upstream });
    setIsUpstreamModalVisible(true);
  };

  const handleDeleteUpstream = async (upstream: UpstreamServer) => {
    try {
      if (!upstream.id) {
        message.error('无法删除：缺少ID信息');
        return;
      }
      const response = await upstreamApi.deleteUpstream(upstream.id);
      if (response.code === 200) {
        message.success('Upstream删除成功');
        loadUpstreams(); // 重新加载数据
        loadLocations(); // 重新加载location数据
      } else {
        message.error(response.message || '删除失败');
      }
    } catch (error) {
      message.error('删除Upstream失败');
      console.error('Delete upstream error:', error);
    }
  };

  const handleSaveUpstream = async () => {
    try {
      const values = await upstreamForm.validateFields();
      
      const upstreamData = {
        name: values.name,
        servers: values.servers.map((s: any) => ({
          address: s.address,
          port: s.port,
          weight: s.weight
        })),
        keepalive: values.keepalive,
        health_check: {
          enabled: values.healthCheckEnabled,
          path: values.healthCheckPath,
          interval: values.healthCheckInterval
        }
      };

      let response;
      if (editingUpstream && editingUpstream.id) {
        // 更新现有upstream
        response = await upstreamApi.updateUpstream(editingUpstream.id, upstreamData);
      } else {
        // 创建新upstream
        response = await upstreamApi.createUpstream(upstreamData);
      }

      if (response.code === 200) {
        message.success(`Upstream${editingUpstream ? '更新' : '创建'}成功`);
        setIsUpstreamModalVisible(false);
        setEditingUpstream(null);
        upstreamForm.resetFields();
        loadUpstreams(); // 重新加载数据
      } else {
        message.error(response.message || '操作失败');
      }
    } catch (error) {
      message.error('保存Upstream失败');
      console.error('Save upstream error:', error);
    }
  };

  // Location管理
  const handleAddLocation = () => {
    setEditingLocation({
      path: '',
      upstream: '',
      proxy_cache: false,
      proxy_buffering: false,
      proxy_pass: '',
      path_rewrite: {
        enabled: false,
        from: '',
        to: ''
      }
    });
    setIsLocationModalVisible(true);
  };

  const handleEditLocation = (location: LocationRule) => {
    setEditingLocation({ ...location });
    setIsLocationModalVisible(true);
  };

  const handleDeleteLocation = async (location: LocationRule) => {
    try {
      if (!location.id) {
        message.error('无法删除：缺少ID信息');
        return;
      }
      const response = await locationApi.deleteLocation(location.id);
      if (response.code === 200) {
        message.success('Location规则删除成功');
        loadLocations(); // 重新加载数据
      } else {
        message.error(response.message || '删除失败');
      }
    } catch (error) {
      message.error('删除Location规则失败');
      console.error('Delete location error:', error);
    }
  };

  const handleSaveLocation = async () => {
    try {
      const values = await locationForm.validateFields();
      
      const locationData = {
        path: values.path,
        upstream: values.upstream,
        proxy_cache: values.proxy_cache,
        proxy_buffering: values.proxy_buffering,
        proxy_pass: `http://${values.upstream}${values.path}`,
        path_rewrite: values.path_rewrite || {
          enabled: false,
          from: '',
          to: ''
        }
      };

      let response;
      if (editingLocation && editingLocation.path) {
        // 更新现有location
        response = await locationApi.updateLocation(editingLocation.path, locationData);
      } else {
        // 创建新location
        response = await locationApi.createLocation(locationData);
      }

      if (response.code === 200) {
        message.success(`Location规则${editingLocation && editingLocation.path ? '更新' : '创建'}成功`);
        setIsLocationModalVisible(false);
        setEditingLocation(null);
        locationForm.resetFields();
        loadLocations(); // 重新加载数据
      } else {
        message.error(response.message || '操作失败');
      }
    } catch (error) {
      message.error('保存Location规则失败');
      console.error('Save location error:', error);
    }
  };


  // 导出配置
  const handleExportConfig = () => {
    const upstreamConfig = generateUpstreamConfig();
    const locationConfig = generateLocationConfig();
    const fullConfig = `# Upstream配置\n${upstreamConfig}\n# Location配置\n${locationConfig}`;
    
    const blob = new Blob([fullConfig], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'model-routing-config.txt';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    message.success('配置导出成功');
  };

  // 表格列定义
  const upstreamColumns = [
    {
      title: 'Upstream名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string) => <Text code>{text}</Text>
    },
    {
      title: '服务器列表',
      key: 'servers',
      render: (_: any, record: UpstreamServer) => (
        <div>
          {Array.isArray(record.servers) ? record.servers.map((server, index) => (
            <div key={index}>
              <Text code>{server.address}:{server.port}</Text>
            </div>
          )) : []}
        </div>
      )
    },
    {
      title: 'Keepalive',
      dataIndex: 'keepalive',
      key: 'keepalive',
      render: (value: number) => <Tag color="blue">{value}</Tag>
    },
    {
      title: '健康检查',
      key: 'health_check',
      render: (_: any, record: UpstreamServer) => (
        <Tag color={record.health_check?.enabled ? 'green' : 'red'}>
          {record.health_check?.enabled ? '启用' : '禁用'}
        </Tag>
      )
    },
    {
      title: '操作',
      key: 'actions',
      render: (_: any, record: UpstreamServer) => (
        <Space size="small">
          <Button type="link" icon={<EditOutlined />} size="small" onClick={() => handleEditUpstream(record)}>
            编辑
          </Button>
          <Button type="link" icon={<DeleteOutlined />} size="small" danger onClick={() => handleDeleteUpstream(record)}>
            删除
          </Button>
        </Space>
      )
    }
  ];

  const locationColumns = [
    {
      title: '路径匹配',
      dataIndex: 'path',
      key: 'path',
      render: (text: string) => <Text code>{text}</Text>
    },
    {
      title: '上游服务器',
      dataIndex: 'upstream',
      key: 'upstream',
      render: (text: string) => <Tag color="blue">{text}</Tag>
    },
    {
      title: '代理地址',
      dataIndex: 'proxy_pass',
      key: 'proxy_pass',
      render: (text: string) => <Text code>{text}</Text>
    },
    {
      title: '缓存设置',
      key: 'cache',
      render: (_: any, record: LocationRule) => (
        <Space size="small">
          <Tag color={record.proxy_cache ? 'green' : 'red'}>
            Cache: {record.proxy_cache ? 'ON' : 'OFF'}
          </Tag>
          <Tag color={record.proxy_buffering ? 'green' : 'red'}>
            Buffering: {record.proxy_buffering ? 'ON' : 'OFF'}
          </Tag>
        </Space>
      )
    },
    {
      title: '路径重写',
      key: 'path_rewrite',
      render: (_: any, record: LocationRule) => (
        <div>
          {record.path_rewrite?.enabled ? (
            <Space size="small">
              <Tag color="blue">启用</Tag>
              <Text code style={{ fontSize: '12px' }}>
                {record.path_rewrite.from} → {record.path_rewrite.to}
              </Text>
            </Space>
          ) : (
            <Tag color="default">禁用</Tag>
          )}
        </div>
      )
    },
    {
      title: '操作',
      key: 'actions',
      render: (_: any, record: LocationRule) => (
        <Space size="small">
          <Button type="link" icon={<EditOutlined />} size="small" onClick={() => handleEditLocation(record)}>
            编辑
          </Button>
          <Button type="link" icon={<DeleteOutlined />} size="small" danger onClick={() => handleDeleteLocation(record)}>
            删除
          </Button>
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
            <Title level={2} style={{ margin: 0, color: '#1d2129' }}>模型路由管理</Title>
            <Text style={{ color: '#4e5969', fontSize: '14px' }}>管理上游服务器和路由规则配置</Text>
          </div>
          <Space>
            <Button icon={<SyncOutlined />}>
              同步配置
            </Button>
            <Button icon={<DownloadOutlined />} onClick={handleExportConfig}>
              导出配置
            </Button>
            <Button type="primary" icon={<SaveOutlined />}>
              保存配置
            </Button>
          </Space>
        </div>
      </div>

      {/* 概览统计 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card style={{ borderRadius: 12, boxShadow: '0 4px 20px rgba(0, 0, 0, 0.08)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <Text style={{ color: '#4e5969', fontSize: '14px' }}>上游服务器</Text>
                <div style={{ marginTop: 8 }}>
                  <Statistic value={Array.isArray(upstreams) ? upstreams.length : 0} valueStyle={{ fontSize: '24px', fontWeight: 'bold', color: '#1d2129' }} />
                </div>
                <div style={{ marginTop: 12, display: 'flex', alignItems: 'center' }}>
                  <Tag color="blue" icon={<CloudOutlined />}>
                    负载均衡
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
                <CloudOutlined style={{ fontSize: 20 }} />
              </div>
            </div>
          </Card>
        </Col>

        <Col xs={24} sm={12} lg={6}>
          <Card style={{ borderRadius: 12, boxShadow: '0 4px 20px rgba(0, 0, 0, 0.08)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <Text style={{ color: '#4e5969', fontSize: '14px' }}>路由规则</Text>
                <div style={{ marginTop: 8 }}>
                  <Statistic value={Array.isArray(locations) ? locations.length : 0} valueStyle={{ fontSize: '24px', fontWeight: 'bold', color: '#1d2129' }} />
                </div>
                <div style={{ marginTop: 12, display: 'flex', alignItems: 'center' }}>
                  <Tag color="green" icon={<LinkOutlined />}>
                    代理转发
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
                <LinkOutlined style={{ fontSize: 20 }} />
              </div>
            </div>
          </Card>
        </Col>

      </Row>

      {/* 主配置区域 */}
      <Card style={{ borderRadius: 12, boxShadow: '0 4px 20px rgba(0, 0, 0, 0.08)' }}>
        <Tabs 
          activeKey={activeTab} 
          onChange={setActiveTab}
          items={[
            {
              key: "upstreams",
              label: "上游服务器",
              children: (
                <>
                  <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Title level={4} style={{ margin: 0 }}>上游服务器配置</Title>
                    <Button type="primary" icon={<PlusOutlined />} onClick={handleAddUpstream}>
                      添加服务器
                    </Button>
                  </div>
                  <Table
                    columns={upstreamColumns}
                    dataSource={upstreams}
                    rowKey="id"
                    pagination={{ pageSize: 10 }}
                  />
                </>
              )
            },
            {
              key: "locations",
              label: "路由规则",
              children: (
                <>
                  <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Title level={4} style={{ margin: 0 }}>路由规则配置</Title>
                    <Button type="primary" icon={<PlusOutlined />} onClick={handleAddLocation}>
                      添加规则
                    </Button>
                  </div>
                  <Table
                    columns={locationColumns}
                    dataSource={locations}
                    rowKey="id"
                    pagination={{ pageSize: 10 }}
                  />
                </>
              )
            },
            {
              key: "preview",
              label: "配置预览",
              children: (
                <>
                  <div style={{ marginBottom: 16 }}>
                    <Title level={4} style={{ margin: 0 }}>Nginx配置预览</Title>
                    <Text style={{ color: '#8c8c8c' }}>以下配置将同步到统一配置管理页面</Text>
                  </div>
                  
                  <div style={{ marginBottom: 16 }}>
                    <Text strong>Upstream配置：</Text>
                    <TextArea
                      value={generateUpstreamConfig()}
                      rows={8}
                      style={{ fontFamily: 'monospace', fontSize: '12px', marginTop: 8 }}
                      readOnly
                    />
                  </div>

                  <div>
                    <Text strong>Location配置：</Text>
                    <TextArea
                      value={generateLocationConfig()}
                      rows={8}
                      style={{ fontFamily: 'monospace', fontSize: '12px', marginTop: 8 }}
                      readOnly
                    />
                  </div>
                </>
              )
            }
          ]}
        />
      </Card>

      {/* 添加/编辑Upstream模态框 */}
      <Modal
        title={editingUpstream?.name ? "编辑Upstream" : "添加Upstream"}
        open={isUpstreamModalVisible}
        onOk={handleSaveUpstream}
        onCancel={() => {
          setIsUpstreamModalVisible(false);
          setEditingUpstream(null);
          upstreamForm.resetFields();
        }}
        width={600}
      >
        <Form form={upstreamForm} layout="vertical" initialValues={editingUpstream || undefined}>
          <Form.Item name="name" label="Upstream名称" rules={[{ required: true, message: '请输入Upstream名称' }]}>
            <Input placeholder="例如: ds1_5b" />
          </Form.Item>
          
          <Form.Item name="servers" label="服务器列表" rules={[{ required: true, message: '请至少添加一个服务器' }]}>
            <Form.List name="servers">
              {(fields, { add, remove }) => (
                <>
                  {fields.map(({ key, name, ...restField }) => (
                    <Space key={key} style={{ display: 'flex', marginBottom: 8 }} align="baseline">
                      <Form.Item
                        {...restField}
                        name={[name, 'address']}
                        rules={[{ required: true, message: '请输入服务器地址' }]}
                      >
                        <Input placeholder="服务器地址" style={{ width: 200 }} />
                      </Form.Item>
                      <Form.Item
                        {...restField}
                        name={[name, 'port']}
                        rules={[{ required: true, message: '请输入端口' }]}
                      >
                        <InputNumber placeholder="端口" style={{ width: 100 }} min={1} max={65535} />
                      </Form.Item>
                      <Form.Item
                        {...restField}
                        name={[name, 'weight']}
                      >
                        <InputNumber placeholder="权重" style={{ width: 80 }} min={1} max={100} />
                      </Form.Item>
                      <Button onClick={() => remove(name)} icon={<DeleteOutlined />} />
                    </Space>
                  ))}
                  <Form.Item>
                    <Button type="dashed" onClick={() => add()} block icon={<PlusOutlined />}>
                      添加服务器
                    </Button>
                  </Form.Item>
                </>
              )}
            </Form.List>
          </Form.Item>
          
          <Form.Item name="keepalive" label="Keepalive连接数">
            <InputNumber min={0} max={1000} style={{ width: '100%' }} placeholder="64" />
          </Form.Item>

          <Divider>健康检查配置</Divider>
          
          <Form.Item name="healthCheckEnabled" label="启用健康检查" valuePropName="checked">
            <Switch />
          </Form.Item>
          
          <Form.Item name="healthCheckPath" label="健康检查路径">
            <Input placeholder="/health" />
          </Form.Item>
          
          <Form.Item name="healthCheckInterval" label="检查间隔(秒)">
            <InputNumber min={5} max={300} style={{ width: '100%' }} placeholder="30" />
          </Form.Item>
        </Form>
      </Modal>

      {/* 添加/编辑Location模态框 */}
      <Modal
        title={editingLocation?.path ? "编辑Location规则" : "添加Location规则"}
        open={isLocationModalVisible}
        onOk={handleSaveLocation}
        onCancel={() => {
          setIsLocationModalVisible(false);
          setEditingLocation(null);
          locationForm.resetFields();
        }}
        width={600}
      >
        <Form form={locationForm} layout="vertical" initialValues={editingLocation || undefined}>
          <Form.Item name="path" label="路径匹配" rules={[{ required: true, message: '请输入路径匹配规则' }]}>
            <Input placeholder="例如: /ds1_5b/v1/chat/completions" />
          </Form.Item>
          
          <Form.Item name="upstream" label="上游服务器" rules={[{ required: true, message: '请选择上游服务器' }]}>
            <Select placeholder="选择上游服务器">
              {Array.isArray(upstreams) ? upstreams.map(upstream => (
                <Option key={upstream.name} value={upstream.name}>{upstream.name}</Option>
              )) : []}
            </Select>
          </Form.Item>
          
          <Form.Item name="proxy_cache" label="代理缓存" valuePropName="checked">
            <Switch checkedChildren="开启" unCheckedChildren="关闭" />
          </Form.Item>
          
          <Form.Item name="proxy_buffering" label="代理缓冲" valuePropName="checked">
            <Switch checkedChildren="开启" unCheckedChildren="关闭" />
          </Form.Item>
          
          <Divider>路径重写配置</Divider>
          
          <Form.Item name={['path_rewrite', 'enabled']} label="启用路径重写" valuePropName="checked">
            <Switch checkedChildren="开启" unCheckedChildren="关闭" />
          </Form.Item>
          
          <Form.Item 
            name={['path_rewrite', 'from']} 
            label="匹配路径模式" 
            rules={[
              ({ getFieldValue }) => ({
                validator(_, value) {
                  const enabled = getFieldValue(['path_rewrite', 'enabled']);
                  if (enabled && !value) {
                    return Promise.reject(new Error('请输入匹配路径模式'));
                  }
                  return Promise.resolve();
                },
              }),
            ]}
          >
            <Input placeholder="例如: /qwen" />
          </Form.Item>
          
          <Form.Item 
            name={['path_rewrite', 'to']} 
            label="重写目标路径" 
            rules={[
              ({ getFieldValue }) => ({
                validator(_, value) {
                  const enabled = getFieldValue(['path_rewrite', 'enabled']);
                  if (enabled && !value) {
                    return Promise.reject(new Error('请输入重写目标路径'));
                  }
                  return Promise.resolve();
                },
              }),
            ]}
          >
            <Input placeholder="例如: /v1/chat/com" />
          </Form.Item>
        </Form>
      </Modal>

    </div>
  );
};

export default ModelRouting;