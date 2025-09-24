import React, { useState, useEffect } from 'react';
import {
  Card, Row, Col, Button, Typography, Space,
  Select, Form, Input, Switch, InputNumber, Tabs,
  Alert, message, Upload, Divider
} from 'antd';
import {
  SaveOutlined, UploadOutlined, DownloadOutlined, CheckCircleOutlined, RocketOutlined
} from '@ant-design/icons';
import { configApi } from '../services/api';

const { Title, Text } = Typography;
const { Option } = Select;
// TabPane已弃用，使用items属性

interface NginxConfig {
  user: string;
  worker_processes: string;
  error_log: string;
  pid: string;
  events: {
    use: string;
    worker_connections: number;
    multi_accept: boolean;
  };
  http: {
    client_max_body_size: string;
    proxy_http_version: string;
    proxy_buffers: string;
    proxy_buffer_size: string;
    proxy_busy_buffers_size: string;
    proxy_connect_timeout: string;
    proxy_read_timeout: string;
    proxy_send_timeout: string;
    keepalive_timeout: string;
    keepalive_requests: number;
    access_log: string;
    log_format: string;
    sendfile: boolean;
    tcp_nopush: boolean;
    tcp_nodelay: boolean;
    server: {
      listen: number;
      server_name: string;
      proxy_headers: {
        host: boolean;
        real_ip: boolean;
        forwarded_for: boolean;
        forwarded_proto: boolean;
        connection: boolean;
      };
      health_check: {
        enabled: boolean;
        path: string;
      };
    };
    limit_req: {
      enabled: boolean;
      zone: string;
      rate: string;
    };
  };
}

