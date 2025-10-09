import React, { useState, useEffect } from 'react';
import {
  Card, Row, Col, Button, Typography, Statistic, Tag, Space, Table,
  Select, Modal, Form, Input, Switch, InputNumber, Checkbox, message
} from 'antd';
import {
  PlusOutlined, CopyOutlined, SafetyOutlined, DashboardOutlined,
  CheckCircleOutlined, ExclamationCircleOutlined, EyeOutlined, EditOutlined,
  DeleteOutlined, ReloadOutlined, ArrowUpOutlined,
  UploadOutlined, LineChartOutlined, PieChartOutlined
} from '@ant-design/icons';
import { policyApi, namespaceApi } from '../services/api';

// Chart.js imports
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
import { Line, Doughnut } from 'react-chartjs-2';

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

const { Title, Text } = Typography;
const { Option } = Select;

interface Policy {
  id: string;
  name: string;
  type: string;
  namespaces: Array<{id: string; code: string; name: string}>;
  rules: string[];
  config: any;
  status: 'enabled' | 'disabled';
  priority: number;
  updateTime: string;
}

interface PolicyTemplate {
  id: string;
  name: string;
  type: string;
  usageCount: number;
}

const PolicyConfiguration: React.FC = () => {
  const [selectedStatus, setSelectedStatus] = useState('all');
  const [selectedType, setSelectedType] = useState('all');
  const [isAddModalVisible, setIsAddModalVisible] = useState(false);
  const [isCopyModalVisible, setIsCopyModalVisible] = useState(false);
  const [isEditModalVisible, setIsEditModalVisible] = useState(false);
  const [editingPolicy, setEditingPolicy] = useState<Policy | null>(null);
  const [selectedPolicyType, setSelectedPolicyType] = useState('message-matching');
  const [form] = Form.useForm();


  const [loading, setLoading] = useState(false);
  const [policies, setPolicies] = useState<Policy[]>([]);
  const [policyTemplates, setPolicyTemplates] = useState<PolicyTemplate[]>([]);
  
  // 命名空间选项状态
  const [namespaceOptions, setNamespaceOptions] = useState<Array<{value: string, label: string}>>([]);
  
  // 图表数据状态
  const [rateLimitTrendData, setRateLimitTrendData] = useState<any>(null);
  const [policyTypeDistributionData, setPolicyTypeDistributionData] = useState<any>(null);
  const [chartLoading, setChartLoading] = useState(false);
  const [rateLimitTimeRange, setRateLimitTimeRange] = useState('today');
  const [policyTypeFilter, setPolicyTypeFilter] = useState('all');

  // 数据加载函数
  const loadPolicyData = async () => {
    try {
      setLoading(true);
      const [policiesResponse, templatesResponse] = await Promise.all([
        policyApi.getPolicies(),
        policyApi.getPolicyTemplates()
      ]);
      
      if (policiesResponse.code === 200) {
        // API返回格式: {data: {items: [...]}}
        const data = policiesResponse.data?.items || policiesResponse.data || [];
        // 解析config字段，如果是字符串则转换为对象
        const processedData = Array.isArray(data) ? data.map(policy => ({
          ...policy,
          config: typeof policy.config === 'string' ? JSON.parse(policy.config || '{}') : policy.config
        })) : [];
        setPolicies(processedData);
      }
      if (templatesResponse.code === 200) {
        // API返回格式: {data: {items: [...]}}
        const data = templatesResponse.data?.items || templatesResponse.data || [];
        setPolicyTemplates(Array.isArray(data) ? data : []);
      }
    } catch (error) {
      message.error('加载策略数据失败');
      console.error('Load policy data error:', error);
    } finally {
      setLoading(false);
    }
  };

  // 加载命名空间列表
  const loadNamespaces = async () => {
    try {
      console.log('开始加载命名空间...');
      const response = await namespaceApi.getNamespaces(1, 100); // 获取所有命名空间
      console.log('命名空间API响应:', response);
      
      if (response.code === 200) {
        const data = response.data?.items || response.data || [];
        console.log('命名空间数据:', data);
        
        const options = data.map((ns: any, index: number) => ({
          value: ns.id || ns.namespace_id || ns.code || ns.name,
          label: ns.name || ns.code,
          key: `${ns.id || ns.namespace_id || ns.code || ns.name}-${index}` // 确保key唯一
        }));
        console.log('命名空间选项:', options);
        // 检查是否有重复的key
        const keys = options.map((opt: any) => opt.key);
        const uniqueKeys = new Set(keys);
        if (keys.length !== uniqueKeys.size) {
          console.warn('发现重复的key:', keys.filter((key: any, index: number) => keys.indexOf(key) !== index));
        }
        setNamespaceOptions(options);
      } else {
        console.error('API返回错误:', response);
        message.error(`加载命名空间失败: ${response.message || '未知错误'}`);
      }
    } catch (error: any) {
      console.error('Load namespaces error:', error);
      message.error(`加载命名空间失败: ${error.message || '网络错误'}`);
    }
  };

  // 加载限流触发趋势数据
  const loadRateLimitTrend = async (timeRange: string = 'today') => {
    try {
      setChartLoading(true);
      // 模拟API调用 - 实际项目中应该调用真实API
      const mockData = {
        labels: timeRange === 'today' 
          ? ['00:00', '03:00', '06:00', '09:00', '12:00', '15:00', '18:00', '21:00']
          : timeRange === 'week'
          ? ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
          : ['第1周', '第2周', '第3周', '第4周'],
        datasets: [{
          label: '限流触发次数',
          data: timeRange === 'today' 
            ? [0, 2, 1, 5, 12, 25, 18, 8]
            : timeRange === 'week'
            ? [15, 22, 18, 35, 28, 12, 8]
            : [120, 150, 180, 200],
          borderColor: '#F53F3F',
          backgroundColor: 'rgba(245, 63, 63, 0.1)',
          fill: true,
          tension: 0.4,
          pointRadius: 4,
          pointHoverRadius: 6
        }]
      };
      setRateLimitTrendData(mockData);
    } catch (error) {
      console.error('加载限流趋势数据失败:', error);
    } finally {
      setChartLoading(false);
    }
  };

  // 加载策略类型分布数据
  const loadPolicyTypeDistribution = async (filter: string = 'all') => {
    try {
      setChartLoading(true);
      // 模拟API调用 - 实际项目中应该调用真实API
      const mockData = {
        labels: ['限流策略', '安全策略', '混合策略', '自定义策略'],
        datasets: [{
          data: filter === 'all' 
            ? [35, 25, 20, 20]
            : filter === 'system'
            ? [40, 30, 30, 0]
            : [0, 0, 0, 100],
          backgroundColor: [
            '#165DFF',
            '#722ED1', 
            '#00B42A',
            '#F7BA1E'
          ],
          borderColor: [
            '#165DFF',
            '#722ED1',
            '#00B42A', 
            '#F7BA1E'
          ],
          borderWidth: 0,
          cutout: '60%'
        }]
      };
      setPolicyTypeDistributionData(mockData);
    } catch (error) {
      console.error('加载策略类型分布数据失败:', error);
    } finally {
      setChartLoading(false);
    }
  };

  // 组件挂载时加载数据
  useEffect(() => {
    loadPolicyData();
    loadNamespaces();
    loadRateLimitTrend();
    loadPolicyTypeDistribution();
  }, []);

  // 处理限流趋势时间范围切换
  const handleRateLimitTimeRangeChange = (timeRange: string) => {
    setRateLimitTimeRange(timeRange);
    loadRateLimitTrend(timeRange);
  };

  // 处理策略类型筛选切换
  const handlePolicyTypeFilterChange = (filter: string) => {
    setPolicyTypeFilter(filter);
    loadPolicyTypeDistribution(filter);
  };

  const handleAddPolicy = () => {
    setIsAddModalVisible(true);
  };

  const handleCopyPolicy = () => {
    setIsCopyModalVisible(true);
  };

  // 创建策略
  const handleCreatePolicy = async (values: any) => {
    try {
      // 获取选中的命名空间ID（现在只选择一个）
      const namespaceId = values.namespaces ? 
        (typeof values.namespaces === 'string' ? values.namespaces : values.namespaces.id) : null;
      
      // 构建配置对象
      const config: any = {};
      if (values.type === 'token-limit') {
        config.maxInputTokenCount = values.maxInputTokenCount;
        config.maxOutputTokenCount = values.maxOutputTokenCount;
        config.enableTimeWindow = values.enableTimeWindow;
        config.timeWindowMinutes = values.timeWindowMinutes;
        config.windowMaxTokenCount = values.windowMaxTokenCount;
      } else if (values.type === 'concurrency-limit') {
        config.maxConcurrentConnections = values.maxConcurrentConnections;
      } else if (values.type === 'qps-limit') {
        config.maxQPS = values.maxQPS;
        config.timeWindow = values.timeWindow;
      } else if (values.type === 'message-matching') {
        config.matchingFieldSource = values.matchingFieldSource;
        config.matchingFieldName = values.matchingFieldName;
        config.matchingOperator = values.matchingOperator;
        config.matchingValue = values.matchingValue;
        config.matchingAction = values.matchingAction;
      }
      
      const response = await policyApi.createPolicy({
        name: values.name,
        type: values.type,
        description: values.description || '',
        namespace_id: namespaceId,
        namespaces: values.namespaces || [],
        rules: values.rules || [],
        config: config,
        priority: values.priority || 100,
        status: 'enabled'
      });
      
      if (response.code === 200) {
        message.success('策略创建成功');
        setIsAddModalVisible(false);
        form.resetFields();
        loadPolicyData();
      } else {
        message.error(response.message || '创建失败');
      }
    } catch (error) {
      message.error('创建策略失败');
      console.error('Create policy error:', error);
    }
  };

  // 删除策略
  const handleDeletePolicy = async (policyId: string) => {
    try {
      const response = await policyApi.deletePolicy(policyId);
      if (response.code === 200) {
        message.success('策略删除成功');
        loadPolicyData();
      } else {
        message.error(response.message || '删除失败');
      }
    } catch (error) {
      message.error('删除策略失败');
      console.error('Delete policy error:', error);
    }
  };

  // 编辑策略
  const handleEditPolicy = (policy: Policy) => {
    console.log('编辑策略，接收到的数据:', policy);
    setEditingPolicy(policy);
    setSelectedPolicyType(policy.type);
    
    // 构建表单初始值
    const formValues: any = {
      name: policy.name,
      type: policy.type,
      namespaces: policy.namespaces && policy.namespaces.length > 0 ? policy.namespaces[0].id : null,
      rules: policy.rules,
      enabled: policy.status === 'enabled',
      priority: Number(policy.priority) || 100
    };
    console.log('设置表单初始值:', formValues);
    
    // 根据策略类型加载配置信息
    if (policy.config) {
      const config = policy.config;
      if (policy.type === 'token-limit') {
        formValues.maxInputTokenCount = config.maxInputTokenCount;
        formValues.maxOutputTokenCount = config.maxOutputTokenCount;
        formValues.enableTimeWindow = config.enableTimeWindow;
        formValues.timeWindowMinutes = config.timeWindowMinutes;
        formValues.windowMaxTokenCount = config.windowMaxTokenCount;
      } else if (policy.type === 'concurrency-limit') {
        formValues.maxConcurrentConnections = config.maxConcurrentConnections;
      } else if (policy.type === 'qps-limit') {
        formValues.maxQPS = config.maxQPS;
        formValues.timeWindow = config.timeWindow;
      } else if (policy.type === 'message-matching') {
        formValues.matchingFieldSource = config.matchingFieldSource;
        formValues.matchingFieldName = config.matchingFieldName;
        formValues.matchingOperator = config.matchingOperator;
        formValues.matchingValue = config.matchingValue;
        formValues.matchingAction = config.matchingAction;
      }
    }
    
    form.setFieldsValue(formValues);
    setIsEditModalVisible(true);
  };

  // 更新策略
  const handleUpdatePolicy = async (values: any) => {
    if (!editingPolicy) return;
    
    try {
      // 获取选中的命名空间ID（现在只选择一个）
      const namespaceId = values.namespaces ? 
        (typeof values.namespaces === 'string' ? values.namespaces : values.namespaces.id) : null;
      
      // 构建配置对象
      const config: any = {};
      if (values.type === 'token-limit') {
        config.maxInputTokenCount = values.maxInputTokenCount;
        config.maxOutputTokenCount = values.maxOutputTokenCount;
        config.enableTimeWindow = values.enableTimeWindow;
        config.timeWindowMinutes = values.timeWindowMinutes;
        config.windowMaxTokenCount = values.windowMaxTokenCount;
      } else if (values.type === 'concurrency-limit') {
        config.maxConcurrentConnections = values.maxConcurrentConnections;
      } else if (values.type === 'qps-limit') {
        config.maxQPS = values.maxQPS;
        config.timeWindow = values.timeWindow;
      } else if (values.type === 'message-matching') {
        config.matchingFieldSource = values.matchingFieldSource;
        config.matchingFieldName = values.matchingFieldName;
        config.matchingOperator = values.matchingOperator;
        config.matchingValue = values.matchingValue;
        config.matchingAction = values.matchingAction;
      }
      
      const updateData = {
        name: values.name,
        type: values.type,
        description: values.description || '',
        namespace_id: namespaceId,
        namespaces: values.namespaces || [],
        rules: values.rules || [],
        config: config,
        priority: Number(values.priority) || 100,
        status: values.enabled ? 'enabled' : 'disabled'
      };
      
      console.log('前端发送的更新数据:', updateData);
      console.log('表单 values:', values);
      console.log('values.priority:', values.priority);
      console.log('values.status:', values.status);
      console.log('values.enabled:', values.enabled);
      console.log('values 的所有键:', Object.keys(values));
      console.log('values.priority 类型:', typeof values.priority);
      console.log('values.priority 值:', values.priority);
      console.log('values.priority || 100 结果:', values.priority || 100);
      
      const response = await policyApi.updatePolicy(editingPolicy.id, updateData);
      
      if (response.code === 200) {
        message.success('策略更新成功');
        setIsEditModalVisible(false);
        setEditingPolicy(null);
        form.resetFields();
        loadPolicyData();
      } else {
        message.error(response.message || '更新失败');
      }
    } catch (error) {
      message.error('更新策略失败');
      console.error('Update policy error:', error);
    }
  };

  // 更新策略状态
  const handleTogglePolicyStatus = async (policyId: string, currentStatus: string) => {
    try {
      const newStatus = currentStatus === 'enabled' ? 'disabled' : 'enabled';
      const response = await policyApi.updatePolicy(policyId, { status: newStatus });
      if (response.code === 200) {
        message.success(`策略已${newStatus === 'enabled' ? '启用' : '禁用'}`);
        loadPolicyData();
      } else {
        message.error(response.message || '状态更新失败');
      }
    } catch (error) {
      message.error('更新策略状态失败');
      console.error('Update policy status error:', error);
    }
  };

  const handleModalOk = () => {
    form.validateFields().then(values => {
      handleCreatePolicy(values);
    });
  };

  const handleModalCancel = () => {
    setIsAddModalVisible(false);
    setIsCopyModalVisible(false);
    setIsEditModalVisible(false);
    setEditingPolicy(null);
    form.resetFields();
    form.setFieldsValue({ priority: 1, enabled: true });
    setSelectedPolicyType('message-matching');
  };

  const handlePolicyTypeChange = (value: string) => {
    setSelectedPolicyType(value);
  };

  const getPolicyTypeColor = (type: string) => {
    switch (type) {
      case '限流策略': return 'green';
      case '权限策略': return 'orange';
      case '安全策略': return 'purple';
      case '混合策略': return 'blue';
      default: return 'default';
    }
  };


  // 根据策略类型和配置生成规则描述
  const generateRuleDescription = (policy: Policy) => {
    if (!policy.config) {
      return policy.rules && policy.rules.length > 0 ? policy.rules[0] : '无规则';
    }

    const config = policy.config;
    
    switch (policy.type) {
      case 'token-limit':
        const maxInput = config.maxInputTokenCount || '未设置';
        const maxOutput = config.maxOutputTokenCount || '未设置';
        const timeWindow = config.enableTimeWindow ? `，时间窗口${config.timeWindowMinutes}分钟` : '';
        const windowMax = config.enableTimeWindow ? `，窗口内最多${config.windowMaxTokenCount}个Token` : '';
        return `输入${maxInput}，输出${maxOutput}${timeWindow}${windowMax}`;
        
      case 'concurrency-limit':
        const maxConcurrent = config.maxConcurrentConnections || '未设置';
        return `最大并发${maxConcurrent}个连接`;
        
      case 'qps-limit':
        const maxQPS = config.maxQPS || '未设置';
        const timeWindowSec = config.timeWindow || '未设置';
        return `每秒最多${maxQPS}个请求，${timeWindowSec}秒窗口`;
        
      case 'message-matching':
        const fieldSource = config.matchingFieldSource || '未设置';
        const fieldName = config.matchingFieldName || '未设置';
        const operator = config.matchingOperator || '未设置';
        const value = config.matchingValue || '未设置';
        const action = config.matchingAction || '未设置';
        return `${fieldSource}.${fieldName} ${operator} "${value}" → ${action}`;
        
      default:
        return policy.rules && policy.rules.length > 0 ? policy.rules[0] : '无规则';
    }
  };

  // 报文匹配规则配置组件
  const MessageMatchingConfig = () => (
    <div>
      <div style={{ 
        backgroundColor: '#f0f8ff', 
        padding: '16px', 
        borderRadius: '8px', 
        marginBottom: '16px',
        border: '1px solid #d6e4ff'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', marginBottom: '12px' }}>
          <div style={{ 
            color: '#1890ff', 
            fontSize: '16px', 
            marginRight: '8px' 
          }}>ℹ</div>
          <Text strong>报文匹配规则配置说明</Text>
        </div>
        <div style={{ fontSize: '12px', color: '#666', lineHeight: '1.6' }}>
          <div><strong>用途：</strong>基于报文内容进行访问控制,允许或拒绝特定条件的请求</div>
          <div><strong>配置要点：</strong></div>
          <div>• 匹配字段来源:选择要匹配的字段来源(报文头、请求体、查询参数、路径参数)</div>
          <div>• 匹配字段名称:输入具体的字段名(如:user_type、client_level、api_version等)</div>
          <div>• 匹配操作符:选择匹配方式(等于、包含、正则匹配等)</div>
          <div>• 匹配值:输入要匹配的具体值</div>
          <div>• 匹配动作:选择匹配成功时的处理动作(允许通过或拒绝请求)</div>
          <div><strong>示例：</strong>当请求体中的user_type字段等于"VIP"时,允许请求通过;当api_version小于"2.0"时,拒绝请求</div>
        </div>
      </div>
      
      <Form.Item name="matchingFieldSource" label="匹配字段来源" rules={[{ required: true, message: '请选择匹配字段来源' }]}>
        <Select placeholder="选择匹配字段的来源">
          <Option key="header" value="header">报文头(Header)</Option>
          <Option key="body" value="body">请求体(Body)</Option>
          <Option key="query" value="query">查询参数(Query)</Option>
          <Option key="path" value="path">路径参数(Path)</Option>
        </Select>
      </Form.Item>
      
      <Form.Item name="matchingFieldName" label="匹配字段名称" rules={[{ required: true, message: '请输入匹配字段名称' }]}>
        <Input placeholder="如:user_type, client_level, api_version" />
      </Form.Item>
      
      <Form.Item name="matchingOperator" label="匹配操作符" rules={[{ required: true, message: '请选择匹配操作符' }]}>
        <Select placeholder="选择匹配方式">
          <Option key="equals" value="equals">等于(=)</Option>
          <Option key="not_equals" value="not_equals">不等于(!=)</Option>
          <Option key="greater_than" value="greater_than">大于(&gt;)</Option>
          <Option key="greater_than_equal" value="greater_than_equal">大于等于(&gt;=)</Option>
          <Option key="less_than" value="less_than">小于(&lt;)</Option>
          <Option key="less_than_equal" value="less_than_equal">小于等于(&lt;=)</Option>
          <Option key="contains" value="contains">包含(contains)</Option>
          <Option key="starts_with" value="starts_with">开头匹配(starts_with)</Option>
          <Option key="ends_with" value="ends_with">结尾匹配(ends_with)</Option>
          <Option key="regex" value="regex">正则匹配(regex)</Option>
        </Select>
      </Form.Item>
      
      <Form.Item name="matchingValue" label="匹配值" rules={[{ required: true, message: '请输入匹配值' }]}>
        <Input placeholder="如:VIP, premium, 2.0" />
      </Form.Item>
      
      <Form.Item name="matchingAction" label="匹配动作" rules={[{ required: true, message: '请选择匹配动作' }]}>
        <Select placeholder="选择匹配成功时的动作">
          <Option key="allow" value="allow">允许通过</Option>
          <Option key="deny" value="deny">拒绝请求</Option>
        </Select>
      </Form.Item>
    </div>
  );

  // Token限制规则配置组件
  const TokenLimitConfig = () => {
    const [enableTimeWindow, setEnableTimeWindow] = useState(false);
    
    return (
      <div>
        <div style={{ 
          backgroundColor: '#f0f8ff', 
          padding: '16px', 
          borderRadius: '8px', 
          marginBottom: '16px',
          border: '1px solid #d6e4ff'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', marginBottom: '12px' }}>
            <div style={{ 
              color: '#1890ff', 
              fontSize: '16px', 
              marginRight: '8px' 
            }}>ℹ</div>
            <Text strong>Token限制规则配置说明</Text>
          </div>
          <div style={{ fontSize: '12px', color: '#666', lineHeight: '1.6' }}>
            <div><strong>用途：</strong>限制请求的Token数量,防止过度消耗AI模型资源</div>
            <div><strong>配置要点：</strong></div>
            <div>• 最大Token输入:单次请求允许的最大输入Token数</div>
            <div>• 最大Token输出:单次请求允许的最大输出Token数</div>
            <div>• 时间窗口:可选,启用后可在指定时间窗口内限制Token总量</div>
            <div>• 窗口内最大Token数:时间窗口内允许的最大Token总数,每小时最多</div>
            <div><strong>示例：</strong>限制单次请求最多4000个输入Token和2000个输出Token,每小时最多100000个Token</div>
          </div>
        </div>
        
        <Form.Item 
          name="maxInputTokenCount" 
          label="最大Token输入" 
          rules={[
            ({ getFieldValue }) => ({
              validator(_, value) {
                const policyType = getFieldValue('type');
                if (policyType === 'token-limit' && !value) {
                  return Promise.reject(new Error('请输入最大Token输入数量'));
                }
                return Promise.resolve();
              },
            }),
          ]}
        >
          <InputNumber placeholder="单次请求允许的最大输入Token数" style={{ width: '100%' }} />
        </Form.Item>
        
        <Form.Item 
          name="maxOutputTokenCount" 
          label="最大Token输出" 
          rules={[
            ({ getFieldValue }) => ({
              validator(_, value) {
                const policyType = getFieldValue('type');
                if (policyType === 'token-limit' && !value) {
                  return Promise.reject(new Error('请输入最大Token输出数量'));
                }
                return Promise.resolve();
              },
            }),
          ]}
        >
          <InputNumber placeholder="单次请求允许的最大输出Token数" style={{ width: '100%' }} />
        </Form.Item>
        
        <Form.Item name="enableTimeWindow" label="启用时间窗口" valuePropName="checked">
          <Switch onChange={(checked) => setEnableTimeWindow(checked)} />
        </Form.Item>
        
        {enableTimeWindow && (
          <>
            <Form.Item name="timeWindowMinutes" label="时间窗口(分钟)" rules={[{ required: true, message: '请输入时间窗口' }]}>
              <InputNumber placeholder="时间窗口长度(分钟)" style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item name="windowMaxTokenCount" label="窗口内最大总Token数" rules={[{ required: true, message: '请输入窗口内最大Token数' }]}>
              <InputNumber placeholder="时间窗口内允许的最大Token总数" style={{ width: '100%' }} />
            </Form.Item>
          </>
        )}
      </div>
    );
  };

  // 并发限制规则配置组件
  const ConcurrencyLimitConfig = () => (
    <div>
      <div style={{ 
        backgroundColor: '#f0f8ff', 
        padding: '16px', 
        borderRadius: '8px', 
        marginBottom: '16px',
        border: '1px solid #d6e4ff'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', marginBottom: '12px' }}>
          <div style={{ 
            color: '#1890ff', 
            fontSize: '16px', 
            marginRight: '8px' 
          }}>ℹ</div>
          <Text strong>并发限制规则配置说明</Text>
        </div>
        <div style={{ fontSize: '12px', color: '#666', lineHeight: '1.6' }}>
          <div><strong>用途：</strong>限制同时处理的请求数量，防止系统过载</div>
          <div><strong>配置要点：</strong></div>
          <div>• 最大并发连接数: 同时允许的最大请求数量</div>
          <div><strong>示例：</strong>限制该命名空间最多同时处理100个请求</div>
        </div>
      </div>
      
      <Form.Item 
        name="maxConcurrentConnections" 
        label="最大并发连接数" 
        rules={[
          ({ getFieldValue }) => ({
            validator(_, value) {
              const policyType = getFieldValue('type');
              if (policyType === 'concurrency-limit' && !value) {
                return Promise.reject(new Error('请输入最大并发连接数'));
              }
              return Promise.resolve();
            },
          }),
        ]}
      >
        <InputNumber placeholder="同时允许的最大请求数量" style={{ width: '100%' }} />
      </Form.Item>
    </div>
  );

  // QPS限制规则配置组件
  const QPSLimitConfig = () => (
    <div>
      <div style={{ 
        backgroundColor: '#f0f8ff', 
        padding: '16px', 
        borderRadius: '8px', 
        marginBottom: '16px',
        border: '1px solid #d6e4ff'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', marginBottom: '12px' }}>
          <div style={{ 
            color: '#1890ff', 
            fontSize: '16px', 
            marginRight: '8px' 
          }}>ℹ</div>
          <Text strong>QPS限制规则配置说明</Text>
        </div>
        <div style={{ fontSize: '12px', color: '#666', lineHeight: '1.6' }}>
          <div><strong>用途：</strong>限制每秒请求数,控制API调用频率</div>
          <div><strong>配置要点：</strong></div>
          <div>• 最大QPS: 每秒允许的最大请求数</div>
          <div>• 时间窗口: 统计QPS的时间窗口(秒)</div>
          <div><strong>示例：</strong>限制每秒最多10个请求,在60秒时间窗口内统计</div>
        </div>
      </div>
      
      <Form.Item 
        name="maxQPS" 
        label="最大QPS" 
        rules={[
          ({ getFieldValue }) => ({
            validator(_, value) {
              const policyType = getFieldValue('type');
              if (policyType === 'qps-limit' && !value) {
                return Promise.reject(new Error('请输入最大QPS'));
              }
              return Promise.resolve();
            },
          }),
        ]}
      >
        <InputNumber placeholder="每秒允许的最大请求数" style={{ width: '100%' }} />
      </Form.Item>
      
      <Form.Item 
        name="timeWindow" 
        label="时间窗口(秒)" 
        rules={[
          ({ getFieldValue }) => ({
            validator(_, value) {
              const policyType = getFieldValue('type');
              if (policyType === 'qps-limit' && !value) {
                return Promise.reject(new Error('请输入时间窗口'));
              }
              return Promise.resolve();
            },
          }),
        ]}
      >
        <InputNumber placeholder="统计QPS的时间窗口(秒)" style={{ width: '100%' }} />
      </Form.Item>
    </div>
  );

  // 策略列表表格列定义
  const policyColumns = [
    {
      title: (
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <Checkbox style={{ marginRight: 8 }} />
          策略名称
        </div>
      ),
      dataIndex: 'name',
      key: 'name',
      render: (text: string) => <Text strong>{text}</Text>
    },
    {
      title: '策略类型',
      dataIndex: 'type',
      key: 'type',
      render: (type: string) => (
        <Tag color={getPolicyTypeColor(type)}>{type}</Tag>
      )
    },
    {
      title: '关联命名空间',
      dataIndex: 'namespaces',
      key: 'namespaces',
      render: (namespaces: Array<{id: string; code: string; name: string}>) => (
        <Space>
          {Array.isArray(namespaces) && namespaces.length > 0 ? namespaces.map((ns, index) => (
            <Tag key={`${ns.id || ns.code || index}-${index}`} color="blue">{ns.name || ns.code}</Tag>
          )) : (
            <Text type="secondary">未关联</Text>
          )}
        </Space>
      )
    },
    {
      title: '主要规则',
      dataIndex: 'rules',
      key: 'rules',
      render: (_rules: string[], record: Policy) => {
        const ruleDescription = generateRuleDescription(record);
        return (
          <div style={{ maxWidth: 300 }}>
            <Tag color="green" style={{ margin: '2px 0', wordBreak: 'break-all' }}>
              {ruleDescription}
            </Tag>
          </div>
        );
      }
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string, record: Policy) => (
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <div 
            style={{ 
              width: 8, 
              height: 8, 
              borderRadius: '50%', 
              backgroundColor: status === 'enabled' ? '#52c41a' : '#f5222d',
              marginRight: 8 
            }} 
          />
          <Text 
            style={{ color: status === 'enabled' ? '#52c41a' : '#f5222d', fontSize: '12px', cursor: 'pointer' }}
            onClick={() => handleTogglePolicyStatus(record.id, status)}
          >
            {status === 'enabled' ? '启用' : '禁用'}
          </Text>
        </div>
      )
    },
    {
      title: '更新时间',
      dataIndex: 'updateTime',
      key: 'updateTime',
      render: (time: string) => <Text style={{ color: '#8c8c8c', fontSize: '12px' }}>{time}</Text>
    },
    {
      title: '操作',
      key: 'actions',
      render: (_: any, record: Policy) => (
        <Space size="small">
          <Button type="link" icon={<EyeOutlined />} size="small">查看</Button>
          <Button type="link" icon={<EditOutlined />} size="small" onClick={() => handleEditPolicy(record)}>编辑</Button>
          <Button 
            type="link" 
            icon={<DeleteOutlined />} 
            size="small" 
            danger
            onClick={() => handleDeletePolicy(record.id)}
          >
            删除
          </Button>
        </Space>
      )
    }
  ];

  // 策略模板表格列定义
  const templateColumns = [
    {
      title: '模板名称',
      dataIndex: 'name',
      key: 'name',
      render: (text: string) => <Text strong>{text}</Text>
    },
    {
      title: '策略类型',
      dataIndex: 'type',
      key: 'type',
      render: (type: string) => (
        <Tag color={getPolicyTypeColor(type)}>{type}</Tag>
      )
    },
    {
      title: '使用次数',
      dataIndex: 'usageCount',
      key: 'usageCount',
      render: (count: number) => <Text style={{ fontSize: '12px' }}>{count}</Text>
    },
    {
      title: '操作',
      key: 'actions',
      render: (_: any) => (
        <Space size="small">
          <Button type="link" icon={<UploadOutlined />} size="small">应用</Button>
          <Button type="link" icon={<EditOutlined />} size="small">编辑</Button>
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
            <Title level={2} style={{ margin: 0, color: '#1d2129' }}>策略配置管理</Title>
            <Text style={{ color: '#4e5969', fontSize: '14px' }}>配置和管理模型访问的限流、权限和安全策略</Text>
          </div>
          <Space>
            <Button type="primary" icon={<PlusOutlined />} onClick={handleAddPolicy}>
              创建策略
            </Button>
            <Button icon={<CopyOutlined />} onClick={handleCopyPolicy}>
              复制策略
            </Button>
            <Button 
              type="default" 
              icon={<ReloadOutlined />}
              onClick={loadNamespaces}
            >
              测试加载命名空间
            </Button>
          </Space>
        </div>
      </div>

      {/* 策略概览卡片 */}
      <Row gutter={[24, 24]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card 
            style={{ 
              borderRadius: 12, 
              boxShadow: '0 4px 20px rgba(0, 0, 0, 0.08)',
              transition: 'all 0.3s ease',
              height: '100%'
            }}
            styles={{ body: { padding: '20px' } }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <Text style={{ color: '#4e5969', fontSize: '14px' }}>总策略数</Text>
                <div style={{ marginTop: 8 }}>
                  <Statistic 
                    value={8} 
                    valueStyle={{ fontSize: '24px', fontWeight: 'bold', color: '#1d2129' }}
                  />
                </div>
                <div style={{ marginTop: 12, display: 'flex', alignItems: 'center' }}>
                  <Tag color="green" icon={<ArrowUpOutlined />}>
                    较上周增长 2
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
                <SafetyOutlined style={{ fontSize: 20 }} />
              </div>
            </div>
          </Card>
        </Col>

        <Col xs={24} sm={12} lg={6}>
          <Card 
            style={{ 
              borderRadius: 12, 
              boxShadow: '0 4px 20px rgba(0, 0, 0, 0.08)',
              transition: 'all 0.3s ease',
              height: '100%'
            }}
            styles={{ body: { padding: '20px' } }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <Text style={{ color: '#4e5969', fontSize: '14px' }}>限流触发</Text>
                <div style={{ marginTop: 8 }}>
                  <Statistic 
                    value={128} 
                    valueStyle={{ fontSize: '24px', fontWeight: 'bold', color: '#1d2129' }}
                  />
                </div>
                <div style={{ marginTop: 12, display: 'flex', alignItems: 'center' }}>
                  <Tag color="orange" icon={<ArrowUpOutlined />}>
                    今日次数
                  </Tag>
                </div>
              </div>
              <div style={{ 
                width: 48, 
                height: 48, 
                borderRadius: 8, 
                backgroundColor: 'rgba(255, 125, 0, 0.1)', 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'center',
                color: '#FF7D00'
              }}>
                <DashboardOutlined style={{ fontSize: 20 }} />
              </div>
            </div>
          </Card>
        </Col>

        <Col xs={24} sm={12} lg={6}>
          <Card 
            style={{ 
              borderRadius: 12, 
              boxShadow: '0 4px 20px rgba(0, 0, 0, 0.08)',
              transition: 'all 0.3s ease',
              height: '100%'
            }}
            styles={{ body: { padding: '20px' } }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <Text style={{ color: '#4e5969', fontSize: '14px' }}>策略应用率</Text>
                <div style={{ marginTop: 8 }}>
                  <Statistic 
                    value="100%" 
                    valueStyle={{ fontSize: '24px', fontWeight: 'bold', color: '#1d2129' }}
                  />
                </div>
                <div style={{ marginTop: 12, display: 'flex', alignItems: 'center' }}>
                  <Tag color="green" icon={<CheckCircleOutlined />}>
                    全部生效中
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
                <CheckCircleOutlined style={{ fontSize: 20 }} />
              </div>
            </div>
          </Card>
        </Col>

        <Col xs={24} sm={12} lg={6}>
          <Card 
            style={{ 
              borderRadius: 12, 
              boxShadow: '0 4px 20px rgba(0, 0, 0, 0.08)',
              transition: 'all 0.3s ease',
              height: '100%'
            }}
            styles={{ body: { padding: '20px' } }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <Text style={{ color: '#4e5969', fontSize: '14px' }}>权限拒绝</Text>
                <div style={{ marginTop: 8 }}>
                  <Statistic 
                    value={36} 
                    valueStyle={{ fontSize: '24px', fontWeight: 'bold', color: '#1d2129' }}
                  />
                </div>
                <div style={{ marginTop: 12, display: 'flex', alignItems: 'center' }}>
                  <Tag color="red" icon={<ExclamationCircleOutlined />}>
                    今日次数
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
                <ExclamationCircleOutlined style={{ fontSize: 20 }} />
              </div>
            </div>
          </Card>
        </Col>
      </Row>

      {/* 策略效果图表 */}
      <Row gutter={[24, 24]} style={{ marginBottom: 24 }}>
        <Col xs={24} lg={12}>
          <Card 
            style={{ 
              borderRadius: 12,
              boxShadow: '0 4px 20px rgba(0, 0, 0, 0.08)'
            }}
            styles={{ body: { padding: '20px' } }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
              <div style={{ display: 'flex', alignItems: 'center' }}>
                <LineChartOutlined style={{ fontSize: 20, color: '#F53F3F', marginRight: 8 }} />
                <Title level={4} style={{ margin: 0, color: '#1d2129' }}>限流触发趋势</Title>
              </div>
              <Space>
                <Button 
                  type={rateLimitTimeRange === 'today' ? 'primary' : 'default'} 
                  size="small"
                  onClick={() => handleRateLimitTimeRangeChange('today')}
                >
                  今日
                </Button>
                <Button 
                  type={rateLimitTimeRange === 'week' ? 'primary' : 'default'} 
                  size="small"
                  onClick={() => handleRateLimitTimeRangeChange('week')}
                >
                  本周
                </Button>
                <Button 
                  type={rateLimitTimeRange === 'month' ? 'primary' : 'default'} 
                  size="small"
                  onClick={() => handleRateLimitTimeRangeChange('month')}
                >
                  本月
                </Button>
              </Space>
            </div>
            <div style={{ height: 300, padding: '20px 0' }}>
              {chartLoading ? (
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
                  <Text style={{ color: '#86909c' }}>加载中...</Text>
                </div>
              ) : rateLimitTrendData ? (
                <Line 
                  data={rateLimitTrendData} 
                  options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                      legend: {
                        display: false
                      }
                    },
                    scales: {
                      y: {
                        beginAtZero: true,
                        grid: {
                          color: '#f0f0f0'
                        }
                      },
                      x: {
                        grid: {
                          color: '#f0f0f0'
                        }
                      }
                    }
                  }}
                />
              ) : (
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
                  <Text style={{ color: '#4e5969' }}>暂无数据</Text>
                </div>
              )}
            </div>
          </Card>
        </Col>

        <Col xs={24} lg={12}>
          <Card 
            style={{ 
              borderRadius: 12,
              boxShadow: '0 4px 20px rgba(0, 0, 0, 0.08)'
            }}
            styles={{ body: { padding: '20px' } }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
              <div style={{ display: 'flex', alignItems: 'center' }}>
                <PieChartOutlined style={{ fontSize: 20, color: '#165DFF', marginRight: 8 }} />
                <Title level={4} style={{ margin: 0, color: '#1d2129' }}>策略类型分布</Title>
              </div>
              <Space>
                <Button 
                  type={policyTypeFilter === 'all' ? 'primary' : 'default'} 
                  size="small"
                  onClick={() => handlePolicyTypeFilterChange('all')}
                >
                  全部
                </Button>
                <Button 
                  type={policyTypeFilter === 'system' ? 'primary' : 'default'} 
                  size="small"
                  onClick={() => handlePolicyTypeFilterChange('system')}
                >
                  系统
                </Button>
                <Button 
                  type={policyTypeFilter === 'custom' ? 'primary' : 'default'} 
                  size="small"
                  onClick={() => handlePolicyTypeFilterChange('custom')}
                >
                  自定义
                </Button>
              </Space>
            </div>
            <div style={{ height: 300, padding: '20px 0' }}>
              {chartLoading ? (
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
                  <Text style={{ color: '#86909c' }}>加载中...</Text>
                </div>
              ) : policyTypeDistributionData ? (
                <Doughnut 
                  data={policyTypeDistributionData} 
                  options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                      legend: {
                        position: 'bottom',
                        labels: {
                          padding: 20,
                          usePointStyle: true
                        }
                      }
                    }
                  }}
                />
              ) : (
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
                  <Text style={{ color: '#4e5969' }}>暂无数据</Text>
                </div>
              )}
            </div>
          </Card>
        </Col>
      </Row>

      {/* 策略列表 */}
      <Card style={{ borderRadius: 12, boxShadow: '0 4px 20px rgba(0, 0, 0, 0.08)', marginBottom: 24 }}>
        <div style={{ padding: '20px', borderBottom: '1px solid #e5e6eb', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Title level={4} style={{ margin: 0, color: '#1d2129' }}>策略配置详情</Title>
          <Space>
            <Select value={selectedStatus} onChange={setSelectedStatus} style={{ width: 120 }} placeholder="全部状态">
              <Option key="all" value="all">全部状态</Option>
              <Option key="enabled" value="enabled">启用</Option>
              <Option key="disabled" value="disabled">禁用</Option>
            </Select>
            <Select value={selectedType} onChange={setSelectedType} style={{ width: 140 }} placeholder="全部策略类型">
              <Option key="all" value="all">全部策略类型</Option>
              <Option key="rate-limit" value="rate-limit">限流策略</Option>
              <Option key="permission" value="permission">权限策略</Option>
              <Option key="security" value="security">安全策略</Option>
              <Option key="hybrid" value="hybrid">混合策略</Option>
            </Select>
            <Button icon={<ReloadOutlined />} />
          </Space>
        </div>
        <Table 
          columns={policyColumns} 
          dataSource={policies}
          loading={loading} 
          rowKey="id"
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            total: policies.length,
            showTotal: (total, range) => `显示 ${range[0]} 到 ${range[1]} 条，共 ${total} 条记录`
          }}
          style={{ borderRadius: 0 }}
        />
      </Card>

      {/* 策略模板 */}
      <Card style={{ borderRadius: 12, boxShadow: '0 4px 20px rgba(0, 0, 0, 0.08)' }}>
        <div style={{ padding: '20px', borderBottom: '1px solid #e5e6eb', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Title level={4} style={{ margin: 0, color: '#1d2129' }}>策略模板</Title>
          <Button type="link" icon={<PlusOutlined />}>创建模板</Button>
        </div>
        <Table 
          columns={templateColumns} 
          dataSource={policyTemplates} 
          rowKey="id"
          pagination={false}
          style={{ borderRadius: 0 }}
        />
      </Card>

      {/* 创建策略模态框 */}
      <Modal 
        title="创建策略" 
        open={isAddModalVisible} 
        onOk={handleModalOk} 
        onCancel={handleModalCancel}
        width={600}
      >
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="策略名称" rules={[{ required: true, message: '请输入策略名称' }]}>
            <Input placeholder="请输入策略名称" />
          </Form.Item>
          <Form.Item name="namespaces" label="关联命名空间" rules={[{ required: true, message: '请选择命名空间' }]}>
            <Select 
              placeholder="请选择命名空间" 
              loading={loading}
              optionFilterProp="children"
              filterOption={(input, option) =>
                (option?.children as unknown as string)?.toLowerCase().includes(input.toLowerCase())
              }
            >
              {namespaceOptions.map((option, index) => (
                <Option key={(option as any).key || `create-${option.value}-${index}`} value={option.value}>
                  {option.label}
                </Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="type" label="策略类型" rules={[{ required: true, message: '请选择策略类型' }]}>
            <Select 
              placeholder="请选择策略类型" 
              onChange={handlePolicyTypeChange}
              value={selectedPolicyType}
            >
              <Option key="message-matching" value="message-matching">报文匹配 - 基于字段匹配的访问控制规则</Option>
              <Option key="token-limit" value="token-limit">Token限制 - 限制请求的Token数量</Option>
              <Option key="concurrency-limit" value="concurrency-limit">并发限制 - 限制并发连接数</Option>
              <Option key="qps-limit" value="qps-limit">QPS限制 - 限制每秒请求数</Option>
            </Select>
          </Form.Item>

          {/* 动态显示不同的配置组件 */}
          {selectedPolicyType === 'message-matching' && <MessageMatchingConfig />}
          {selectedPolicyType === 'token-limit' && <TokenLimitConfig />}
          {selectedPolicyType === 'concurrency-limit' && <ConcurrencyLimitConfig />}
          {selectedPolicyType === 'qps-limit' && <QPSLimitConfig />}

          <Form.Item 
            name="priority" 
            label="优先级"
            rules={[{ required: true, message: '请设置优先级' }]}
            initialValue={100}
          >
            <div>
              <InputNumber 
                min={1} 
                max={100} 
                placeholder="1-100" 
                style={{ width: '100%' }}
              />
              <div style={{ fontSize: '12px', color: '#666', marginTop: '4px' }}>数字越小优先级越高</div>
            </div>
          </Form.Item>
          
          <Form.Item name="enabled" label="启用" valuePropName="checked">
            <Switch defaultChecked />
          </Form.Item>
        </Form>
      </Modal>

      {/* 复制策略模态框 */}
      <Modal 
        title="复制策略" 
        open={isCopyModalVisible} 
        onOk={handleModalCancel} 
        onCancel={handleModalCancel}
        width={500}
      >
        <Form layout="vertical">
          <Form.Item label="选择源策略">
            <Select placeholder="请选择要复制的策略">
              {Array.isArray(policies) && policies.map((policy, index) => (
                <Option key={`policy-${policy.id}-${index}`} value={policy.id}>{policy.name}</Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item label="新策略名称">
            <Input placeholder="请输入新策略名称" />
          </Form.Item>
        </Form>
      </Modal>

      {/* 编辑策略模态框 */}
      <Modal 
        title="编辑策略" 
        open={isEditModalVisible} 
        onOk={() => form.validateFields().then(values => handleUpdatePolicy(values))} 
        onCancel={handleModalCancel}
        width={600}
      >
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="策略名称" rules={[{ required: true, message: '请输入策略名称' }]}>
            <Input placeholder="请输入策略名称" />
          </Form.Item>
          <Form.Item name="namespaces" label="关联命名空间" rules={[{ required: true, message: '请选择命名空间' }]}>
            <Select 
              placeholder="请选择命名空间" 
              loading={loading}
              optionFilterProp="children"
              filterOption={(input, option) =>
                (option?.children as unknown as string)?.toLowerCase().includes(input.toLowerCase())
              }
            >
              {namespaceOptions.map((option, index) => (
                <Option key={(option as any).key || `edit-${option.value}-${index}`} value={option.value}>
                  {option.label}
                </Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="type" label="策略类型" rules={[{ required: true, message: '请选择策略类型' }]}>
            <Select 
              placeholder="请选择策略类型" 
              onChange={handlePolicyTypeChange}
              value={selectedPolicyType}
            >
              <Option key="message-matching" value="message-matching">报文匹配 - 基于字段匹配的访问控制规则</Option>
              <Option key="token-limit" value="token-limit">Token限制 - 限制请求的Token数量</Option>
              <Option key="concurrency-limit" value="concurrency-limit">并发限制 - 限制并发连接数</Option>
              <Option key="qps-limit" value="qps-limit">QPS限制 - 限制每秒请求数</Option>
            </Select>
          </Form.Item>

          {/* 动态显示不同的配置组件 */}
          {selectedPolicyType === 'message-matching' && <MessageMatchingConfig />}
          {selectedPolicyType === 'token-limit' && <TokenLimitConfig />}
          {selectedPolicyType === 'concurrency-limit' && <ConcurrencyLimitConfig />}
          {selectedPolicyType === 'qps-limit' && <QPSLimitConfig />}

          <Form.Item 
            name="priority" 
            label="优先级"
            rules={[{ required: true, message: '请设置优先级' }]}
            initialValue={100}
          >
            <div>
              <InputNumber 
                min={1} 
                max={100} 
                placeholder="1-100" 
                style={{ width: '100%' }}
              />
              <div style={{ fontSize: '12px', color: '#666', marginTop: '4px' }}>数字越小优先级越高</div>
            </div>
          </Form.Item>
          
          <Form.Item name="enabled" label="启用" valuePropName="checked">
            <Switch defaultChecked />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default PolicyConfiguration;
