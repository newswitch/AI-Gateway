import React, { useState, useEffect } from 'react';
import { 
  Card, Row, Col, Button, Typography, Statistic, Tag, Space, Table, 
  Select, Modal, Form, Input, Avatar, Tabs, message, Progress, Divider, InputNumber, Popconfirm
} from 'antd';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title as ChartTitle,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { Doughnut, Line } from 'react-chartjs-2';
import { 
  PlusOutlined, UploadOutlined, EyeOutlined, EditOutlined, DeleteOutlined,
  ReloadOutlined, PoweroffOutlined,
  CheckCircleOutlined, WarningOutlined,
  PlayCircleOutlined, LinkOutlined, AppstoreOutlined,
  DatabaseOutlined, LineChartOutlined,
  PieChartOutlined
} from '@ant-design/icons';

// 注册Chart.js组件
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  ChartTitle,
  Tooltip,
  Legend,
  Filler
);
import { namespaceApi } from '../services/api';

const { Title, Text } = Typography;
const { Option } = Select;
// TabPane已弃用，使用items属性

interface Namespace {
  id: string;
  code: string;
  name: string;
  description?: string;
  owner: {
    name: string;
    avatar: string;
  };
  status: 'enabled' | 'disabled';
  createdAt: string;
  updatedAt: string;
  matcher?: {
    matcher_id: string;
    matcher_name: string;
    matcher_type: 'header' | 'body';
    match_field: string;
    match_operator: string;
    match_value: string;
    priority: number;
    status: number;
  };
}

interface RouteRule {
  id: string;
  name: string;
  routeType: string;
  matchPattern: string;
  priority: number;
  status: 'enabled' | 'disabled';
}