const UnifiedNginxConfig: React.FC = () => {
  const [activeTab, setActiveTab] = useState('visual');
  const [config, setConfig] = useState<NginxConfig | null>(null);
  const [rawConfig, setRawConfig] = useState('');
  const [isConfigValid, setIsConfigValid] = useState(true);
  const [validationErrors, setValidationErrors] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  // const [deployStatus, setDeployStatus] = useState<string>('');

  // 数据加载函数
  const loadConfigData = async () => {
    try {
      setLoading(true);
      const response = await configApi.getNginxConfig();
      if (response.code === 200) {
        // API返回的数据结构是 {data: {global, events, http, server, system, rate_limit}}
        // 需要转换为前端期望的格式
        const apiData = response.data;
        if (apiData) {
          // 构造NginxConfig对象 - 使用API返回的真实数据
          const nginxConfig: NginxConfig = {
            user: 'nginx',
            worker_processes: apiData.global?.worker_processes || 'auto',
            error_log: apiData.global?.error_log || '/var/log/nginx/error.log',
            pid: apiData.global?.pid || '/var/run/nginx.pid',
            events: {
              use: apiData.events?.use || 'epoll',
              worker_connections: apiData.events?.worker_connections || 1024,
              multi_accept: apiData.events?.multi_accept === 'on'
            },
            http: {
              client_max_body_size: apiData.system?.client_max_body_size || apiData.http?.client_max_body_size || '100m',
              proxy_http_version: '1.1',
              proxy_buffers: '4 32k',
              proxy_buffer_size: '8k',
              proxy_busy_buffers_size: '64k',
              proxy_connect_timeout: apiData.system?.client_body_timeout || '60s',
              proxy_read_timeout: apiData.system?.client_header_timeout || '60s',
              proxy_send_timeout: apiData.system?.send_timeout || '60s',
              keepalive_timeout: apiData.http?.keepalive_timeout || '65',
              keepalive_requests: 1000,
              access_log: apiData.http?.access_log || '/var/log/nginx/access.log main',
              log_format: apiData.http?.log_format || 'main',
              sendfile: apiData.http?.sendfile === 'on',
              tcp_nopush: apiData.http?.tcp_nopush === 'on',
              tcp_nodelay: apiData.http?.tcp_nodelay === 'on',
              server: {
                listen: apiData.server?.listen || 80,
                server_name: apiData.server?.server_name || 'localhost',
                proxy_headers: {
                  host: true,
                  real_ip: true,
                  forwarded_for: true,
                  forwarded_proto: true,
                  connection: true
                },
                health_check: {
                  enabled: true,
                  path: '/health'
                }
              },
              limit_req: {
                enabled: !!apiData.rate_limit?.limit_req_zone,
                zone: apiData.rate_limit?.limit_req_zone?.split(' ')[2] || 'llm:10m',
                rate: apiData.rate_limit?.limit_req_zone?.split(' ')[3] || '10r/s'
              }
            }
          };
          
          setConfig(nginxConfig);
          // 生成原始配置文本
          const rawConfigText = generateRawConfig(nginxConfig);
          setRawConfig(rawConfigText);
          setIsConfigValid(true);
          setValidationErrors([]);
        }
      } else {
        message.error('加载配置失败');
      }
    } catch (error) {
      message.error('加载配置失败');
      console.error('Load config error:', error);
    } finally {
      setLoading(false);
    }
  };

  // 生成原始配置文本的函数 - 使用真实配置数据
  const generateRawConfig = (config: NginxConfig): string => {
    let configText = `user ${config.user};
worker_processes ${config.worker_processes};
error_log ${config.error_log};
pid ${config.pid};

events {
    use ${config.events.use};
    worker_connections ${config.events.worker_connections};
    multi_accept ${config.events.multi_accept ? 'on' : 'off'};
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    
    client_max_body_size ${config.http.client_max_body_size};
    proxy_http_version ${config.http.proxy_http_version};
    proxy_buffers ${config.http.proxy_buffers};
    proxy_buffer_size ${config.http.proxy_buffer_size};
    proxy_busy_buffers_size ${config.http.proxy_busy_buffers_size};
    proxy_connect_timeout ${config.http.proxy_connect_timeout};
    proxy_read_timeout ${config.http.proxy_read_timeout};
    proxy_send_timeout ${config.http.proxy_send_timeout};
    keepalive_timeout ${config.http.keepalive_timeout};
    keepalive_requests ${config.http.keepalive_requests};
    
    access_log ${config.http.access_log};
    log_format ${config.http.log_format} '$remote_addr - $remote_user [$time_local] "$request" $status $body_bytes_sent "$http_referer" "$http_user_agent" "$http_x_forwarded_for"';
    
    sendfile ${config.http.sendfile ? 'on' : 'off'};
    tcp_nopush ${config.http.tcp_nopush ? 'on' : 'off'};
    tcp_nodelay ${config.http.tcp_nodelay ? 'on' : 'off'}`;

    // 添加限流配置
    if (config.http.limit_req.enabled) {
      configText += `
    
    # 限流配置
    limit_req_zone $binary_remote_addr zone=${config.http.limit_req.zone.split(':')[0]}:${config.http.limit_req.zone.split(':')[1]} rate=${config.http.limit_req.rate};`;
    }

    configText += `
    
    server {
        listen ${config.http.server.listen};
        server_name ${config.http.server.server_name};
        
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Connection "";`;

    // 添加健康检查配置
    if (config.http.server.health_check.enabled) {
      configText += `
        
        # 健康检查
        location ${config.http.server.health_check.path} {
            access_log off;
            return 200 "healthy\\n";
            add_header Content-Type text/plain;
        }`;
    }

    // 添加限流应用到location
    if (config.http.limit_req.enabled) {
      configText += `
        
        # 应用限流
        location / {
            limit_req zone=${config.http.limit_req.zone.split(':')[0]} burst=20 nodelay;
            root /usr/share/nginx/html;
            index index.html index.htm;
        }`;
    } else {
      configText += `
        
        location / {
            root /usr/share/nginx/html;
            index index.html index.htm;
        }`;
    }

    configText += `
    }
}`;

    return configText;
  };

  // 组件挂载时加载数据
  useEffect(() => {
    loadConfigData();
  }, []);

  // 保存配置
  const handleSaveConfig = async () => {
    try {
      setLoading(true);
      const response = await configApi.updateNginxConfig({
        config: config,
        rawConfig: rawConfig
      });
      
      if (response.code === 200) {
        message.success('配置保存成功');
        loadConfigData();
      } else {
        message.error(response.message || '保存失败');
      }
    } catch (error) {
      message.error('保存配置失败');
      console.error('Save config error:', error);
    } finally {
      setLoading(false);
    }
  };

  // 部署配置
  const handleDeployConfig = async () => {
    try {
      setLoading(true);
      const response = await configApi.deployConfig();
      
      if (response.code === 200) {
        message.success('配置部署成功');
        // setDeployStatus('deployed');
        loadConfigData();
      } else {
        message.error(response.message || '部署失败');
        // setDeployStatus('failed');
      }
    } catch (error) {
      message.error('部署配置失败');
      console.error('Deploy config error:', error);
      // setDeployStatus('failed');
    } finally {
      setLoading(false);
    }
  };

  // 验证配置
  const handleValidateConfig = async () => {
    try {
      setLoading(true);
      const response = await configApi.validateConfig({
        rawConfig: rawConfig
      });
      
      if (response.code === 200) {
        setIsConfigValid(response.data?.isValid || false);
        setValidationErrors(response.data?.errors || []);
        if (response.data?.isValid) {
          message.success('配置验证通过');
        } else {
          message.error('配置验证失败');
        }
      } else {
        message.error(response.message || '验证失败');
      }
    } catch (error) {
      message.error('验证配置失败');
      console.error('Validate config error:', error);
    } finally {
      setLoading(false);
    }
  };

  // 解析Nginx配置文件的函数
  const parseNginxConfig = (configText: string): NginxConfig => {
    const lines = configText.split('\n').map(line => line.trim()).filter(line => line && !line.startsWith('#'));

    const config: NginxConfig = {
      user: 'nginx',
      worker_processes: 'auto',
      error_log: '/var/log/nginx/error.log notice',
      pid: '/var/run/nginx.pid',
      events: {
        use: 'epoll',
        worker_connections: 4096,
        multi_accept: false
      },
      http: {
        client_max_body_size: '256M',
        proxy_http_version: '1.1',
        proxy_buffers: '4 256K',
        proxy_buffer_size: '256K',
        proxy_busy_buffers_size: '512K',
        proxy_connect_timeout: '900s',
        proxy_read_timeout: '1800s',
        proxy_send_timeout: '1800s',
        keepalive_timeout: '180s',
        keepalive_requests: 100,
        access_log: '/var/log/nginx/access.log main',
        log_format: 'main',
        sendfile: true,
        tcp_nopush: true,
        tcp_nodelay: true,
        server: {
          listen: 8080,
          server_name: 'localhost',
          proxy_headers: {
            host: true,
            real_ip: true,
            forwarded_for: true,
            forwarded_proto: true,
            connection: true
          },
          health_check: {
            enabled: false,
            path: '/health'
          }
        },
        limit_req: {
          enabled: false,
          zone: 'llm:10m',
          rate: '30r/s'
        }
      }
    };

    // 解析配置
    let inEvents = false;
    let inHttp = false;
    let inServer = false;

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      
      // 解析全局配置
      if (line.startsWith('user ')) {
        config.user = line.replace('user ', '').replace(';', '');
      } else if (line.startsWith('worker_processes ')) {
        config.worker_processes = line.replace('worker_processes ', '').replace(';', '');
      } else if (line.startsWith('error_log ')) {
        config.error_log = line.replace('error_log ', '').replace(';', '');
      } else if (line.startsWith('pid ')) {
        config.pid = line.replace('pid ', '').replace(';', '');
      }
      
      // 解析events块
      if (line.startsWith('events {')) {
        inEvents = true;
      } else if (line === '}' && inEvents) {
        inEvents = false;
      } else if (inEvents && line.startsWith('use ')) {
        config.events.use = line.replace('use ', '').replace(';', '');
      } else if (inEvents && line.startsWith('worker_connections ')) {
        const match = line.match(/worker_connections\s+(\d+);/);
        if (match) {
          config.events.worker_connections = parseInt(match[1]);
        }
      } else if (inEvents && line.startsWith('multi_accept ')) {
        config.events.multi_accept = line.includes('on');
      }
      
      // 解析http块
      if (line.startsWith('http {')) {
        inHttp = true;
      } else if (line === '}' && inHttp) {
        inHttp = false;
      } else if (inHttp && line.startsWith('client_max_body_size ')) {
        config.http.client_max_body_size = line.replace('client_max_body_size ', '').replace(';', '');
      } else if (inHttp && line.startsWith('proxy_http_version ')) {
        config.http.proxy_http_version = line.replace('proxy_http_version ', '').replace(';', '');
      } else if (inHttp && line.startsWith('proxy_buffers ')) {
        config.http.proxy_buffers = line.replace('proxy_buffers ', '').replace(';', '');
      } else if (inHttp && line.startsWith('proxy_buffer_size ')) {
        config.http.proxy_buffer_size = line.replace('proxy_buffer_size ', '').replace(';', '');
      } else if (inHttp && line.startsWith('proxy_busy_buffers_size ')) {
        config.http.proxy_busy_buffers_size = line.replace('proxy_busy_buffers_size ', '').replace(';', '');
      } else if (inHttp && line.startsWith('proxy_connect_timeout ')) {
        config.http.proxy_connect_timeout = line.replace('proxy_connect_timeout ', '').replace(';', '');
      } else if (inHttp && line.startsWith('proxy_read_timeout ')) {
        config.http.proxy_read_timeout = line.replace('proxy_read_timeout ', '').replace(';', '');
      } else if (inHttp && line.startsWith('proxy_send_timeout ')) {
        config.http.proxy_send_timeout = line.replace('proxy_send_timeout ', '').replace(';', '');
      } else if (inHttp && line.startsWith('keepalive_timeout ')) {
        config.http.keepalive_timeout = line.replace('keepalive_timeout ', '').replace(';', '');
      } else if (inHttp && line.startsWith('keepalive_requests ')) {
        const match = line.match(/keepalive_requests\s+(\d+);/);
        if (match) {
          config.http.keepalive_requests = parseInt(match[1]);
        }
      } else if (inHttp && line.startsWith('access_log ')) {
        config.http.access_log = line.replace('access_log ', '').replace(';', '');
      } else if (inHttp && line.startsWith('log_format ')) {
        config.http.log_format = line.replace('log_format ', '').split(' ')[0];
      } else if (inHttp && line.startsWith('sendfile ')) {
        config.http.sendfile = line.includes('on');
      } else if (inHttp && line.startsWith('tcp_nopush ')) {
        config.http.tcp_nopush = line.includes('on');
      } else if (inHttp && line.startsWith('tcp_nodelay ')) {
        config.http.tcp_nodelay = line.includes('on');
      } else if (inHttp && line.startsWith('limit_req_zone ')) {
        const match = line.match(/limit_req_zone\s+\$binary_remote_addr\s+zone=([^:]+):([^;]+);/);
        if (match) {
          config.http.limit_req.enabled = true;
          config.http.limit_req.zone = `${match[1]}:${match[2]}`;
        }
        const rateMatch = line.match(/rate=([^;]+);/);
        if (rateMatch) {
          config.http.limit_req.rate = rateMatch[1];
        }
      }
      
      // 解析server块
      if (line.startsWith('server {')) {
        inServer = true;
      } else if (line === '}' && inServer) {
        inServer = false;
      } else if (inServer && line.startsWith('listen ')) {
        const listenMatch = line.match(/listen\s+(\d+);/);
        if (listenMatch) {
          config.http.server.listen = parseInt(listenMatch[1]);
        }
      } else if (inServer && line.startsWith('server_name ')) {
        const serverNameMatch = line.match(/server_name\s+([^;]+);/);
        if (serverNameMatch) {
          config.http.server.server_name = serverNameMatch[1];
        }
      } else if (inServer && line.startsWith('location /health')) {
        config.http.server.health_check.enabled = true;
      }
    }

    return config;
  };

  // 将配置对象转换为Nginx配置文件文本
  const configToText = (config: NginxConfig): string => {
    let text = `user ${config.user};
worker_processes ${config.worker_processes};

error_log ${config.error_log};
pid ${config.pid};

events {
    use ${config.events.use};
    worker_connections ${config.events.worker_connections};${config.events.multi_accept ? '\n    multi_accept on;  # 提高连接接收效率' : ''}
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for" '
                    '"$upstream_addr" "$request_time"';  # 增加请求耗时统计

    client_max_body_size ${config.http.client_max_body_size};
    proxy_http_version ${config.http.proxy_http_version};
    proxy_buffers ${config.http.proxy_buffers};
    proxy_buffer_size ${config.http.proxy_buffer_size};
    proxy_busy_buffers_size ${config.http.proxy_busy_buffers_size};
    proxy_connect_timeout ${config.http.proxy_connect_timeout};
    proxy_read_timeout ${config.http.proxy_read_timeout};  # 大模型推理耗时较长，保持长超时
    proxy_send_timeout ${config.http.proxy_send_timeout};
    keepalive_timeout ${config.http.keepalive_timeout};
    keepalive_requests ${config.http.keepalive_requests};
    access_log ${config.http.access_log} main;

    # 启用TCP_NODELAY提高实时性，适合流式响应
    tcp_nodelay ${config.http.tcp_nodelay ? 'on' : 'off'};
    # 启用sendfile提高文件传输效率
    sendfile ${config.http.sendfile ? 'on' : 'off'};
    tcp_nopush ${config.http.tcp_nopush ? 'on' : 'off'};

`;

    // Add limit_req_zone config
    if (config.http.limit_req.enabled) {
      text += `    # 配置请求速率限制
    limit_req_zone $binary_remote_addr zone=${config.http.limit_req.zone} rate=${config.http.limit_req.rate};

`;
    }

    // Add server config
    text += `    server {
        listen ${config.http.server.listen};
        server_name ${config.http.server.server_name};  # 可根据需要添加域名

        # 通用代理配置，减少重复代码
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Connection "";  # 清除连接头，使用keepalive

`;

    // Location配置由模型路由页面管理

    // Add health check
    if (config.http.server.health_check.enabled) {
      text += `        # 可选：监控接口
        location ${config.http.server.health_check.path} {
            return 200 'OK';
            add_header Content-Type text/plain;
        }

`;
    }

    text += `    }

    include /etc/nginx/conf.d/*.conf;
}`;

    return text;
  };

  // 验证配置
  const validateConfig = (config: NginxConfig): { isValid: boolean; errors: string[] } => {
    const errors: string[] = [];

    if (!config.user) errors.push('用户配置不能为空');
    if (!config.worker_processes) errors.push('工作进程数不能为空');
    if (!config.error_log) errors.push('错误日志路径不能为空');
    if (!config.pid) errors.push('PID文件路径不能为空');
    if (!config.events.use) errors.push('事件模型不能为空');
    if (config.events.worker_connections <= 0) errors.push('工作连接数必须大于0');
    if (!config.http.client_max_body_size) errors.push('客户端最大请求体大小不能为空');
    if (!config.http.proxy_http_version) errors.push('代理HTTP版本不能为空');
    if (config.http.server.listen <= 0 || config.http.server.listen > 65535) {
      errors.push('监听端口必须在1-65535之间');
    }

    return {
      isValid: errors.length === 0,
      errors
    };
  };

  // 初始化配置
  useEffect(() => {
    const defaultConfigText = `user nginx;
worker_processes auto;

error_log /var/log/nginx/error.log notice;
pid /var/run/nginx.pid;

events {
    use epoll;
    worker_connections 4096;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for" '
                    '"$upstream_addr"';

    client_max_body_size 256M;
    proxy_http_version 1.1;
    proxy_buffers 4 256K;
    proxy_buffer_size 256K;
    proxy_busy_buffers_size 512K;
    proxy_connect_timeout 900s;
    proxy_read_timeout 1800s;
    keepalive_timeout 180s;
    keepalive_requests 100;
    access_log /var/log/nginx/access.log main;

    server {
        listen 8080;

        # 通用代理配置，减少重复代码
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Connection "";  # 清除连接头，使用keepalive

        # Location配置由模型路由页面管理
    }

    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;

    include /etc/nginx/conf.d/*.conf;
}`;

    setRawConfig(defaultConfigText);
    const parsedConfig = parseNginxConfig(defaultConfigText);
    setConfig(parsedConfig);
    const validation = validateConfig(parsedConfig);
    setIsConfigValid(validation.isValid);
    setValidationErrors(validation.errors);
  }, []);

  // 处理配置更新
  const handleConfigUpdate = (newConfig: NginxConfig) => {
    setConfig(newConfig);
    const validation = validateConfig(newConfig);
    setIsConfigValid(validation.isValid);
    setValidationErrors(validation.errors);
    setRawConfig(configToText(newConfig));
  };

  // 处理原始配置文本变化
  const handleRawConfigChange = (value: string) => {
    setRawConfig(value);
    try {
      const parsedConfig = parseNginxConfig(value);
      setConfig(parsedConfig);
      const validation = validateConfig(parsedConfig);
      setIsConfigValid(validation.isValid);
      setValidationErrors(validation.errors);
    } catch (error) {
      setIsConfigValid(false);
      setValidationErrors(['配置文件格式错误']);
    }
  };

  // 导出配置
  const handleExportConfig = () => {
    const blob = new Blob([rawConfig], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'nginx.conf';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    message.success('配置导出成功');
  };

  // 导入配置
  const handleImportConfig = (file: any) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const content = e.target?.result as string;
      handleRawConfigChange(content);
      message.success('配置导入成功');
    };
    reader.readAsText(file);
    return false; // 阻止默认上传行为
  };

  if (!config) {
    return <div>加载中...</div>;
  }

  return (
    <div style={{ padding: '24px', backgroundColor: '#f5f5f5', minHeight: '100vh' }}>
      {/* 页面标题 */}
      <div style={{ marginBottom: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <Title level={2} style={{ margin: 0, color: '#1d2129' }}>统一配置管理</Title>
            <Text style={{ color: '#4e5969', fontSize: '14px' }}>管理Nginx系统级配置，upstream和location配置请使用模型路由页面</Text>
          </div>
          <Space>
            <Upload beforeUpload={handleImportConfig} showUploadList={false}>
              <Button icon={<UploadOutlined />}>
                导入配置
              </Button>
            </Upload>
            <Button icon={<DownloadOutlined />} onClick={handleExportConfig}>
              导出配置
            </Button>
            <Button type="primary" icon={<SaveOutlined />} onClick={handleSaveConfig} loading={loading}>
              保存配置
            </Button>
            <Button icon={<CheckCircleOutlined />} onClick={handleValidateConfig} loading={loading}>
              验证配置
            </Button>
            <Button type="primary" icon={<RocketOutlined />} onClick={handleDeployConfig} loading={loading}>
              部署配置
            </Button>
          </Space>
        </div>
      </div>

      {/* 配置状态 */}
      {!isConfigValid && (
        <Alert
          message="配置验证失败"
          description={
            <div>
              <Text>发现以下问题：</Text>
              <ul style={{ marginTop: 8, marginBottom: 0 }}>
                {validationErrors.map((error, index) => (
                  <li key={index}>{error}</li>
                ))}
              </ul>
            </div>
          }
          type="error"
          showIcon
          style={{ marginBottom: 24 }}
        />
      )}

      {/* 主配置区域 */}
      <Card style={{ borderRadius: 12, boxShadow: '0 4px 20px rgba(0, 0, 0, 0.08)' }}>
        <Tabs 
          activeKey={activeTab} 
          onChange={setActiveTab}
          items={[
            {
              key: "visual",
              label: "可视化配置",
              children: (
                <>
                  <div style={{ marginBottom: 24 }}>
              <Title level={4} style={{ margin: 0 }}>全局配置</Title>
              <Text style={{ color: '#8c8c8c' }}>配置Nginx的基本运行参数</Text>
            </div>

            <Row gutter={[16, 16]}>
              <Col xs={24} sm={12} lg={6}>
                <Form.Item label="运行用户">
                  <Input
                    value={config.user}
                    onChange={(e) => handleConfigUpdate({
                      ...config,
                      user: e.target.value
                    })}
                  />
                </Form.Item>
              </Col>
              <Col xs={24} sm={12} lg={6}>
                <Form.Item label="工作进程数">
                  <Input
                    value={config.worker_processes}
                    onChange={(e) => handleConfigUpdate({
                      ...config,
                      worker_processes: e.target.value
                    })}
                  />
                </Form.Item>
              </Col>
              <Col xs={24} sm={12} lg={6}>
                <Form.Item label="错误日志">
                  <Input
                    value={config.error_log}
                    onChange={(e) => handleConfigUpdate({
                      ...config,
                      error_log: e.target.value
                    })}
                  />
                </Form.Item>
              </Col>
              <Col xs={24} sm={12} lg={6}>
                <Form.Item label="PID文件">
                  <Input
                    value={config.pid}
                    onChange={(e) => handleConfigUpdate({
                      ...config,
                      pid: e.target.value
                    })}
                  />
                </Form.Item>
              </Col>
            </Row>

            <Divider />

            <div style={{ marginBottom: 24 }}>
              <Title level={4} style={{ margin: 0 }}>Events配置</Title>
              <Text style={{ color: '#8c8c8c' }}>配置事件处理模型和连接参数</Text>
            </div>

            <Row gutter={[16, 16]}>
              <Col xs={24} sm={12} lg={6}>
                <Form.Item label="事件模型">
                  <Select
                    value={config.events.use}
                    onChange={(value) => handleConfigUpdate({
                      ...config,
                      events: { ...config.events, use: value }
                    })}
                  >
                    <Option value="epoll">epoll</Option>
                    <Option value="kqueue">kqueue</Option>
                    <Option value="select">select</Option>
                    <Option value="poll">poll</Option>
                  </Select>
                </Form.Item>
              </Col>
              <Col xs={24} sm={12} lg={6}>
                <Form.Item label="工作连接数">
                  <InputNumber
                    value={config.events.worker_connections}
                    onChange={(value) => handleConfigUpdate({
                      ...config,
                      events: { ...config.events, worker_connections: value || 0 }
                    })}
                    style={{ width: '100%' }}
                    min={1}
                    max={65535}
                  />
                </Form.Item>
              </Col>
              <Col xs={24} sm={12} lg={6}>
                <Form.Item label="多连接接受">
                  <Switch
                    checked={config.events.multi_accept}
                    onChange={(checked) => handleConfigUpdate({
                      ...config,
                      events: { ...config.events, multi_accept: checked }
                    })}
                  />
                </Form.Item>
              </Col>
            </Row>

            <Divider />

            <div style={{ marginBottom: 24 }}>
              <Title level={4} style={{ margin: 0 }}>HTTP配置</Title>
              <Text style={{ color: '#8c8c8c' }}>配置HTTP模块的基本参数</Text>
            </div>

            <Row gutter={[16, 16]}>
              <Col xs={24} sm={12} lg={6}>
                <Form.Item label="客户端最大请求体">
                  <Input
                    value={config.http.client_max_body_size}
                    onChange={(e) => handleConfigUpdate({
                      ...config,
                      http: { ...config.http, client_max_body_size: e.target.value }
                    })}
                  />
                </Form.Item>
              </Col>
              <Col xs={24} sm={12} lg={6}>
                <Form.Item label="代理HTTP版本">
                  <Select
                    value={config.http.proxy_http_version}
                    onChange={(value) => handleConfigUpdate({
                      ...config,
                      http: { ...config.http, proxy_http_version: value }
                    })}
                  >
                    <Option value="1.0">1.0</Option>
                    <Option value="1.1">1.1</Option>
                  </Select>
                </Form.Item>
              </Col>
              <Col xs={24} sm={12} lg={6}>
                <Form.Item label="代理缓冲区">
                  <Input
                    value={config.http.proxy_buffers}
                    onChange={(e) => handleConfigUpdate({
                      ...config,
                      http: { ...config.http, proxy_buffers: e.target.value }
                    })}
                  />
                </Form.Item>
              </Col>
              <Col xs={24} sm={12} lg={6}>
                <Form.Item label="代理缓冲区大小">
                  <Input
                    value={config.http.proxy_buffer_size}
                    onChange={(e) => handleConfigUpdate({
                      ...config,
                      http: { ...config.http, proxy_buffer_size: e.target.value }
                    })}
                  />
                </Form.Item>
              </Col>
            </Row>

            <Row gutter={[16, 16]}>
              <Col xs={24} sm={12} lg={6}>
                <Form.Item label="连接超时">
                  <Input
                    value={config.http.proxy_connect_timeout}
                    onChange={(e) => handleConfigUpdate({
                      ...config,
                      http: { ...config.http, proxy_connect_timeout: e.target.value }
                    })}
                  />
                </Form.Item>
              </Col>
              <Col xs={24} sm={12} lg={6}>
                <Form.Item label="读取超时">
                  <Input
                    value={config.http.proxy_read_timeout}
                    onChange={(e) => handleConfigUpdate({
                      ...config,
                      http: { ...config.http, proxy_read_timeout: e.target.value }
                    })}
                  />
                </Form.Item>
              </Col>
              <Col xs={24} sm={12} lg={6}>
                <Form.Item label="发送超时">
                  <Input
                    value={config.http.proxy_send_timeout}
                    onChange={(e) => handleConfigUpdate({
                      ...config,
                      http: { ...config.http, proxy_send_timeout: e.target.value }
                    })}
                  />
                </Form.Item>
              </Col>
              <Col xs={24} sm={12} lg={6}>
                <Form.Item label="Keepalive超时">
                  <Input
                    value={config.http.keepalive_timeout}
                    onChange={(e) => handleConfigUpdate({
                      ...config,
                      http: { ...config.http, keepalive_timeout: e.target.value }
                    })}
                  />
                </Form.Item>
              </Col>
            </Row>

            <Divider />

            <div style={{ marginBottom: 24 }}>
              <Title level={4} style={{ margin: 0 }}>服务器配置</Title>
              <Text style={{ color: '#8c8c8c' }}>配置服务器监听和代理头设置</Text>
            </div>

            <Row gutter={[16, 16]}>
              <Col xs={24} sm={12} lg={6}>
                <Form.Item label="监听端口">
                  <InputNumber
                    value={config.http.server.listen}
                    onChange={(value) => handleConfigUpdate({
                      ...config,
                      http: {
                        ...config.http,
                        server: { ...config.http.server, listen: value || 8080 }
                      }
                    })}
                    style={{ width: '100%' }}
                    min={1}
                    max={65535}
                  />
                </Form.Item>
              </Col>
              <Col xs={24} sm={12} lg={6}>
                <Form.Item label="服务器名称">
                  <Input
                    value={config.http.server.server_name}
                    onChange={(e) => handleConfigUpdate({
                      ...config,
                      http: {
                        ...config.http,
                        server: { ...config.http.server, server_name: e.target.value }
                      }
                    })}
                  />
                </Form.Item>
              </Col>
            </Row>

            <div style={{ marginBottom: 16 }}>
              <Text strong>代理头设置：</Text>
            </div>

            <Row gutter={[16, 16]}>
              <Col xs={24} sm={12} lg={6}>
                <Form.Item label="Host头">
                  <Switch
                    checked={config.http.server.proxy_headers.host}
                    onChange={(checked) => handleConfigUpdate({
                      ...config,
                      http: {
                        ...config.http,
                        server: {
                          ...config.http.server,
                          proxy_headers: { ...config.http.server.proxy_headers, host: checked }
                        }
                      }
                    })}
                  />
                </Form.Item>
              </Col>
              <Col xs={24} sm={12} lg={6}>
                <Form.Item label="Real-IP头">
                  <Switch
                    checked={config.http.server.proxy_headers.real_ip}
                    onChange={(checked) => handleConfigUpdate({
                      ...config,
                      http: {
                        ...config.http,
                        server: {
                          ...config.http.server,
                          proxy_headers: { ...config.http.server.proxy_headers, real_ip: checked }
                        }
                      }
                    })}
                  />
                </Form.Item>
              </Col>
              <Col xs={24} sm={12} lg={6}>
                <Form.Item label="Forwarded-For头">
                  <Switch
                    checked={config.http.server.proxy_headers.forwarded_for}
                    onChange={(checked) => handleConfigUpdate({
                      ...config,
                      http: {
                        ...config.http,
                        server: {
                          ...config.http.server,
                          proxy_headers: { ...config.http.server.proxy_headers, forwarded_for: checked }
                        }
                      }
                    })}
                  />
                </Form.Item>
              </Col>
              <Col xs={24} sm={12} lg={6}>
                <Form.Item label="Forwarded-Proto头">
                  <Switch
                    checked={config.http.server.proxy_headers.forwarded_proto}
                    onChange={(checked) => handleConfigUpdate({
                      ...config,
                      http: {
                        ...config.http,
                        server: {
                          ...config.http.server,
                          proxy_headers: { ...config.http.server.proxy_headers, forwarded_proto: checked }
                        }
                      }
                    })}
                  />
                </Form.Item>
              </Col>
            </Row>

            <Divider />

            <div style={{ marginBottom: 24 }}>
              <Title level={4} style={{ margin: 0 }}>系统优化</Title>
              <Text style={{ color: '#8c8c8c' }}>配置系统级性能优化参数</Text>
            </div>

            <Row gutter={[16, 16]}>
              <Col xs={24} sm={12} lg={6}>
                <Form.Item label="启用Sendfile">
                  <Switch
                    checked={config.http.sendfile}
                    onChange={(checked) => handleConfigUpdate({
                      ...config,
                      http: { ...config.http, sendfile: checked }
                    })}
                  />
                </Form.Item>
              </Col>
              <Col xs={24} sm={12} lg={6}>
                <Form.Item label="启用TCP_NOPUSH">
                  <Switch
                    checked={config.http.tcp_nopush}
                    onChange={(checked) => handleConfigUpdate({
                      ...config,
                      http: { ...config.http, tcp_nopush: checked }
                    })}
                  />
                </Form.Item>
              </Col>
              <Col xs={24} sm={12} lg={6}>
                <Form.Item label="启用TCP_NODELAY">
                  <Switch
                    checked={config.http.tcp_nodelay}
                    onChange={(checked) => handleConfigUpdate({
                      ...config,
                      http: { ...config.http, tcp_nodelay: checked }
                    })}
                  />
                </Form.Item>
              </Col>
            </Row>

            <Divider />

            <div style={{ marginBottom: 24 }}>
              <Title level={4} style={{ margin: 0 }}>限流配置</Title>
              <Text style={{ color: '#8c8c8c' }}>配置请求速率限制</Text>
            </div>

            <Row gutter={[16, 16]}>
              <Col xs={24} sm={12} lg={6}>
                <Form.Item label="启用限流">
                  <Switch
                    checked={config.http.limit_req.enabled}
                    onChange={(checked) => handleConfigUpdate({
                      ...config,
                      http: {
                        ...config.http,
                        limit_req: { ...config.http.limit_req, enabled: checked }
                      }
                    })}
                  />
                </Form.Item>
              </Col>
              <Col xs={24} sm={12} lg={6}>
                <Form.Item label="限流区域">
                  <Input
                    value={config.http.limit_req.zone}
                    onChange={(e) => handleConfigUpdate({
                      ...config,
                      http: {
                        ...config.http,
                        limit_req: { ...config.http.limit_req, zone: e.target.value }
                      }
                    })}
                    disabled={!config.http.limit_req.enabled}
                  />
                </Form.Item>
              </Col>
              <Col xs={24} sm={12} lg={6}>
                <Form.Item label="限流速率">
                  <Input
                    value={config.http.limit_req.rate}
                    onChange={(e) => handleConfigUpdate({
                      ...config,
                      http: {
                        ...config.http,
                        limit_req: { ...config.http.limit_req, rate: e.target.value }
                      }
                    })}
                    disabled={!config.http.limit_req.enabled}
                  />
                </Form.Item>
              </Col>
            </Row>
                </>
              )
            },
            {
              key: "raw",
              label: "原始配置",
              children: (
                <>
                  <div style={{ marginBottom: 16 }}>
              <Title level={4} style={{ margin: 0 }}>Nginx配置文件</Title>
              <Text style={{ color: '#8c8c8c' }}>直接编辑原始配置文件</Text>
            </div>
            <Input.TextArea
              value={rawConfig}
              onChange={(e) => handleRawConfigChange(e.target.value)}
              rows={20}
              style={{ fontFamily: 'monospace', fontSize: '12px' }}
              placeholder="在此编辑Nginx配置文件..."
            />
                </>
              )
            }
          ]}
        />
      </Card>
    </div>
  );
};

export default UnifiedNginxConfig;