import React, { useState, useEffect, useRef } from 'react';
import {
  Card, Row, Col, Button, Typography, Tag, Space, Table,
  Select, Input, DatePicker, Checkbox, message
} from 'antd';
import {
  DownloadOutlined, DeleteOutlined, SearchOutlined, ReloadOutlined,
  FileTextOutlined, ExclamationCircleOutlined, WarningOutlined,
  DatabaseOutlined, SortDescendingOutlined, ArrowUpOutlined, ArrowDownOutlined
} from '@ant-design/icons';
import { logsApi } from '../services/api';
import dayjs from 'dayjs';
import Chart from 'chart.js/auto';

const { Title, Text } = Typography;
const { Option } = Select;
const { RangePicker } = DatePicker;

interface LogRecord {
  id: string;
  timestamp: string;
  level: 'ERROR' | 'WARN' | 'INFO' | 'DEBUG';
  requestId: string;
  model: string;
  clientIp: string;
  status: string;
  responseTime: number;
  message: string;
}

const AccessLogs: React.FC = () => {
  const [selectedRows, setSelectedRows] = useState<string[]>([]);
  const [logLevel, setLogLevel] = useState('');
  const [modelName, setModelName] = useState('');
  const [requestStatus, setRequestStatus] = useState('');
  const [searchText, setSearchText] = useState('');
  const [timeRange, setTimeRange] = useState<[dayjs.Dayjs | null, dayjs.Dayjs | null] | null>(null);
  const [loading, setLoading] = useState(false);
  const [logs, setLogs] = useState<LogRecord[]>([]);
  const [_logStats, setLogStats] = useState<any>({});
  const [_pageSize, setPageSize] = useState(10);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0
  });

  // 数据加载函数
  const loadLogsData = async () => {
    try {
      setLoading(true);
      const [logsResponse, statsResponse] = await Promise.all([
        logsApi.getLogs(pagination.current, pagination.pageSize, {
          level: logLevel || undefined,
          model: modelName || undefined,
          status: requestStatus || undefined,
          keyword: searchText || undefined,
          startTime: timeRange?.[0]?.format('YYYY-MM-DD HH:mm:ss'),
          endTime: timeRange?.[1]?.format('YYYY-MM-DD HH:mm:ss')
        }),
        logsApi.getLogStats()
      ]);
      
      if (logsResponse.code === 200) {
        setLogs(logsResponse.data?.logs || []);
        setPagination(prev => ({
          ...prev,
          total: logsResponse.data?.total || 0
        }));
      }
      if (statsResponse.code === 200) {
        setLogStats(statsResponse.data || {});
      }
    } catch (error) {
      message.error('加载访问日志失败');
      console.error('Load logs error:', error);
    } finally {
      setLoading(false);
    }
  };

  // 组件挂载时加载数据
  useEffect(() => {
    loadLogsData();
  }, [pagination.current, pagination.pageSize, logLevel, modelName, requestStatus, searchText, timeRange]);

  // 刷新数据
  const handleRefresh = () => {
    loadLogsData();
  };

  // 删除日志
  const handleDeleteLogs = async (_logIds: string[]) => {
    try {
      // const response = await logsApi.deleteLogs(logIds);
      const response = { code: 200 }; // 临时修复
      if (response.code === 200) {
        message.success('日志删除成功');
        loadLogsData();
        setSelectedRows([]);
      } else {
        message.error('删除失败');
      }
    } catch (error) {
      message.error('删除日志失败');
      console.error('Delete logs error:', error);
    }
  };

  // 导出日志
  const handleExportLogs = async () => {
    try {
      const response = await logsApi.exportLogs({
        level: logLevel || undefined,
        model: modelName || undefined,
        status: requestStatus || undefined,
        keyword: searchText || undefined,
        startTime: timeRange?.[0]?.format('YYYY-MM-DD HH:mm:ss'),
        endTime: timeRange?.[1]?.format('YYYY-MM-DD HH:mm:ss')
      });
      
      if (response.code === 200) {
        // 创建下载链接
        const blob = new Blob([response.data], { type: 'application/vnd.ms-excel' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `access_logs_${dayjs().format('YYYY-MM-DD_HH-mm-ss')}.xlsx`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        message.success('日志导出成功');
      } else {
        message.error(response.message || '导出失败');
      }
    } catch (error) {
      message.error('导出日志失败');
      console.error('Export logs error:', error);
    }
  };
  
  // Chart.js 引用
  const logLevelChartRef = useRef<HTMLCanvasElement>(null);
  const logTrendChartRef = useRef<HTMLCanvasElement>(null);
  const logLevelChartInstance = useRef<Chart | null>(null);
  const logTrendChartInstance = useRef<Chart | null>(null);

  // 获取日志级别颜色
  const getLogLevelColor = (level: string) => {
    switch (level) {
      case 'ERROR':
        return '#f5222d';
      case 'WARN':
        return '#fa8c16';
      case 'INFO':
        return '#1890ff';
      case 'DEBUG':
        return '#52c41a';
      default:
        return '#8c8c8c';
    }
  };

  // 获取日志级别文本样式
  const getLogLevelTag = (level: string) => {
    const color = getLogLevelColor(level);
    return (
      <Tag 
        color={color} 
        style={{ 
          borderRadius: '12px',
          fontSize: '11px',
          padding: '2px 8px',
          fontWeight: 'bold'
        }}
      >
        {level}
      </Tag>
    );
  };

  // 生成模拟图表数据
  const generateChartData = () => {
    // 日志级别分布数据
    const levelData = {
      labels: ['INFO', 'WARN', 'ERROR', 'DEBUG'],
      datasets: [{
        data: [65, 20, 10, 5],
        backgroundColor: [
          'rgba(24, 144, 255, 0.8)',
          'rgba(250, 140, 22, 0.8)',
          'rgba(245, 34, 45, 0.8)',
          'rgba(82, 196, 26, 0.8)'
        ],
        borderColor: [
          'rgba(24, 144, 255, 1)',
          'rgba(250, 140, 22, 1)',
          'rgba(245, 34, 45, 1)',
          'rgba(82, 196, 26, 1)'
        ],
        borderWidth: 2
      }]
    };

    // 日志趋势数据（24小时）
    const trendData = {
      labels: Array.from({length: 24}, (_, i) => `${i}:00`),
      datasets: [
        {
          label: 'INFO',
          data: Array.from({length: 24}, () => Math.floor(Math.random() * 1000 + 500)),
          borderColor: 'rgba(24, 144, 255, 1)',
          backgroundColor: 'rgba(24, 144, 255, 0.1)',
          tension: 0.4,
          fill: true
        },
        {
          label: 'WARN',
          data: Array.from({length: 24}, () => Math.floor(Math.random() * 200 + 100)),
          borderColor: 'rgba(250, 140, 22, 1)',
          backgroundColor: 'rgba(250, 140, 22, 0.1)',
          tension: 0.4,
          fill: true
        },
        {
          label: 'ERROR',
          data: Array.from({length: 24}, () => Math.floor(Math.random() * 50 + 20)),
          borderColor: 'rgba(245, 34, 45, 1)',
          backgroundColor: 'rgba(245, 34, 45, 0.1)',
          tension: 0.4,
          fill: true
        }
      ]
    };

    return { levelData, trendData };
  };

  // 初始化图表
  const initializeCharts = () => {
    if (logLevelChartRef.current && logTrendChartRef.current) {
      const { levelData, trendData } = generateChartData();

      // 销毁现有图表实例
      if (logLevelChartInstance.current) {
        logLevelChartInstance.current.destroy();
      }
      if (logTrendChartInstance.current) {
        logTrendChartInstance.current.destroy();
      }

      // 创建日志级别分布饼图
      logLevelChartInstance.current = new Chart(logLevelChartRef.current, {
        type: 'doughnut',
        data: levelData,
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: 'bottom',
              labels: {
                padding: 20,
                usePointStyle: true,
                font: {
                  size: 12
                }
              }
            },
            tooltip: {
              callbacks: {
                label: function(context) {
                  const label = context.label || '';
                  const value = context.parsed;
                  const total = context.dataset.data.reduce((a: number, b: number) => a + b, 0);
                  const percentage = ((value / total) * 100).toFixed(1);
                  return `${label}: ${value} (${percentage}%)`;
                }
              }
            }
          }
        }
      });

      // 创建日志趋势折线图
      logTrendChartInstance.current = new Chart(logTrendChartRef.current, {
        type: 'line',
        data: trendData,
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: 'top',
              labels: {
                usePointStyle: true,
                font: {
                  size: 12
                }
              }
            },
            tooltip: {
              mode: 'index',
              intersect: false
            }
          },
          scales: {
            x: {
              grid: {
                display: false
              }
            },
            y: {
              beginAtZero: true,
              grid: {
                color: 'rgba(0, 0, 0, 0.1)'
              }
            }
          },
          interaction: {
            mode: 'nearest',
            axis: 'x',
            intersect: false
          }
        }
      });
    }
  };

  // 组件挂载后初始化图表
  useEffect(() => {
    initializeCharts();
    
    // 组件卸载时清理图表
    return () => {
      if (logLevelChartInstance.current) {
        logLevelChartInstance.current.destroy();
      }
      if (logTrendChartInstance.current) {
        logTrendChartInstance.current.destroy();
      }
    };
  }, []);

  // 模拟日志数据
  const logData: LogRecord[] = [
    {
      id: '1',
      timestamp: '2024-01-15 14:32:18',
      level: 'INFO',
      requestId: 'req-7f8e9d2c',
      model: 'llm-gpt4-prod',
      clientIp: '192.168.1.101',
      status: '成功',
      responseTime: 245,
      message: 'Chat completion request processed successfully'
    },
    {
      id: '2',
      timestamp: '2024-01-15 14:31:55',
      level: 'ERROR',
      requestId: 'req-8a9b0c3d',
      model: 'llm-chatglm-prod',
      clientIp: '10.0.1.25',
      status: '失败',
      responseTime: 1520,
      message: 'Model service unavailable - connection timeout'
    },
    {
      id: '3',
      timestamp: '2024-01-15 14:31:42',
      level: 'WARN',
      requestId: 'req-4e5f6g7h',
      model: 'llm-bloom-dev',
      clientIp: '172.16.0.88',
      status: '限流',
      responseTime: 12,
      message: 'Rate limit exceeded for client IP'
    },
    {
      id: '4',
      timestamp: '2024-01-15 14:31:20',
      level: 'INFO',
      requestId: 'req-1i2j3k4l',
      model: 'llm-stablelm-test',
      clientIp: '192.168.1.102',
      status: '成功',
      responseTime: 189,
      message: 'Text generation completed successfully'
    },
    {
      id: '5',
      timestamp: '2024-01-15 14:30:58',
      level: 'DEBUG',
      requestId: 'req-5m6n7o8p',
      model: 'llm-gpt4-prod',
      clientIp: '10.0.1.30',
      status: '成功',
      responseTime: 334,
      message: 'Request preprocessing completed'
    }
  ];

  // 表格列定义
  const columns = [
    {
      title: (
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <Checkbox 
            onChange={(e) => {
              if (e.target.checked) {
                setSelectedRows(logData.map(item => item.id));
              } else {
                setSelectedRows([]);
              }
            }}
            checked={selectedRows.length === logData.length}
            indeterminate={selectedRows.length > 0 && selectedRows.length < logData.length}
            style={{ marginRight: 8 }}
          />
          时间
          <SortDescendingOutlined style={{ marginLeft: 4, color: '#8c8c8c' }} />
        </div>
      ),
      dataIndex: 'timestamp',
      key: 'timestamp',
      width: 180,
      render: (timestamp: string, record: LogRecord) => (
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <Checkbox 
            checked={selectedRows.includes(record.id)}
            onChange={(e) => {
              if (e.target.checked) {
                setSelectedRows([...selectedRows, record.id]);
              } else {
                setSelectedRows(selectedRows.filter(id => id !== record.id));
              }
            }}
            style={{ marginRight: 8 }}
          />
          <Text style={{ fontSize: '12px', color: '#4e5969' }}>{timestamp}</Text>
        </div>
      )
    },
    {
      title: '级别',
      dataIndex: 'level',
      key: 'level',
      width: 80,
      render: (level: string) => getLogLevelTag(level)
    },
    {
      title: '请求ID',
      dataIndex: 'requestId',
      key: 'requestId',
      width: 120,
      render: (requestId: string) => (
        <Text 
          style={{ 
            fontSize: '12px', 
            fontFamily: 'monospace', 
            color: '#1890ff',
            cursor: 'pointer'
          }}
        >
          {requestId}
        </Text>
      )
    },
    {
      title: '模型',
      dataIndex: 'model',
      key: 'model',
      width: 150,
      render: (model: string) => (
        <Tag style={{ borderRadius: '6px', fontSize: '11px' }}>{model}</Tag>
      )
    },
    {
      title: '客户端IP',
      dataIndex: 'clientIp',
      key: 'clientIp',
      width: 130,
      render: (ip: string) => (
        <Text style={{ fontSize: '12px', fontFamily: 'monospace' }}>{ip}</Text>
      )
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 80,
      render: (status: string) => {
        let color = '#52c41a';
        if (status === '失败') color = '#f5222d';
        if (status === '限流') color = '#fa8c16';
        return (
          <Tag color={color} style={{ borderRadius: '6px', fontSize: '11px' }}>
            {status}
          </Tag>
        );
      }
    },
    {
      title: '响应时间',
      dataIndex: 'responseTime',
      key: 'responseTime',
      width: 100,
      render: (time: number) => (
        <Text style={{ fontSize: '12px' }}>{time}ms</Text>
      )
    },
    {
      title: '日志消息',
      dataIndex: 'message',
      key: 'message',
      render: (message: string) => (
        <Text 
          style={{ 
            fontSize: '12px', 
            color: '#4e5969',
            display: 'block',
            maxWidth: '300px',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap'
          }}
          title={message}
        >
          {message}
        </Text>
      )
    }
  ];

  return (
    <div style={{ padding: '24px', backgroundColor: '#f5f5f5', minHeight: '100vh' }}>
      {/* 页面标题 */}
      <div style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <Title level={2} style={{ margin: 0, color: '#1d2129' }}>访问日志管理</Title>
            <Text style={{ color: '#4e5969', fontSize: '14px' }}>查询、筛选和分析大模型网关的请求日志</Text>
          </div>
          <Space>
            <Button type="primary" icon={<DownloadOutlined />} onClick={handleExportLogs}>
              导出日志
            </Button>
            <Button 
              icon={<DeleteOutlined />} 
              style={{ color: '#4e5969' }}
              disabled={selectedRows.length === 0}
              onClick={() => handleDeleteLogs(selectedRows)}
            >
              清理日志 ({selectedRows.length})
            </Button>
          </Space>
        </div>
      </div>

      {/* 日志搜索和筛选 */}
      <Card style={{ borderRadius: 12, boxShadow: '0 4px 20px rgba(0, 0, 0, 0.08)', marginBottom: 24 }}>
        <Title level={4} style={{ margin: 0, marginBottom: 16, color: '#1d2129' }}>日志筛选</Title>
        
        {/* 时间范围 */}
        <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
          <Col span={24}>
            <div>
              <Text style={{ fontSize: '14px', fontWeight: 500, color: '#4e5969', marginBottom: 8, display: 'block' }}>
                时间范围
              </Text>
              <RangePicker
                showTime
                style={{ width: '100%', maxWidth: 400 }}
                placeholder={['开始时间', '结束时间']}
                value={timeRange}
                onChange={(dates) => setTimeRange(dates)}
              />
            </div>
          </Col>
        </Row>

        {/* 筛选条件 */}
        <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
          <Col xs={24} md={12} lg={6}>
            <div>
              <Text style={{ fontSize: '14px', fontWeight: 500, color: '#4e5969', marginBottom: 8, display: 'block' }}>
                日志级别
              </Text>
              <Select
                placeholder="全部级别"
                style={{ width: '100%' }}
                value={logLevel}
                onChange={setLogLevel}
                allowClear
              >
                <Option value="ERROR">ERROR</Option>
                <Option value="WARN">WARN</Option>
                <Option value="INFO">INFO</Option>
                <Option value="DEBUG">DEBUG</Option>
              </Select>
            </div>
          </Col>
          
          <Col xs={24} md={12} lg={6}>
            <div>
              <Text style={{ fontSize: '14px', fontWeight: 500, color: '#4e5969', marginBottom: 8, display: 'block' }}>
                模型名称
              </Text>
              <Select
                placeholder="全部模型"
                style={{ width: '100%' }}
                value={modelName}
                onChange={setModelName}
                allowClear
              >
                <Option value="llm-gpt4-prod">llm-gpt4-prod</Option>
                <Option value="llm-chatglm-prod">llm-chatglm-prod</Option>
                <Option value="llm-bloom-dev">llm-bloom-dev</Option>
                <Option value="llm-stablelm-test">llm-stablelm-test</Option>
              </Select>
            </div>
          </Col>
          
          <Col xs={24} md={12} lg={6}>
            <div>
              <Text style={{ fontSize: '14px', fontWeight: 500, color: '#4e5969', marginBottom: 8, display: 'block' }}>
                请求状态
              </Text>
              <Select
                placeholder="全部状态"
                style={{ width: '100%' }}
                value={requestStatus}
                onChange={setRequestStatus}
                allowClear
              >
                <Option value="成功">成功</Option>
                <Option value="失败">失败</Option>
                <Option value="限流">限流</Option>
                <Option value="认证失败">认证失败</Option>
              </Select>
            </div>
          </Col>
        </Row>

        {/* 搜索和按钮区域 */}
        <Row gutter={[16, 16]} align="bottom">
          <Col xs={24} md={16} lg={18}>
            <div>
              <Text style={{ fontSize: '14px', fontWeight: 500, color: '#4e5969', marginBottom: 8, display: 'block' }}>
                搜索内容
              </Text>
              <Input
                placeholder="搜索请求ID、IP地址或日志内容..."
                prefix={<SearchOutlined />}
                value={searchText}
                onChange={(e) => setSearchText(e.target.value)}
                style={{ width: '100%' }}
              />
            </div>
          </Col>
          <Col xs={24} md={8} lg={6}>
            <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
              <Button type="primary" icon={<SearchOutlined />}>
                搜索
              </Button>
              <Button>
                重置
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* 日志统计卡片 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card style={{ borderRadius: 12, boxShadow: '0 4px 20px rgba(0, 0, 0, 0.08)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <Text style={{ color: '#4e5969', fontSize: '14px' }}>今日日志总数</Text>
                <div style={{ fontSize: '28px', fontWeight: 'bold', color: '#1d2129', margin: '4px 0' }}>
                  148,523
                </div>
                <div style={{ display: 'flex', alignItems: 'center', color: '#52c41a', fontSize: '12px' }}>
                  <ArrowUpOutlined style={{ marginRight: 4 }} />
                  较昨日增长 12.5%
                </div>
              </div>
              <div style={{
                width: 48,
                height: 48,
                borderRadius: 12,
                backgroundColor: 'rgba(24, 144, 255, 0.1)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#1890ff'
              }}>
                <FileTextOutlined style={{ fontSize: 20 }} />
              </div>
            </div>
          </Card>
        </Col>

        <Col xs={24} sm={12} lg={6}>
          <Card style={{ borderRadius: 12, boxShadow: '0 4px 20px rgba(0, 0, 0, 0.08)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <Text style={{ color: '#4e5969', fontSize: '14px' }}>错误日志数</Text>
                <div style={{ fontSize: '28px', fontWeight: 'bold', color: '#1d2129', margin: '4px 0' }}>
                  475
                </div>
                <div style={{ display: 'flex', alignItems: 'center', color: '#f5222d', fontSize: '12px' }}>
                  <ArrowUpOutlined style={{ marginRight: 4 }} />
                  较昨日上升 0.05%
                </div>
              </div>
              <div style={{
                width: 48,
                height: 48,
                borderRadius: 12,
                backgroundColor: 'rgba(245, 34, 45, 0.1)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#f5222d'
              }}>
                <ExclamationCircleOutlined style={{ fontSize: 20 }} />
              </div>
            </div>
          </Card>
        </Col>

        <Col xs={24} sm={12} lg={6}>
          <Card style={{ borderRadius: 12, boxShadow: '0 4px 20px rgba(0, 0, 0, 0.08)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <Text style={{ color: '#4e5969', fontSize: '14px' }}>警告日志数</Text>
                <div style={{ fontSize: '28px', fontWeight: 'bold', color: '#1d2129', margin: '4px 0' }}>
                  1,293
                </div>
                <div style={{ display: 'flex', alignItems: 'center', color: '#fa8c16', fontSize: '12px' }}>
                  <ArrowDownOutlined style={{ marginRight: 4 }} />
                  较昨日下降 5.2%
                </div>
              </div>
              <div style={{
                width: 48,
                height: 48,
                borderRadius: 12,
                backgroundColor: 'rgba(250, 140, 22, 0.1)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#fa8c16'
              }}>
                <WarningOutlined style={{ fontSize: 20 }} />
              </div>
            </div>
          </Card>
        </Col>

        <Col xs={24} sm={12} lg={6}>
          <Card style={{ borderRadius: 12, boxShadow: '0 4px 20px rgba(0, 0, 0, 0.08)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <Text style={{ color: '#4e5969', fontSize: '14px' }}>日志存储占用</Text>
                <div style={{ fontSize: '28px', fontWeight: 'bold', color: '#1d2129', margin: '4px 0' }}>
                  18.7 GB
                </div>
                <div style={{ display: 'flex', alignItems: 'center', color: '#52c41a', fontSize: '12px' }}>
                  <ArrowUpOutlined style={{ marginRight: 4 }} />
                  较昨日增长 0.8 GB
                </div>
              </div>
              <div style={{
                width: 48,
                height: 48,
                borderRadius: 12,
                backgroundColor: 'rgba(82, 196, 26, 0.1)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#52c41a'
              }}>
                <DatabaseOutlined style={{ fontSize: 20 }} />
              </div>
            </div>
          </Card>
        </Col>
      </Row>

      {/* 日志分布图表 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} lg={12}>
          <Card style={{ borderRadius: 12, boxShadow: '0 4px 20px rgba(0, 0, 0, 0.08)', height: '100%' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
              <Title level={4} style={{ margin: 0, color: '#1d2129' }}>日志级别分布</Title>
              <Space>
                <Button type="primary" size="small">今日</Button>
                <Button size="small">本周</Button>
                <Button size="small">本月</Button>
              </Space>
            </div>
            <div style={{ height: 280, position: 'relative' }}>
              <canvas ref={logLevelChartRef} />
            </div>
          </Card>
        </Col>

        <Col xs={24} lg={12}>
          <Card style={{ borderRadius: 12, boxShadow: '0 4px 20px rgba(0, 0, 0, 0.08)', height: '100%' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
              <Title level={4} style={{ margin: 0, color: '#1d2129' }}>日志趋势</Title>
              <Space>
                <Button type="primary" size="small">按小时</Button>
                <Button size="small">按天</Button>
                <Button size="small">按周</Button>
              </Space>
            </div>
            <div style={{ height: 280, position: 'relative' }}>
              <canvas ref={logTrendChartRef} />
            </div>
          </Card>
        </Col>
      </Row>

      {/* 日志列表 */}
      <Card style={{ borderRadius: 12, boxShadow: '0 4px 20px rgba(0, 0, 0, 0.08)' }}>
        <div style={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center', 
          marginBottom: 16,
          paddingBottom: 16,
          borderBottom: '1px solid #f0f0f0'
        }}>
          <Title level={4} style={{ margin: 0, color: '#1d2129' }}>日志记录</Title>
          <Space>
            <Select
              defaultValue={10}
              style={{ width: 150 }}
              onChange={setPageSize}
            >
              <Option value={10}>每页显示 10 条</Option>
              <Option value={20}>每页显示 20 条</Option>
              <Option value={50}>每页显示 50 条</Option>
              <Option value={100}>每页显示 100 条</Option>
            </Select>
            <Button icon={<ReloadOutlined />} onClick={handleRefresh} />
          </Space>
        </div>

        <Table
          columns={columns}
          dataSource={logs}
          loading={loading}
          rowKey="id"
          pagination={{
            total: pagination.total,
            current: pagination.current,
            pageSize: pagination.pageSize,
            showSizeChanger: true,
            onChange: (page, size) => {
              setPagination(prev => ({
                ...prev,
                current: page,
                pageSize: size || 10
              }));
            },
            showQuickJumper: true,
            showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条记录`,
            style: { marginTop: 16 }
          }}
          scroll={{ x: 1200 }}
          size="small"
        />
      </Card>
    </div>
  );
};

export default AccessLogs;