const NamespaceManagement: React.FC = () => {
  const [isAddModalVisible, setIsAddModalVisible] = useState(false);
  const [isViewModalVisible, setIsViewModalVisible] = useState(false);
  const [isEditModalVisible, setIsEditModalVisible] = useState(false);
  const [selectedNamespace, setSelectedNamespace] = useState<Namespace | null>(null);
  const [selectedOwner, setSelectedOwner] = useState('all');
  const [selectedStatus, setSelectedStatus] = useState('all');
  const [searchKeyword, setSearchKeyword] = useState('');
  const [form] = Form.useForm();
  const [editForm] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [namespaces, setNamespaces] = useState<Namespace[]>([]);
  const [pagination, setPagination] = useState({
    total: 0,
    page: 1,
    size: 10,
    pages: 1
  });
  const [statusDistributionData, setStatusDistributionData] = useState<any>(null);
  const [requestTrendData, setRequestTrendData] = useState<any>(null);
  const [chartLoading, setChartLoading] = useState(false);
  const [statusTimeRange, setStatusTimeRange] = useState('all');
  const [trendTimeRange, setTrendTimeRange] = useState('today');
  const [routeRules, setRouteRules] = useState<RouteRule[]>([]);
  const [upstreams, setUpstreams] = useState<any[]>([]);

  // 数据加载函数
  const loadNamespaces = async (page: number = 1, size: number = 10) => {
    try {
      console.log('[NamespaceManagement] 开始加载命名空间数据...', { page, size });
      setLoading(true);
      const response = await namespaceApi.getNamespaces(page, size);
      console.log('[NamespaceManagement] 命名空间API响应:', response);
      
      if (response.code === 200) {
        // API返回格式: {data: {items: [...], total: 3, page: 1, size: 10, pages: 1}}
        const data = response.data?.items || response.data || [];
        console.log('[NamespaceManagement] 解析后的命名空间数据:', data);
        setNamespaces(Array.isArray(data) ? data : []);
        
        // 保存分页信息
        if (response.data) {
          setPagination({
            total: response.data.total || 0,
            page: response.data.page || 1,
            size: response.data.size || 10,
            pages: response.data.pages || 1
          });
        }
        console.log('[NamespaceManagement] 命名空间数据加载成功');
      } else {
        console.error('[NamespaceManagement] API返回错误:', response);
        message.error(`加载命名空间失败: ${response.message || '未知错误'}`);
      }
    } catch (error: any) {
      console.error('[NamespaceManagement] 加载命名空间异常:', error);
      console.error('[NamespaceManagement] 错误详情:', {
        message: error.message,
        stack: error.stack,
        name: error.name
      });
      message.error(`加载命名空间失败: ${error.message || '网络错误'}`);
      // 确保在错误情况下设置空数组
      setNamespaces([]);
    } finally {
      setLoading(false);
    }
  };

  // 加载状态分布数据
  const loadStatusDistribution = async (timeRange: string = 'all') => {
    try {
      setChartLoading(true);
      const response = await namespaceApi.getNamespaceStatusDistribution(timeRange);
      if (response.code === 200) {
        setStatusDistributionData(response.data);
      } else {
        message.error('加载状态分布数据失败');
      }
    } catch (error: any) {
      message.error('加载状态分布数据失败');
      console.error('Load status distribution error:', error);
    } finally {
      setChartLoading(false);
    }
  };

  // 加载请求趋势数据
  const loadRequestTrend = async (timeRange: string = 'today') => {
    try {
      setChartLoading(true);
      const response = await namespaceApi.getNamespaceRequestTrend(timeRange);
      if (response.code === 200) {
        setRequestTrendData(response.data);
      } else {
        message.error('加载请求趋势数据失败');
      }
    } catch (error: any) {
      message.error('加载请求趋势数据失败');
      console.error('Load request trend error:', error);
    } finally {
      setChartLoading(false);
    }
  };

  // 加载路由规则数据
  const loadRouteRules = async () => {
    try {
      // 这里应该调用路由规则API，暂时使用空数组
      setRouteRules([]);
    } catch (error: any) {
      console.error('加载路由规则失败:', error);
      setRouteRules([]);
    }
  };

  // 加载上游服务器数据
  const loadUpstreams = async () => {
    try {
      // 这里应该调用上游服务器API，暂时使用空数组
      setUpstreams([]);
    } catch (error: any) {
      console.error('加载上游服务器失败:', error);
      setUpstreams([]);
    }
  };

  // 处理状态分布时间范围切换
  const handleStatusTimeRangeChange = (timeRange: string) => {
    setStatusTimeRange(timeRange);
    loadStatusDistribution(timeRange);
  };

  // 处理请求趋势时间范围切换
  const handleTrendTimeRangeChange = (timeRange: string) => {
    setTrendTimeRange(timeRange);
    loadRequestTrend(timeRange);
  };

  // 组件挂载时加载数据
  useEffect(() => {
    loadNamespaces();
    loadStatusDistribution();
    loadRequestTrend();
    loadRouteRules();
    loadUpstreams();
  }, []);

  // 计算统计数据
  const totalNamespaces = namespaces.length;
  const enabledNamespaces = namespaces.filter(ns => ns.status === 'enabled').length;
  const enabledRate = totalNamespaces > 0 ? ((enabledNamespaces / totalNamespaces) * 100).toFixed(1) : '0.0';

  // 状态分布图表数据
  const statusChartData = statusDistributionData ? {
    labels: statusDistributionData.labels || ['启用', '禁用'],
    datasets: [
      {
        data: statusDistributionData.data || [enabledNamespaces, totalNamespaces - enabledNamespaces],
        backgroundColor: [
          '#00B42A',
          '#D9D9D9'
        ],
        borderWidth: 0,
        cutout: '60%'
      }
    ]
  } : {
    labels: ['启用', '禁用'],
    datasets: [
      {
        data: [enabledNamespaces, totalNamespaces - enabledNamespaces],
        backgroundColor: [
          '#00B42A',
          '#D9D9D9'
        ],
        borderWidth: 0,
        cutout: '60%'
      }
    ]
  };

  // 请求趋势图表数据 - 优先使用API数据
  const requestTrendChartData = requestTrendData ? {
    labels: requestTrendData.labels || ['00:00', '03:00', '06:00', '09:00', '12:00', '15:00', '18:00', '21:00'],
    datasets: requestTrendData.datasets || []
  } : {
    labels: ['00:00', '03:00', '06:00', '09:00', '12:00', '15:00', '18:00', '21:00'],
    datasets: []
  };
  

  // 图表配置选项
  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom' as const,
        labels: {
          usePointStyle: true,
          padding: 20
        }
      }
    }
  };

  const lineChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
        labels: {
          usePointStyle: true,
          padding: 20
        }
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        max: 4500,
        ticks: {
          stepSize: 500
        },
        grid: {
          color: 'rgba(0, 0, 0, 0.1)'
        }
      },
      x: {
        grid: {
          color: 'rgba(0, 0, 0, 0.1)'
        }
      }
    }
  };

  // 模拟数据（作为备用）- 已注释，使用真实数据
  /* const mockNamespaces: Namespace[] = [
    {
      id: '1',
      code: 'ns-enterprise-001',
      name: '企业版模型服务',
      owner: {
        name: '张三',
        avatar: 'https://picsum.photos/id/1001/200/200'
      },
      defaultUpstream: 'llm-gpt4-prod',
      qps: 100,
      concurrency: 50,
      quota: '10万/天',
      maxSize: '10MB',
      timeout: '30s',
      status: 'enabled',
      createdAt: '2023-06-15',
      updatedAt: '2023-07-02'
    },
    {
      id: '2',
      code: 'ns-dev-002',
      name: '开发测试模型服务',
      owner: {
        name: '李四',
        avatar: 'https://picsum.photos/id/1002/200/200'
      },
      defaultUpstream: 'llm-bloom-dev',
      qps: 50,
      concurrency: 20,
      quota: '5万/天',
      maxSize: '5MB',
      timeout: '60s',
      status: 'enabled',
      createdAt: '2023-06-10',
      updatedAt: '2023-06-28'
    },
    {
      id: '3',
      code: 'ns-test-003',
      name: '测试环境模型服务',
      owner: {
        name: '王五',
        avatar: 'https://picsum.photos/id/1003/200/200'
      },
      defaultUpstream: '未绑定',
      qps: 20,
      concurrency: 10,
      quota: '1万/天',
      maxSize: '2MB',
      timeout: '120s',
      status: 'disabled',
      createdAt: '2023-05-28',
      updatedAt: '2023-05-28'
    },
    {
      id: '4',
      code: 'ns-internal-004',
      name: '内部业务模型服务',
      owner: {
        name: '赵六',
        avatar: 'https://picsum.photos/id/1004/200/200'
      },
      defaultUpstream: 'llm-chatglm-prod',
      qps: 80,
      concurrency: 40,
      quota: '8万/天',
      maxSize: '8MB',
      timeout: '45s',
      status: 'enabled',
      quotaWarning: true,
      createdAt: '2023-06-02',
      updatedAt: '2023-07-01'
    }
  ]; */


  // 表格列定义
  const namespaceColumns = [
    {
      title: (
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <input type="checkbox" style={{ marginRight: 8 }} />
          ID/Code
        </div>
      ),
      dataIndex: 'code',
      key: 'code',
      render: (text: string | undefined) => <Text strong>{text || ''}</Text>
    },
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string | undefined) => <Text>{text || ''}</Text>
    },
    {
      title: '负责人',
      dataIndex: 'owner',
      key: 'owner',
      render: (owner: { name: string; avatar: string } | undefined) => (
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <Avatar src={owner?.avatar} size={24} style={{ marginRight: 8 }} />
          <Text>{owner?.name || ''}</Text>
        </div>
      )
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <div style={{
            width: 8,
            height: 8,
            borderRadius: '50%',
            backgroundColor: status === 'enabled' ? '#00B42A' : '#C9CDD4',
            marginRight: 8
          }} />
          <Text style={{ color: status === 'enabled' ? '#00B42A' : '#8C8C8C' }}>
            {status === 'enabled' ? '启用' : '禁用'}
          </Text>
        </div>
      )
    },
    {
      title: '消息匹配器',
      key: 'matcher',
      render: (_: any, record: Namespace) => {
        const matcher = record.matcher;
        if (!matcher) {
          return <Text type="secondary">未配置</Text>;
        }
        return (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <Tag color="blue" style={{ fontSize: '11px' }}>
              {matcher.matcher_type === 'header' ? '请求头' : '请求体'}
            </Tag>
            <Text style={{ fontSize: '12px' }}>
              {matcher.match_field} {matcher.match_operator} "{matcher.match_value}"
            </Text>
          </div>
        );
      }
    },
    {
      title: '创建/更新时间',
      key: 'dates',
      render: (_: any, record: Namespace) => (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          <Text style={{ fontSize: '12px' }}>{record.createdAt}</Text>
          <Text style={{ fontSize: '12px' }}>{record.updatedAt}</Text>
        </div>
      )
    },
    {
      title: '操作',
      key: 'actions',
      width: 120,
      render: (_: any, record: Namespace) => (
        <Space size="small">
          <Button 
            type="link" 
            size="small" 
            icon={<EditOutlined />}
            onClick={() => handleEditNamespace(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定要删除这个命名空间吗？"
            description="删除后无法恢复，同时会删除相关的匹配器和策略。"
            onConfirm={() => handleDeleteNamespace(record.id)}
            okText="确定"
            cancelText="取消"
          >
          <Button 
            type="link" 
            size="small" 
              danger
              icon={<DeleteOutlined />}
          >
            删除
          </Button>
          </Popconfirm>
        </Space>
      )
    },
  ];

  const routeColumns = [
    {
      title: '规则名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string | undefined) => <Text strong>{text || ''}</Text>
    },
    {
      title: '路由类型',
      dataIndex: 'routeType',
      key: 'routeType',
      render: (type: string) => {
        const typeMap: { [key: string]: { color: string; text: string } } = {
          prefix: { color: 'blue', text: '前缀匹配' },
          exact: { color: 'green', text: '精确匹配' },
          regex: { color: 'orange', text: '正则匹配' },
          weighted: { color: 'purple', text: '权重路由' }
        };
        const config = typeMap[type];
        return <Tag color={config.color}>{config.text}</Tag>;
      }
    },
    {
      title: '匹配模式',
      dataIndex: 'matchPattern',
      key: 'matchPattern',
      render: (text: string | undefined) => <Text code>{text || ''}</Text>
    },
    {
      title: '优先级',
      dataIndex: 'priority',
      key: 'priority',
      render: (priority: number) => {
        const color = priority === 1 ? 'red' : priority <= 3 ? 'orange' : 'default';
        const text = priority === 1 ? `${priority} (最高)` : priority.toString();
        return <Tag color={color}>{text}</Tag>;
      }
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <div style={{
            width: 8,
            height: 8,
            borderRadius: '50%',
            backgroundColor: status === 'enabled' ? '#00B42A' : '#C9CDD4',
            marginRight: 8
          }} />
          <Text style={{ color: status === 'enabled' ? '#00B42A' : '#8C8C8C' }}>
            {status === 'enabled' ? '启用' : '禁用'}
          </Text>
        </div>
      )
    },
    {
      title: '操作',
      key: 'actions',
      render: (_: any) => (
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 12 }}>
          <Button type="link" size="small" style={{ padding: 0 }}>
            查看
          </Button>
          <Button type="link" size="small" style={{ padding: 0, color: '#F53F3F' }}>
            解绑
          </Button>
        </div>
      )
    }
  ];

  const handleAddNamespace = () => {
    setIsAddModalVisible(true);
  };

  const handleModalOk = async () => {
    try {
      const values = await form.validateFields();
      
      // 调用API创建命名空间
      const response = await namespaceApi.createNamespace({
        code: values.code,
        name: values.name,
        description: values.description || '',
        owner: values.owner || 'admin',
        status: 'enabled',
        // 传递匹配器配置
        matcherType: values.matcherType,
        matchField: values.matchField,
        matchOperator: values.matchOperator,
        matchValue: values.matchValue,
        priority: values.priority
      });
      
      if (response.code === 200) {
        message.success('命名空间和消息匹配器创建成功');
      setIsAddModalVisible(false);
      form.resetFields();
        // 重新加载数据
        loadNamespaces();
      } else {
        message.error(response.message || '创建失败');
      }
    } catch (error) {
      message.error('创建命名空间失败');
      console.error('Create namespace error:', error);
    }
  };

  const handleModalCancel = () => {
    setIsAddModalVisible(false);
    form.resetFields();
  };

  // 删除命名空间
  const handleEditNamespace = (namespace: Namespace) => {
    console.log('编辑命名空间:', namespace);
    setSelectedNamespace(namespace);
    setIsEditModalVisible(true);
    
    // 设置表单初始值
    form.setFieldsValue({
      code: namespace.code,
      name: namespace.name,
      description: namespace.description,
      status: namespace.status,
      matcherType: namespace.matcher?.matcher_type || 'header',
      matchField: namespace.matcher?.match_field || 'channelcode',
      matchOperator: namespace.matcher?.match_operator || 'equals',
      matchValue: namespace.matcher?.match_value || namespace.code,
      priority: namespace.matcher?.priority || 100
    });
  };

  const handleUpdateNamespace = async () => {
    try {
      const values = await form.validateFields();
      
      if (!selectedNamespace) return;
      
      // 调用API更新命名空间
      const response = await namespaceApi.updateNamespace(selectedNamespace.id, {
        code: values.code,
        name: values.name,
        description: values.description || '',
        status: 'enabled',
        // 传递匹配器配置
        matcherType: values.matcherType,
        matchField: values.matchField,
        matchOperator: values.matchOperator,
        matchValue: values.matchValue,
        priority: values.priority
      });
      
      if (response.code === 200) {
        message.success('命名空间更新成功');
        setIsEditModalVisible(false);
        setSelectedNamespace(null);
        form.resetFields();
        // 重新加载数据
        loadNamespaces();
      } else {
        message.error(response.message || '更新失败');
      }
    } catch (error) {
      message.error('更新命名空间失败');
      console.error('Update namespace error:', error);
    }
  };

  const handleDeleteNamespace = async (id: string) => {
    try {
      const response = await namespaceApi.deleteNamespace(id);
      if (response.code === 200) {
        message.success('命名空间删除成功');
        loadNamespaces(); // 重新加载数据
      } else {
        message.error(response.message || '删除失败');
      }
    } catch (error) {
      message.error('删除命名空间失败');
      console.error('Delete namespace error:', error);
    }
  };

  // 更新命名空间状态
  const handleToggleStatus = async (id: string, currentStatus: string) => {
    try {
      const newStatus = currentStatus === 'enabled' ? 'disabled' : 'enabled';
      const response = await namespaceApi.updateNamespace(id, { status: newStatus });
      if (response.code === 200) {
        message.success(`命名空间已${newStatus === 'enabled' ? '启用' : '禁用'}`);
        loadNamespaces(); // 重新加载数据
      } else {
        message.error(response.message || '状态更新失败');
      }
    } catch (error) {
      message.error('更新命名空间状态失败');
      console.error('Update namespace status error:', error);
    }
  };

  // 查看命名空间详情
  const handleViewNamespace = (namespace: Namespace) => {
    setSelectedNamespace(namespace);
    setIsViewModalVisible(true);
  };


  // 保存编辑
  const handleEditSave = async () => {
    try {
      const values = await editForm.validateFields();
      if (!selectedNamespace) return;

      const response = await namespaceApi.updateNamespace(selectedNamespace.id, {
        code: values.code,
        name: values.name,
        description: values.description || '',
        status: values.status
      });

      if (response.code === 200) {
        message.success('命名空间更新成功');
        setIsEditModalVisible(false);
        setSelectedNamespace(null);
        editForm.resetFields();
        loadNamespaces(); // 重新加载数据
      } else {
        message.error(response.message || '更新失败');
      }
    } catch (error) {
      message.error('更新命名空间失败');
      console.error('Update namespace error:', error);
    }
  };

  // 关闭查看模态框
  const handleViewModalCancel = () => {
    setIsViewModalVisible(false);
    setSelectedNamespace(null);
  };

  // 关闭编辑模态框
  const handleEditModalCancel = () => {
    setIsEditModalVisible(false);
    setSelectedNamespace(null);
    editForm.resetFields();
  };

  return (
    <div style={{ padding: '24px', backgroundColor: '#f5f5f5', minHeight: '100vh' }}>
      {/* 页面标题 */}
      <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <Title level={2} style={{ margin: 0, color: '#1d2129' }}>命名空间管理</Title>
          <Text style={{ color: '#86909c', fontSize: '14px' }}>管理和配置模型服务的命名空间</Text>
        </div>
        <Space>
          <Button type="primary" icon={<PlusOutlined />} onClick={handleAddNamespace}>
            创建命名空间
          </Button>
          <Button icon={<UploadOutlined />}>
            导入命名空间
          </Button>
        </Space>
      </div>

      {/* 概览卡片 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={8}>
          <Card style={{ borderRadius: 12, boxShadow: '0 4px 20px rgba(0, 0, 0, 0.08)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <Text style={{ color: '#86909c', fontSize: '14px' }}>命名空间总数</Text>
                <div style={{ marginTop: 8 }}>
                  <Statistic value={totalNamespaces} valueStyle={{ fontSize: '24px', fontWeight: 'bold', color: '#1d2129' }} />
                </div>
                <div style={{ marginTop: 12, display: 'flex', alignItems: 'center' }}>
                  <Tag color="blue" icon={<DatabaseOutlined />}>
                    当前活跃
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
                <DatabaseOutlined style={{ fontSize: 20 }} />
              </div>
            </div>
          </Card>
        </Col>

        <Col xs={24} sm={12} lg={8}>
          <Card style={{ borderRadius: 12, boxShadow: '0 4px 20px rgba(0, 0, 0, 0.08)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <Text style={{ color: '#86909c', fontSize: '14px' }}>启用中</Text>
                <div style={{ marginTop: 8 }}>
                  <Statistic value={enabledNamespaces} valueStyle={{ fontSize: '24px', fontWeight: 'bold', color: '#1d2129' }} />
                </div>
                <div style={{ marginTop: 12, display: 'flex', alignItems: 'center' }}>
                  <Tag color="green" icon={<CheckCircleOutlined />}>
                    {enabledRate}% 启用率
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
                <PlayCircleOutlined style={{ fontSize: 20 }} />
              </div>
            </div>
          </Card>
        </Col>


        <Col xs={24} sm={12} lg={8}>
          <Card style={{ borderRadius: 12, boxShadow: '0 4px 20px rgba(0, 0, 0, 0.08)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <Text style={{ color: '#86909c', fontSize: '14px' }}>禁用中</Text>
                <div style={{ marginTop: 8 }}>
                  <Statistic value={totalNamespaces - enabledNamespaces} valueStyle={{ fontSize: '24px', fontWeight: 'bold', color: '#1d2129' }} />
                </div>
                <div style={{ marginTop: 12, display: 'flex', alignItems: 'center' }}>
                  <Tag color="red" icon={<PoweroffOutlined />}>
                    {totalNamespaces - enabledNamespaces > 0 ? '需要处理' : '全部启用'}
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
                <PoweroffOutlined style={{ fontSize: 20 }} />
              </div>
            </div>
          </Card>
        </Col>
      </Row>

      {/* 图表区域占位 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} lg={12}>
          <Card style={{ borderRadius: 12, boxShadow: '0 4px 20px rgba(0, 0, 0, 0.08)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <div style={{ display: 'flex', alignItems: 'center' }}>
                <PieChartOutlined style={{ fontSize: 20, color: '#165DFF', marginRight: 8 }} />
              <Title level={4} style={{ margin: 0, color: '#1d2129' }}>命名空间状态分布</Title>
              </div>
              <Space>
                <Button 
                  size="small" 
                  type={statusTimeRange === 'all' ? 'primary' : 'default'}
                  onClick={() => handleStatusTimeRangeChange('all')}
                >
                  全部
                </Button>
                <Button 
                  size="small" 
                  type={statusTimeRange === 'week' ? 'primary' : 'default'}
                  onClick={() => handleStatusTimeRangeChange('week')}
                >
                  本周
                </Button>
                <Button 
                  size="small" 
                  type={statusTimeRange === 'month' ? 'primary' : 'default'}
                  onClick={() => handleStatusTimeRangeChange('month')}
                >
                  本月
                </Button>
              </Space>
            </div>
            <div style={{ height: 288, padding: '20px 0' }}>
              {chartLoading ? (
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
                  <Text style={{ color: '#86909c' }}>加载中...</Text>
                </div>
              ) : (
                <Doughnut data={statusChartData} options={chartOptions} />
              )}
            </div>
          </Card>
        </Col>

        <Col xs={24} lg={12}>
          <Card style={{ borderRadius: 12, boxShadow: '0 4px 20px rgba(0, 0, 0, 0.08)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <div style={{ display: 'flex', alignItems: 'center' }}>
                <LineChartOutlined style={{ fontSize: 20, color: '#165DFF', marginRight: 8 }} />
              <Title level={4} style={{ margin: 0, color: '#1d2129' }}>命名空间请求趋势</Title>
              </div>
              <Space>
                <Button 
                  size="small" 
                  type={trendTimeRange === 'today' ? 'primary' : 'default'}
                  onClick={() => handleTrendTimeRangeChange('today')}
                >
                  今日
                </Button>
                <Button 
                  size="small" 
                  type={trendTimeRange === 'week' ? 'primary' : 'default'}
                  onClick={() => handleTrendTimeRangeChange('week')}
                >
                  本周
                </Button>
                <Button 
                  size="small" 
                  type={trendTimeRange === 'month' ? 'primary' : 'default'}
                  onClick={() => handleTrendTimeRangeChange('month')}
                >
                  本月
                </Button>
              </Space>
            </div>
            <div style={{ height: 288, padding: '20px 0' }}>
              {chartLoading ? (
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
                  <Text style={{ color: '#86909c' }}>加载中...</Text>
                </div>
              ) : (
                <Line 
                  key={`trend-chart-${trendTimeRange}-${requestTrendData ? JSON.stringify(requestTrendData).length : 0}`}
                  data={requestTrendChartData} 
                  options={lineChartOptions} 
                />
              )}
            </div>
          </Card>
        </Col>
      </Row>

      {/* 命名空间列表 */}
      <Card style={{ borderRadius: 12, boxShadow: '0 4px 20px rgba(0, 0, 0, 0.08)', marginBottom: 24 }}>
        <div style={{ padding: '20px', borderBottom: '1px solid #e5e6eb', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <AppstoreOutlined style={{ fontSize: 20, color: '#165DFF', marginRight: 8 }} />
          <Title level={4} style={{ margin: 0, color: '#1d2129' }}>命名空间列表</Title>
          </div>
          <Space>
            <Input
              placeholder="关键字搜索..."
              prefix={<EyeOutlined style={{ color: '#C9CDD4' }} />}
              style={{ width: 200 }}
              value={searchKeyword}
              onChange={(e) => setSearchKeyword(e.target.value)}
            />
            <Select
              value={selectedOwner}
              onChange={setSelectedOwner}
              style={{ width: 120 }}
              placeholder="负责人筛选"
            >
              <Option value="all">全部负责人</Option>
              <Option value="张三">张三</Option>
              <Option value="李四">李四</Option>
              <Option value="王五">王五</Option>
              <Option value="赵六">赵六</Option>
            </Select>
            <Select
              value={selectedStatus}
              onChange={setSelectedStatus}
              style={{ width: 100 }}
              placeholder="状态筛选"
            >
              <Option value="all">全部状态</Option>
              <Option value="enabled">启用</Option>
              <Option value="disabled">禁用</Option>
            </Select>
            <Button icon={<ReloadOutlined />} />
          </Space>
        </div>
        
        <Table
          columns={namespaceColumns}
          dataSource={Array.isArray(namespaces) ? namespaces : []}
          loading={loading}
          rowKey="id"
          pagination={{
            current: pagination.page,
            pageSize: pagination.size,
            total: pagination.total,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `显示 ${range[0]} 到 ${range[1]} 条，共 ${total} 条记录`,
            onChange: (page, size) => {
              loadNamespaces(page, size);
            },
            onShowSizeChange: (_, size) => {
              loadNamespaces(1, size);
            }
          }}
          style={{ borderRadius: 0 }}
        />
      </Card>

      {/* 命名空间详情 */}
      <Card style={{ borderRadius: 12, boxShadow: '0 4px 20px rgba(0, 0, 0, 0.08)' }}>
        <div style={{ padding: '20px', borderBottom: '1px solid #e5e6eb' }}>
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <DatabaseOutlined style={{ fontSize: 20, color: '#165DFF', marginRight: 8 }} />
          <Title level={4} style={{ margin: 0, color: '#1d2129' }}>
              命名空间详情 <Text style={{ fontSize: '14px', color: '#8C8C8C', fontWeight: 'normal', marginLeft: 8 }}>
                {namespaces.length > 0 ? namespaces[0].code : '暂无数据'}
              </Text>
          </Title>
          </div>
        </div>
        
        <Tabs 
          defaultActiveKey="1" 
          style={{ padding: '0 20px' }}
          items={[
            {
              key: "1",
              label: (
                <span>
                  <LinkOutlined style={{ marginRight: 6 }} />
                  路由规则
                </span>
              ),
              children: (
            <div style={{ padding: '20px 0' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                <Title level={5} style={{ margin: 0 }}>已绑定规则清单</Title>
                <Space>
                  <Button type="link" icon={<PlusOutlined />}>
                    绑定规则
                  </Button>
                  <Button type="link" icon={<ReloadOutlined />}>
                    排序规则
                  </Button>
                  <Button type="link" icon={<AppstoreOutlined />}>
                    冲突检测
                  </Button>
                </Space>
              </div>
              
              <Table
                columns={routeColumns}
                dataSource={Array.isArray(routeRules) ? routeRules : []}
                rowKey="id"
                pagination={false}
                size="small"
              />
            </div>
              )
            },
            {
              key: "2",
              label: (
                <span>
                  <DatabaseOutlined style={{ marginRight: 6 }} />
                  上游绑定
                </span>
              ),
              children: (
            <div style={{ padding: '20px 0' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                <Title level={5} style={{ margin: 0 }}>上游服务器绑定</Title>
                <Space>
                  <Button type="primary" icon={<PlusOutlined />} size="small">
                    绑定上游
                  </Button>
                  <Button icon={<ReloadOutlined />} size="small">
                    刷新
                  </Button>
                </Space>
            </div>
              
              <Table
                columns={[
                  {
                    title: '上游名称',
                    dataIndex: 'name',
                    key: 'name',
                    render: (text: string | undefined) => <Text strong>{text || ''}</Text>
                  },
                  {
                    title: '服务器地址',
                    dataIndex: 'servers',
                    key: 'servers',
                    render: (servers: any[]) => (
                      <div>
                        {servers.map((server, index) => (
                          <Text key={index} style={{ display: 'block', fontSize: '12px' }}>
                            {server.address}:{server.port} (权重: {server.weight})
                          </Text>
                        ))}
                      </div>
                    )
                  },
                  {
                    title: '健康检查',
                    dataIndex: 'healthCheck',
                    key: 'healthCheck',
                    render: (enabled: boolean) => (
                      <Tag color={enabled ? 'green' : 'red'}>
                        {enabled ? '启用' : '禁用'}
                      </Tag>
                    )
                  },
                  {
                    title: '操作',
                    key: 'actions',
                    render: (_: any) => (
                      <Space size="small">
                        <Button type="link" size="small">编辑</Button>
                        <Button type="link" size="small" danger>解绑</Button>
                      </Space>
                    )
                  }
                ]}
                dataSource={Array.isArray(upstreams) ? upstreams : []}
                rowKey="name"
                pagination={false}
                size="small"
              />
            </div>
              )
            },
            {
              key: "3",
              label: (
                <span>
                  <CheckCircleOutlined style={{ marginRight: 6 }} />
                  鉴权策略
                </span>
              ),
              children: (
            <div style={{ padding: '20px 0' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                <Title level={5} style={{ margin: 0 }}>鉴权策略配置</Title>
                <Space>
                  <Button type="primary" icon={<PlusOutlined />} size="small">
                    添加策略
                  </Button>
                  <Button icon={<ReloadOutlined />} size="small">
                    刷新
                  </Button>
                </Space>
            </div>
              
              <Table
                columns={[
                  {
                    title: '策略名称',
                    dataIndex: 'name',
                    key: 'name',
                    render: (text: string | undefined) => <Text strong>{text || ''}</Text>
                  },
                  {
                    title: '策略类型',
                    dataIndex: 'type',
                    key: 'type',
                    render: (type: string) => (
                      <Tag color={type === 'API Key' ? 'blue' : type === 'JWT' ? 'green' : 'orange'}>
                        {type}
                      </Tag>
                    )
                  },
                  {
                    title: '状态',
                    dataIndex: 'status',
                    key: 'status',
                    render: (status: string) => (
                      <Tag color={status === 'enabled' ? 'green' : 'red'}>
                        {status === 'enabled' ? '启用' : '禁用'}
                      </Tag>
                    )
                  },
                  {
                    title: '创建时间',
                    dataIndex: 'createdAt',
                    key: 'createdAt',
                    render: (time: string) => <Text style={{ fontSize: '12px' }}>{time}</Text>
                  },
                  {
                    title: '操作',
                    key: 'actions',
                    render: (_: any) => (
                      <Space size="small">
                        <Button type="link" size="small">编辑</Button>
                        <Button type="link" size="small" danger>删除</Button>
                      </Space>
                    )
                  }
                ]}
                dataSource={[]}
                rowKey="id"
                pagination={false}
                size="small"
              />
            </div>
              )
            },
            {
              key: "4",
              label: (
                <span>
                  <WarningOutlined style={{ marginRight: 6 }} />
                  限流/配额
                </span>
              ),
              children: (
            <div style={{ padding: '20px 0' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                <Title level={5} style={{ margin: 0 }}>限流配额配置</Title>
                <Space>
                  <Button type="primary" icon={<PlusOutlined />} size="small">
                    添加规则
                  </Button>
                  <Button icon={<ReloadOutlined />} size="small">
                    刷新
                  </Button>
                </Space>
            </div>
              
              <Row gutter={16} style={{ marginBottom: 16 }}>
                <Col span={8}>
                  <Card size="small">
                    <Statistic
                      title="QPS限制"
                      value={100}
                      suffix="req/s"
                      valueStyle={{ color: '#1890ff' }}
                    />
                  </Card>
                </Col>
                <Col span={8}>
                  <Card size="small">
                    <Statistic
                      title="并发限制"
                      value={50}
                      suffix="连接"
                      valueStyle={{ color: '#52c41a' }}
                    />
                  </Card>
                </Col>
                <Col span={8}>
                  <Card size="small">
                    <Statistic
                      title="Token配额"
                      value="10万"
                      suffix="/天"
                      valueStyle={{ color: '#fa8c16' }}
                    />
                  </Card>
                </Col>
              </Row>
              
              <Table
                columns={[
                  {
                    title: '规则名称',
                    dataIndex: 'name',
                    key: 'name',
                    render: (text: string | undefined) => <Text strong>{text || ''}</Text>
                  },
                  {
                    title: '限制类型',
                    dataIndex: 'type',
                    key: 'type',
                    render: (type: string) => (
                      <Tag color={type === 'QPS' ? 'blue' : type === '并发' ? 'green' : 'orange'}>
                        {type}
                      </Tag>
                    )
                  },
                  {
                    title: '限制值',
                    dataIndex: 'limit',
                    key: 'limit',
                    render: (limit: string) => <Text code>{limit}</Text>
                  },
                  {
                    title: '状态',
                    dataIndex: 'status',
                    key: 'status',
                    render: (status: string) => (
                      <Tag color={status === 'enabled' ? 'green' : 'red'}>
                        {status === 'enabled' ? '启用' : '禁用'}
                      </Tag>
                    )
                  },
                  {
                    title: '操作',
                    key: 'actions',
                    render: (_: any) => (
                      <Space size="small">
                        <Button type="link" size="small">编辑</Button>
                        <Button type="link" size="small" danger>删除</Button>
                      </Space>
                    )
                  }
                ]}
                dataSource={[]}
                rowKey="id"
                pagination={false}
                size="small"
              />
            </div>
              )
            },
            {
              key: "5",
              label: "灰度发布",
              children: (
            <div style={{ padding: '20px 0' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                <Title level={5} style={{ margin: 0 }}>灰度发布配置</Title>
                <Space>
                  <Button type="primary" icon={<PlusOutlined />} size="small">
                    创建发布
                  </Button>
                  <Button icon={<ReloadOutlined />} size="small">
                    刷新
                  </Button>
                </Space>
            </div>
              
              <Table
                columns={[
                  {
                    title: '发布名称',
                    dataIndex: 'name',
                    key: 'name',
                    render: (text: string | undefined) => <Text strong>{text || ''}</Text>
                  },
                  {
                    title: '灰度比例',
                    dataIndex: 'ratio',
                    key: 'ratio',
                    render: (ratio: number) => (
                      <Progress percent={ratio} size="small" style={{ width: 100 }} />
                    )
                  },
                  {
                    title: '目标版本',
                    dataIndex: 'targetVersion',
                    key: 'targetVersion',
                    render: (version: string) => <Text code>{version}</Text>
                  },
                  {
                    title: '状态',
                    dataIndex: 'status',
                    key: 'status',
                    render: (status: string) => (
                      <Tag color={status === 'running' ? 'green' : status === 'paused' ? 'orange' : 'red'}>
                        {status === 'running' ? '运行中' : status === 'paused' ? '暂停' : '已停止'}
                      </Tag>
                    )
                  },
                  {
                    title: '操作',
                    key: 'actions',
                    render: (_: any) => (
                      <Space size="small">
                        <Button type="link" size="small">编辑</Button>
                        <Button type="link" size="small">暂停</Button>
                        <Button type="link" size="small" danger>停止</Button>
                      </Space>
                    )
                  }
                ]}
                dataSource={[]}
                rowKey="id"
                pagination={false}
                size="small"
              />
            </div>
              )
            },
            {
              key: "6",
              label: "访问密钥",
              children: (
            <div style={{ padding: '20px 0' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                <Title level={5} style={{ margin: 0 }}>访问密钥管理</Title>
                <Space>
                  <Button type="primary" icon={<PlusOutlined />} size="small">
                    生成密钥
                  </Button>
                  <Button icon={<ReloadOutlined />} size="small">
                    刷新
                  </Button>
                </Space>
            </div>
              
              <Table
                columns={[
                  {
                    title: '密钥名称',
                    dataIndex: 'name',
                    key: 'name',
                    render: (text: string | undefined) => <Text strong>{text || ''}</Text>
                  },
                  {
                    title: '密钥类型',
                    dataIndex: 'type',
                    key: 'type',
                    render: (type: string) => (
                      <Tag color={type === 'API Key' ? 'blue' : 'green'}>
                        {type}
                      </Tag>
                    )
                  },
                  {
                    title: '密钥值',
                    dataIndex: 'key',
                    key: 'key',
                    render: (key: string) => (
                      <Text code style={{ fontSize: '11px' }}>
                        {key.substring(0, 8)}...{key.substring(key.length - 8)}
                      </Text>
                    )
                  },
                  {
                    title: '权限',
                    dataIndex: 'permissions',
                    key: 'permissions',
                    render: (permissions: string[]) => (
                      <div>
                        {permissions.map(perm => (
                          <Tag key={perm} style={{ margin: '1px', fontSize: '11px' }}>
                            {perm}
                          </Tag>
                        ))}
                      </div>
                    )
                  },
                  {
                    title: '状态',
                    dataIndex: 'status',
                    key: 'status',
                    render: (status: string) => (
                      <Tag color={status === 'active' ? 'green' : 'red'}>
                        {status === 'active' ? '激活' : '禁用'}
                      </Tag>
                    )
                  },
                  {
                    title: '操作',
                    key: 'actions',
                    render: (_: any) => (
                      <Space size="small">
                        <Button type="link" size="small">复制</Button>
                        <Button type="link" size="small">编辑</Button>
                        <Button type="link" size="small" danger>删除</Button>
                      </Space>
                    )
                  }
                ]}
                dataSource={[]}
                rowKey="id"
                pagination={false}
                size="small"
              />
            </div>
              )
            }
          ]}
        />
      </Card>

      {/* 添加命名空间模态框 */}
      <Modal
        title="创建命名空间"
        open={isAddModalVisible}
        onOk={handleModalOk}
        onCancel={handleModalCancel}
        width={600}
      >
        <Form form={form} layout="vertical">
          <Form.Item label="命名空间代码" name="code" rules={[{ required: true, message: '请输入命名空间代码' }]}>
            <Input placeholder="例如: wechat" />
          </Form.Item>
          <Form.Item label="命名空间名称" name="name" rules={[{ required: true, message: '请输入命名空间名称' }]}>
            <Input placeholder="例如: 微信服务" />
          </Form.Item>
          <Form.Item label="描述" name="description">
            <Input.TextArea rows={3} placeholder="请输入命名空间描述" />
          </Form.Item>
          
          <Divider orientation="left" style={{ margin: '20px 0 16px 0' }}>消息匹配器配置</Divider>
          
          <Form.Item 
            label="匹配类型" 
            name="matcherType" 
            rules={[{ required: true, message: '请选择匹配类型' }]}
            initialValue="header"
          >
            <Select placeholder="选择匹配类型">
              <Option value="header">请求头匹配</Option>
              <Option value="body">请求体匹配</Option>
            </Select>
          </Form.Item>
          
          <Form.Item 
            label="匹配字段" 
            name="matchField" 
            rules={[{ required: true, message: '请输入匹配字段' }]}
            initialValue="channelcode"
          >
            <Input placeholder="例如: channelcode, user-agent, x-channel" />
          </Form.Item>
          
          <Form.Item 
            label="匹配操作符" 
            name="matchOperator" 
            rules={[{ required: true, message: '请选择匹配操作符' }]}
            initialValue="equals"
          >
            <Select placeholder="选择匹配操作符">
              <Option value="equals">等于</Option>
              <Option value="contains">包含</Option>
              <Option value="regex">正则匹配</Option>
              <Option value="in">包含在列表中</Option>
            </Select>
          </Form.Item>
          
          <Form.Item 
            label="匹配值" 
            name="matchValue" 
            rules={[{ required: true, message: '请输入匹配值' }]}
          >
            <Input placeholder="例如: wechat, alipay, web" />
          </Form.Item>
          
          <Form.Item 
            label="优先级" 
            name="priority" 
            rules={[{ required: true, message: '请设置优先级' }]}
            initialValue={100}
          >
            <InputNumber 
              min={1} 
              max={1000} 
              placeholder="1-1000，数字越大优先级越高" 
              style={{ width: '100%' }}
            />
          </Form.Item>
        </Form>
      </Modal>

      {/* 编辑命名空间模态框 */}
      <Modal
        title="编辑命名空间"
        open={isEditModalVisible}
        onOk={handleUpdateNamespace}
        onCancel={() => {
          setIsEditModalVisible(false);
          setSelectedNamespace(null);
          form.resetFields();
        }}
        width={600}
      >
        <Form form={form} layout="vertical">
          <Form.Item label="命名空间代码" name="code" rules={[{ required: true, message: '请输入命名空间代码' }]}>
            <Input placeholder="例如: wechat" />
          </Form.Item>
          <Form.Item label="命名空间名称" name="name" rules={[{ required: true, message: '请输入命名空间名称' }]}>
            <Input placeholder="例如: 微信服务" />
          </Form.Item>
          <Form.Item label="描述" name="description">
            <Input.TextArea rows={3} placeholder="请输入命名空间描述" />
          </Form.Item>
          
          <Form.Item 
            label="状态" 
            name="status" 
            rules={[{ required: true, message: '请选择状态' }]}
          >
            <Select>
              <Option value="enabled">启用</Option>
              <Option value="disabled">禁用</Option>
            </Select>
          </Form.Item>
          
          <Divider orientation="left" style={{ margin: '20px 0 16px 0' }}>消息匹配器配置</Divider>
          
          <Form.Item 
            label="匹配类型" 
            name="matcherType" 
            rules={[{ required: true, message: '请选择匹配类型' }]}
          >
            <Select placeholder="选择匹配类型">
              <Option value="header">请求头匹配</Option>
              <Option value="body">请求体匹配</Option>
            </Select>
          </Form.Item>
          
          <Form.Item 
            label="匹配字段" 
            name="matchField" 
            rules={[{ required: true, message: '请输入匹配字段' }]}
          >
            <Input placeholder="例如: channelcode, user-agent, x-channel" />
          </Form.Item>
          
          <Form.Item 
            label="匹配操作符" 
            name="matchOperator" 
            rules={[{ required: true, message: '请选择匹配操作符' }]}
          >
            <Select placeholder="选择匹配操作符">
              <Option value="equals">等于</Option>
              <Option value="contains">包含</Option>
              <Option value="regex">正则匹配</Option>
              <Option value="in">包含在列表中</Option>
            </Select>
          </Form.Item>
          
          <Form.Item 
            label="匹配值" 
            name="matchValue" 
            rules={[{ required: true, message: '请输入匹配值' }]}
          >
            <Input placeholder="例如: wechat, alipay, web" />
          </Form.Item>
          
          <Form.Item 
            label="优先级" 
            name="priority" 
            rules={[{ required: true, message: '请设置优先级' }]}
          >
            <InputNumber 
              min={1} 
              max={1000} 
              placeholder="1-1000，数字越大优先级越高" 
              style={{ width: '100%' }}
            />
          </Form.Item>
        </Form>
      </Modal>

      {/* 查看命名空间详情模态框 */}
      <Modal
        title="命名空间详情"
        open={isViewModalVisible}
        onCancel={handleViewModalCancel}
        footer={[
          <Button key="close" onClick={handleViewModalCancel}>
            关闭
          </Button>
        ]}
        width={800}
      >
        {selectedNamespace && (
          <div style={{ padding: '20px 0' }}>
            <Row gutter={[16, 16]}>
              <Col span={12}>
                <Card size="small" title="基本信息">
                  <div style={{ marginBottom: 12 }}>
                    <Text strong>命名空间代码：</Text>
                    <Text code style={{ marginLeft: 8 }}>{selectedNamespace.code}</Text>
                  </div>
                  <div style={{ marginBottom: 12 }}>
                    <Text strong>命名空间名称：</Text>
                    <Text style={{ marginLeft: 8 }}>{selectedNamespace.name}</Text>
                  </div>
                  <div style={{ marginBottom: 12 }}>
                    <Text strong>状态：</Text>
                    <Tag color={selectedNamespace.status === 'enabled' ? 'green' : 'red'} style={{ marginLeft: 8 }}>
                      {selectedNamespace.status === 'enabled' ? '启用' : '禁用'}
                    </Tag>
                  </div>
                  <div style={{ marginBottom: 12 }}>
                    <Text strong>负责人：</Text>
                    <div style={{ display: 'flex', alignItems: 'center', marginLeft: 8, marginTop: 4 }}>
                      <Avatar src={selectedNamespace.owner.avatar} size={20} style={{ marginRight: 8 }} />
                      <Text>{selectedNamespace.owner.name}</Text>
                    </div>
                  </div>
                </Card>
              </Col>
              <Col span={12}>
                <Card size="small" title="基本信息">
                  <div style={{ marginBottom: 12 }}>
                    <Text strong>描述：</Text>
                    <Text style={{ marginLeft: 8, color: selectedNamespace.description ? 'inherit' : '#8C8C8C' }}>
                      {selectedNamespace.description || '暂无描述'}
                    </Text>
                  </div>
                </Card>
              </Col>
            </Row>
            

            <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
              <Col span={12}>
                <Card size="small" title="时间信息">
                  <div style={{ marginBottom: 12 }}>
                    <Text strong>创建时间：</Text>
                    <Text style={{ marginLeft: 8 }}>{selectedNamespace.createdAt}</Text>
                  </div>
                  <div style={{ marginBottom: 12 }}>
                    <Text strong>更新时间：</Text>
                    <Text style={{ marginLeft: 8 }}>{selectedNamespace.updatedAt}</Text>
                  </div>
                </Card>
              </Col>
              <Col span={12}>
                <Card size="small" title="状态信息">
                  <div style={{ marginBottom: 12 }}>
                    <Text strong>当前状态：</Text>
                    <Tag color={selectedNamespace.status === 'enabled' ? 'green' : 'red'} style={{ marginLeft: 8 }}>
                      {selectedNamespace.status === 'enabled' ? '启用' : '禁用'}
                    </Tag>
                  </div>
                </Card>
              </Col>
            </Row>
          </div>
        )}
      </Modal>

    </div>
  );
};

export default NamespaceManagement;
