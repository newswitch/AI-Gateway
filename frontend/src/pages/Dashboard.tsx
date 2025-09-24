import React, { useState, useEffect } from 'react';
import {
  Card, Row, Col, Select, Button, Checkbox, Typography, Statistic, Tag, Space, Table,
  Switch, message
} from 'antd';
import {
  UserOutlined, ArrowUpOutlined, ArrowDownOutlined,
  CheckCircleOutlined, ExclamationCircleOutlined,
  CalendarOutlined, CalculatorOutlined, ReloadOutlined,
  ExpandOutlined, DownloadOutlined
} from '@ant-design/icons';
import { dashboardApi } from '../services/api';
import { Line, Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title as ChartTitle,
  Tooltip as ChartTooltip,
  Legend,
} from 'chart.js';

// 注册Chart.js组件
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  ChartTitle,
  ChartTooltip,
  Legend
);

const { Option } = Select;
const { Title, Text } = Typography;

// 类型定义
interface TimeBucketData {
  time: string;
  requestCount: number;
  successCount: number;
  failCount: number;
  inputTokens: number;
  outputTokens: number;
  avgResponseTime: number;
}

const Dashboard: React.FC = () => {
  // 状态管理
  const [timeRange, setTimeRange] = useState('15m');
  const [granularity, setGranularity] = useState('minute');
  const [namespace, setNamespace] = useState('all');
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(15);
  const [loading, setLoading] = useState(false);

  // 数据状态
  const [coreMetrics, setCoreMetrics] = useState({
    totalRequests: 0,
    successRate: '0%',
    growthRate: '0%',
    inputTokens: 0,
    outputTokens: 0,
    avgInputTokens: 0,
    avgOutputTokens: 0,
    peakQPS: 0,
    currentQPS: 0
  });

  // 命名空间选项状态
  const [namespaceOptions, setNamespaceOptions] = useState<Array<{value: string, label: string}>>([
    { value: 'all', label: '全部命名空间' }
  ]);

  // 图表数据状态
  const [chartData, setChartData] = useState({
    labels: [],
    datasets: [
      {
        label: '请求量',
        data: [],
        borderColor: 'rgb(24, 144, 255)',
        backgroundColor: 'rgba(24, 144, 255, 0.1)',
        tension: 0.1,
      },
      {
        label: '输入Token',
        data: [],
        borderColor: 'rgb(82, 196, 26)',
        backgroundColor: 'rgba(82, 196, 26, 0.1)',
        tension: 0.1,
      },
      {
        label: '输出Token',
        data: [],
        borderColor: 'rgb(250, 173, 20)',
        backgroundColor: 'rgba(250, 173, 20, 0.1)',
        tension: 0.1,
      },
    ],
  });

  // 命名空间图表数据状态
  const [namespaceChartData, setNamespaceChartData] = useState({
    labels: [],
    datasets: [
      {
        label: '请求量',
        data: [],
        backgroundColor: [
          'rgba(24, 144, 255, 0.8)',
          'rgba(82, 196, 26, 0.8)',
          'rgba(250, 173, 20, 0.8)',
          'rgba(245, 34, 45, 0.8)',
          'rgba(114, 46, 209, 0.8)',
        ],
        borderColor: [
          'rgb(24, 144, 255)',
          'rgb(82, 196, 26)',
          'rgb(250, 173, 20)',
          'rgb(245, 34, 45)',
          'rgb(114, 46, 209)',
        ],
        borderWidth: 1,
      },
    ],
  });

  // 命名空间表格数据状态
  const [namespaceTableData, setNamespaceTableData] = useState([]);

  // 时间桶明细数据状态
  const [timeBucketData, setTimeBucketData] = useState<TimeBucketData[]>([]);

  // 图表配置
  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: false,
      },
    },
    scales: {
      y: {
        beginAtZero: true,
      },
    },
  };

  // 数据加载函数
  const loadDashboardData = async () => {
    try {
      setLoading(true);
      console.log('开始加载仪表盘数据...');
      console.log('API基础URL:', import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001');
      
      const [metricsResponse, namespacesResponse, realtimeResponse] = await Promise.all([
        dashboardApi.getMetrics(),
        dashboardApi.getNamespaces(),
        dashboardApi.getRealtime(timeRange, granularity, namespace === 'all' ? undefined : namespace)
      ]);
      
      console.log('API响应数据:', { metricsResponse, namespacesResponse, realtimeResponse });
      setCoreMetrics(metricsResponse.data);
      
      // 处理实时数据用于图表
      if (realtimeResponse.data && realtimeResponse.data.data) {
        const realtimeData = realtimeResponse.data.data;
        const labels = realtimeData.map((item: any) => item.timestamp);
        const requestData = realtimeData.map((item: any) => item.requests || 0);
        const inputTokenData = realtimeData.map((item: any) => item.input_tokens || 0);
        const outputTokenData = realtimeData.map((item: any) => item.output_tokens || 0);
        
        setChartData({
          labels,
          datasets: [
            {
              ...chartData.datasets[0],
              data: requestData,
            },
            {
              ...chartData.datasets[1],
              data: inputTokenData,
            },
            {
              ...chartData.datasets[2],
              data: outputTokenData,
            },
          ],
        });
      }

      // 处理命名空间数据
      if (namespacesResponse.data) {
        // API返回的数据结构是 {data: [...]} 直接数组
        const namespaces = Array.isArray(namespacesResponse.data) 
          ? namespacesResponse.data 
          : namespacesResponse.data.data || [];
        
        console.log('命名空间数据:', namespaces);
        console.log('命名空间数量:', namespaces.length);
        
        // 设置表格数据
        setNamespaceTableData(namespaces);
        
        // 设置命名空间选项
        const options = [
          { value: 'all', label: '全部命名空间' },
          ...namespaces.map((ns: any) => ({
            value: ns.code || ns.name,
            label: ns.name || ns.code
          }))
        ];
        console.log('命名空间选项:', options);
        setNamespaceOptions(options);
        
        // 设置饼图数据
        const chartLabels = namespaces.map((ns: any) => ns.name);
        const chartData = namespaces.map((ns: any) => ns.request_count || 0);
        
        setNamespaceChartData({
          labels: chartLabels,
          datasets: [
            {
              ...namespaceChartData.datasets[0],
              data: chartData,
            },
          ],
        });
      }

      // 处理时间桶数据（从实时数据生成）
      if (realtimeResponse.data && realtimeResponse.data.data) {
        const realtimeData = realtimeResponse.data.data;
        const timeBucketData = realtimeData.map((item: any, index: number) => ({
          time: item.timestamp || `10:${15 - index}`,
          requestCount: item.requests || 0,
          successCount: Math.floor((item.requests || 0) * 0.95), // 假设95%成功率
          failCount: Math.floor((item.requests || 0) * 0.05), // 假设5%失败率
          inputTokens: item.input_tokens || 0,
          outputTokens: item.output_tokens || 0,
          avgResponseTime: Math.floor(Math.random() * 100) + 350 // 模拟响应时间
        }));
        
        setTimeBucketData(timeBucketData);
      }
    } catch (error: any) {
      console.error('Dashboard data loading error:', error);
      message.error(`加载仪表盘数据失败: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  // 组件挂载时加载数据
  useEffect(() => {
    loadDashboardData();
  }, [timeRange, granularity, namespace]);

  // 自动刷新
  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(loadDashboardData, refreshInterval * 1000);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, refreshInterval, timeRange, granularity, namespace]);

  // 手动刷新函数
  const handleRefresh = () => {
    loadDashboardData();
  };


  const healthStatus = [
    { name: 'Config Center', status: 'normal', message: '连接正常，延迟 12ms' },
    { name: '网关服务', status: 'normal', message: '8/8 实例运行中' },
    { name: 'Redis', status: 'warning', message: '连接正常，内存使用率 85%' },
    { name: '数据库', status: 'normal', message: '连接正常，CPU 使用率 32%' }
  ];

  // 渲染健康状态图标
  const renderHealthStatusIcon = (status: string) => {
    switch (status) {
      case 'normal':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
      case 'warning':
        return <ExclamationCircleOutlined style={{ color: '#faad14' }} />;
      case 'error':
        return <ExclamationCircleOutlined style={{ color: '#f5222d' }} />;
      default:
        return null;
    }
  };

  return (
    <div style={{ 
      padding: '24px', 
      backgroundColor: '#f5f5f5', 
      minHeight: '100vh',
      width: '100%',
      maxWidth: '100%'
    }}>
      {/* 页面标题 */}
      <div style={{ marginBottom: 24 }}>
        <Title level={2} style={{ margin: 0, color: '#1d2129' }}>总览</Title>
        <Text style={{ color: '#4e5969', fontSize: '14px' }}>大模型网关使用情况概览与分析</Text>
        {loading && <Text style={{ color: '#1890ff', fontSize: '12px' }}>正在加载数据...</Text>}
      </div>
      
      {/* 时间与筛选区域 */}
      <Card 
        style={{ 
          marginBottom: 24, 
          borderRadius: 12, 
          boxShadow: '0 4px 20px rgba(0, 0, 0, 0.08)',
          width: '100%'
        }}
      >
        <Row gutter={[24, 24]}>
          <Col xs={24} sm={12} lg={8} xl={6}>
            <Text strong style={{ display: 'block', marginBottom: 8, color: '#4e5969' }}>时间范围</Text>
            <Space wrap>
              <Button 
                type={timeRange === '15m' ? 'primary' : 'default'} 
                onClick={() => setTimeRange('15m')}
                style={{ borderRadius: 8 }}
              >
                近15分钟
              </Button>
              <Button 
                type={timeRange === '1h' ? 'primary' : 'default'} 
                onClick={() => setTimeRange('1h')}
                style={{ borderRadius: 8 }}
              >
                1小时
              </Button>
              <Button 
                type={timeRange === '24h' ? 'primary' : 'default'} 
                onClick={() => setTimeRange('24h')}
                style={{ borderRadius: 8 }}
              >
                24小时
              </Button>
              <Button 
                type={timeRange === '7d' ? 'primary' : 'default'} 
                onClick={() => setTimeRange('7d')}
                icon={<CalendarOutlined />}
                style={{ borderRadius: 8 }}
              >
                7天
              </Button>
            </Space>
          </Col>
          
          <Col xs={24} sm={12} lg={8} xl={6}>
            <Text strong style={{ display: 'block', marginBottom: 8, color: '#4e5969' }}>统计粒度</Text>
            <Space wrap>
              <Button 
                type={granularity === 'minute' ? 'primary' : 'default'} 
                onClick={() => setGranularity('minute')}
                style={{ borderRadius: 8 }}
              >
                分钟
              </Button>
              <Button 
                type={granularity === 'hour' ? 'primary' : 'default'} 
                onClick={() => setGranularity('hour')}
                style={{ borderRadius: 8 }}
              >
                小时
              </Button>
              <Button 
                type={granularity === 'day' ? 'primary' : 'default'} 
                onClick={() => setGranularity('day')}
                style={{ borderRadius: 8 }}
              >
                天
              </Button>
            </Space>
          </Col>
          
          <Col xs={24} sm={12} lg={8} xl={6}>
            <Text strong style={{ display: 'block', marginBottom: 8, color: '#4e5969' }}>命名空间</Text>
            <Select 
              style={{ width: '100%' }} 
              value={namespace} 
              onChange={setNamespace}
              placeholder="选择命名空间"
              loading={loading}
            >
              {namespaceOptions.map(option => (
                <Option key={option.value} value={option.value}>
                  {option.label}
                </Option>
              ))}
            </Select>
          </Col>
          
          <Col xs={24} sm={12} lg={8} xl={6}>
            <Text strong style={{ display: 'block', marginBottom: 8, color: '#4e5969' }}>自动刷新</Text>
            <Space>
              <Switch 
                checked={autoRefresh} 
                onChange={setAutoRefresh}
                size="small"
              />
              <Select 
                value={refreshInterval} 
                onChange={setRefreshInterval}
                style={{ width: 120 }}
                disabled={!autoRefresh}
              >
                <Option value={15}>15秒</Option>
                <Option value={60}>60秒</Option>
              </Select>
              <Button 
                icon={<ReloadOutlined />} 
                onClick={handleRefresh}
                size="small"
              >
                手动刷新
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>
      
      {/* 核心指标卡片 */}
      <Row gutter={[24, 24]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={8} xl={6}>
          <Card 
            hoverable
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
                <Text style={{ color: '#4e5969', fontSize: '14px' }}>总用户访问量</Text>
                <div style={{ marginTop: 8 }}>
                  <Statistic 
                    value={coreMetrics.totalRequests} 
                    valueStyle={{ fontSize: '24px', fontWeight: 'bold', color: '#1d2129' }}
                  />
                </div>
                <div style={{ marginTop: 12, display: 'flex', alignItems: 'center' }}>
                  <Tag color="green" icon={<ArrowUpOutlined />} style={{ marginRight: 12 }}>
                    较昨日增长 {coreMetrics.growthRate}
                  </Tag>
                  <Text style={{ color: '#4e5969', fontSize: '12px' }}>
                    成功率: {coreMetrics.successRate}
                  </Text>
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
                <UserOutlined style={{ fontSize: 20 }} />
              </div>
            </div>
          </Card>
        </Col>
        
        <Col xs={24} sm={12} lg={8} xl={6}>
          <Card 
            hoverable
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
                <Text style={{ color: '#4e5969', fontSize: '14px' }}>输入Token总数</Text>
                <div style={{ marginTop: 8 }}>
                  <Statistic 
                    value={coreMetrics.inputTokens} 
                    valueStyle={{ fontSize: '24px', fontWeight: 'bold', color: '#1d2129' }}
                  />
                </div>
                <Tag color="green" icon={<ArrowUpOutlined />} style={{ marginTop: 12 }}>
                  较昨日增长 8.5%
                </Tag>
              </div>
              <div style={{ 
                width: 48, 
                height: 48, 
                borderRadius: 8, 
                backgroundColor: 'rgba(15, 198, 194, 0.1)', 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'center',
                color: '#0FC6C2'
              }}>
                <ArrowDownOutlined style={{ fontSize: 20 }} />
              </div>
            </div>
          </Card>
        </Col>
        
        <Col xs={24} sm={12} lg={8} xl={6}>
          <Card 
            hoverable
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
                <Text style={{ color: '#4e5969', fontSize: '14px' }}>输出Token总数</Text>
                <div style={{ marginTop: 8 }}>
                  <Statistic 
                    value={coreMetrics.outputTokens} 
                    valueStyle={{ fontSize: '24px', fontWeight: 'bold', color: '#1d2129' }}
                  />
                </div>
                <Tag color="red" icon={<ArrowDownOutlined />} style={{ marginTop: 12 }}>
                  较昨日下降 2.3%
                </Tag>
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
                <ArrowUpOutlined style={{ fontSize: 20 }} />
              </div>
            </div>
          </Card>
        </Col>
        
        <Col xs={24} sm={12} lg={8} xl={6}>
          <Card 
            hoverable
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
                <Text style={{ color: '#4e5969', fontSize: '14px' }}>当前QPS</Text>
                <div style={{ marginTop: 8 }}>
                  <Statistic 
                    value={coreMetrics.currentQPS} 
                    valueStyle={{ fontSize: '24px', fontWeight: 'bold', color: '#1d2129' }}
                  />
                </div>
                <div style={{ marginTop: 12, display: 'flex', alignItems: 'center' }}>
                  <Text style={{ color: '#4e5969', fontSize: '12px' }}>
                    峰值: {coreMetrics.peakQPS}
                  </Text>
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
                <CalculatorOutlined style={{ fontSize: 20 }} />
              </div>
            </div>
          </Card>
        </Col>
      </Row>
      
             {/* 请求与Token趋势 */}
       <Card 
         style={{ 
           marginBottom: 24, 
           borderRadius: 12,
           boxShadow: '0 4px 20px rgba(0, 0, 0, 0.08)'
         }}
         styles={{ body: { padding: '20px' } }}
       >
         <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
           <Title level={4} style={{ margin: 0, color: '#1d2129' }}>请求与Token趋势</Title>
           <Space>
             <Space>
               <Checkbox defaultChecked>请求量</Checkbox>
               <Checkbox defaultChecked>输入Token</Checkbox>
               <Checkbox defaultChecked>输出Token</Checkbox>
             </Space>
             <Button icon={<ExpandOutlined />} style={{ borderRadius: 8 }}>全屏</Button>
             <Button icon={<ReloadOutlined />} style={{ borderRadius: 8 }}>重置视图</Button>
           </Space>
         </div>
         <div style={{ height: 400, padding: '20px' }}>
           <Line data={chartData} options={chartOptions} />
         </div>
       </Card>
       
       {/* 命名空间排行 */}
       <Card 
         style={{ 
           marginBottom: 24, 
           borderRadius: 12,
           boxShadow: '0 4px 20px rgba(0, 0, 0, 0.08)'
         }}
         styles={{ body: { padding: 0 } }}
       >
         <div style={{ padding: '20px', borderBottom: '1px solid #e5e6eb' }}>
           <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
             <Title level={4} style={{ margin: 0, color: '#1d2129' }}>命名空间排行</Title>
             <Space>
               <Select defaultValue="requestCount" style={{ width: 180 }}>
                 <Option value="requestCount">按请求量排序</Option>
                 <Option value="inputTokens">按输入Token排序</Option>
                 <Option value="outputTokens">按输出Token排序</Option>
               </Select>
               <Select defaultValue="10" style={{ width: 120 }}>
                 <Option value="5">显示Top 5</Option>
                 <Option value="10">显示Top 10</Option>
                 <Option value="all">显示全部</Option>
               </Select>
             </Space>
           </div>
         </div>
         
         <div style={{ padding: '20px', borderBottom: '1px solid #e5e6eb' }}>
           <div style={{ height: 300, padding: '20px' }}>
             <Doughnut data={namespaceChartData} options={{
               responsive: true,
               maintainAspectRatio: false,
               plugins: {
                 legend: {
                   position: 'right' as const,
                 },
                 title: {
                   display: true,
                   text: '命名空间请求量分布',
                   font: {
                     size: 16,
                     weight: 'bold'
                   }
                 },
               },
             }} />
           </div>
         </div>
         
         <Table 
           columns={[
             {
               title: '命名空间',
               dataIndex: 'name',
               key: 'name',
               render: (text: string) => <Text strong>{text}</Text>
             },
             {
               title: '请求量',
               dataIndex: 'request_count',
               key: 'request_count',
               render: (value: number) => value?.toLocaleString() || 0
             },
             {
               title: '输入Token',
               dataIndex: 'input_tokens',
               key: 'input_tokens',
               render: (value: number) => value?.toLocaleString() || 0
             },
             {
               title: '输出Token',
               dataIndex: 'output_tokens',
               key: 'output_tokens',
               render: (value: number) => value?.toLocaleString() || 0
             },
             {
               title: '占比',
               dataIndex: 'percentage',
               key: 'percentage',
               render: (value: number) => `${value?.toFixed(1) || 0}%`
             },
             {
               title: '环比变化',
               dataIndex: 'growth_rate',
               key: 'growth_rate',
               render: (value: number) => (
                 <Tag color={value >= 0 ? 'green' : 'red'}>
                   {value >= 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
                   {Math.abs(value)?.toFixed(1) || 0}%
                 </Tag>
               )
             },
             {
               title: '最近活动时间',
               dataIndex: 'last_active',
               key: 'last_active',
               render: (value: string) => value || '未知'
             }
           ]}
           dataSource={namespaceTableData} 
           rowKey="name"
           pagination={{
             pageSize: 4,
             showSizeChanger: false,
             total: namespaceTableData.length,
             style: { padding: '16px 20px' }
           }}
           style={{ borderRadius: 0 }}
         />
       </Card>
       
       {/* 时间桶明细数据 */}
       <Card 
         style={{ 
           marginBottom: 24, 
           borderRadius: 12,
           boxShadow: '0 4px 20px rgba(0, 0, 0, 0.08)'
         }}
         styles={{ body: { padding: 0 } }}
       >
         <div style={{ padding: '20px', borderBottom: '1px solid #e5e6eb' }}>
           <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
             <Title level={4} style={{ margin: 0, color: '#1d2129' }}>时间桶明细数据</Title>
             <Space>
               <Button 
                 icon={<DownloadOutlined />} 
                 style={{ borderRadius: 8 }}
                 onClick={() => {
                   const csvContent = [
                     ['时间', '请求量', '成功数', '失败数', '输入Token', '输出Token', '平均响应时间(ms)'],
                     ...timeBucketData.map(item => [
                       item.time,
                       item.requestCount,
                       item.successCount,
                       item.failCount,
                       item.inputTokens,
                       item.outputTokens,
                       item.avgResponseTime
                     ])
                   ].map(row => row.join(',')).join('\n');
                   
                   const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
                   const link = document.createElement('a');
                   link.href = URL.createObjectURL(blob);
                   link.download = `时间桶明细数据_${new Date().toISOString().split('T')[0]}.csv`;
                   link.click();
                 }}
               >
                 导出CSV
               </Button>
               <Button 
                 icon={<DownloadOutlined />} 
                 style={{ borderRadius: 8 }}
                 onClick={() => {
                   const jsonContent = JSON.stringify(timeBucketData, null, 2);
                   const blob = new Blob([jsonContent], { type: 'application/json;charset=utf-8;' });
                   const link = document.createElement('a');
                   link.href = URL.createObjectURL(blob);
                   link.download = `时间桶明细数据_${new Date().toISOString().split('T')[0]}.json`;
                   link.click();
                 }}
               >
                 导出JSON
               </Button>
             </Space>
           </div>
         </div>
         
         <Table 
           columns={[
             {
               title: '时间',
               dataIndex: 'time',
               key: 'time',
               render: (text: string) => <Text strong>{text}</Text>
             },
             {
               title: '请求量',
               dataIndex: 'requestCount',
               key: 'requestCount',
               render: (value: number) => value?.toLocaleString() || 0
             },
             {
               title: '成功数',
               dataIndex: 'successCount',
               key: 'successCount',
               render: (value: number) => <Text style={{ color: '#52c41a' }}>{value?.toLocaleString() || 0}</Text>
             },
             {
               title: '失败数',
               dataIndex: 'failCount',
               key: 'failCount',
               render: (count: number) => <Text type="danger">{count?.toLocaleString() || 0}</Text>
             },
             {
               title: '输入Token',
               dataIndex: 'inputTokens',
               key: 'inputTokens',
               render: (value: number) => value?.toLocaleString() || 0
             },
             {
               title: '输出Token',
               dataIndex: 'outputTokens',
               key: 'outputTokens',
               render: (value: number) => value?.toLocaleString() || 0
             },
             {
               title: '平均响应时间(ms)',
               dataIndex: 'avgResponseTime',
               key: 'avgResponseTime',
               render: (value: number) => `${value || 0}ms`
             }
           ]}
           dataSource={timeBucketData} 
           rowKey="time"
           pagination={{
             pageSize: 5,
             showSizeChanger: false,
             total: timeBucketData.length,
             hideOnSinglePage: true,
             style: { padding: '16px 20px' }
           }}
           style={{ borderRadius: 0 }}
         />
       </Card>
       
       {/* 系统健康状态 */}
       <Card 
         style={{ 
           borderRadius: 12,
           boxShadow: '0 4px 20px rgba(0, 0, 0, 0.08)',
           width: '100%'
         }}
         styles={{ body: { padding: '20px' } }}
       >
         <Title level={4} style={{ margin: 0, marginBottom: 16, color: '#1d2129' }}>系统健康状态</Title>
         <Row gutter={[24, 24]}>
           {healthStatus.map((item, index) => (
             <Col xs={24} sm={12} lg={8} xl={6} key={index}>
               <Card
                 style={{ 
                   borderRadius: 8,
                   backgroundColor: '#fafafa',
                   border: 'none',
                   height: '100%'
                 }}
                 styles={{ body: { padding: '12px' } }}
               >
                 <div style={{ display: 'flex', alignItems: 'center' }}>
                   <div style={{ marginRight: 12 }}>
                     {renderHealthStatusIcon(item.status)}
                   </div>
                   <div>
                     <Text strong style={{ color: '#1d2129' }}>{item.name}</Text>
                     <br />
                     <Text style={{ color: '#4e5969', fontSize: '12px' }}>{item.message}</Text>
                   </div>
                 </div>
               </Card>
             </Col>
           ))}
         </Row>
       </Card>
    </div>
  );
};

export default Dashboard;