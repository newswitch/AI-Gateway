/**
 * API服务调用封装
 * 统一管理所有后端API接口调用
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001';

// 通用响应类型
interface ApiResponse<T = any> {
  code: number;
  message: string;
  data: T;
  timestamp: string;
}

// 分页响应类型
export interface PaginatedResponse<T = any> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

// 请求配置
interface RequestConfig {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE';
  headers?: Record<string, string>;
  body?: any;
}

// 通用请求函数
async function request<T = any>(
  endpoint: string,
  config: RequestConfig = {}
): Promise<ApiResponse<T>> {
  const { method = 'GET', headers = {}, body } = config;
  
  const url = `${API_BASE_URL}${endpoint}`;
  const requestHeaders: Record<string, string> = {
    'Content-Type': 'application/json',
    ...headers,
  };

  // 添加认证token - 使用有效的token
  const token = localStorage.getItem('token') || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiYWRtaW4iLCJ1c2VybmFtZSI6ImFkbWluIiwiaWF0IjoxNzA1MzEyMjAwfQ.example';
  requestHeaders.Authorization = `Bearer ${token}`;

  console.log('[API] 请求开始:', { 
    url, 
    method, 
    headers: requestHeaders, 
    body,
    API_BASE_URL 
  });
  
  try {
    const response = await fetch(url, {
      method,
      headers: requestHeaders,
      body: body ? JSON.stringify(body) : undefined,
    });

    console.log('[API] 响应状态:', { 
      status: response.status, 
      statusText: response.statusText, 
      url,
      ok: response.ok 
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('[API] 错误响应:', {
        status: response.status,
        statusText: response.statusText,
        url,
        errorText
      });
      throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
    }

    const result = await response.json();
    console.log('[API] 成功响应:', result);
    return result;
  } catch (error) {
    console.error('[API] 请求异常:', {
      url,
      method,
      error: error instanceof Error ? error.message : String(error),
      stack: error instanceof Error ? error.stack : undefined
    });
    throw error;
  }
}

// 仪表盘API
export const dashboardApi = {
  // 获取核心指标
  getMetrics: () => request('/api/dashboard/metrics'),
  
  // 获取命名空间统计
  getNamespaces: () => request('/api/dashboard/namespaces'),
  
  // 获取实时监控数据
  getRealtime: (timeRange: string = '15m', granularity: string = 'minute', namespace?: string) => 
    request(`/api/dashboard/realtime?timeRange=${timeRange}&granularity=${granularity}${namespace ? `&namespace=${namespace}` : ''}`),
  
  // 获取系统健康状态
  getHealth: () => request('/api/dashboard/health'),
};

// 命名空间管理API
export const namespaceApi = {
  // 获取命名空间列表
  getNamespaces: (page: number = 1, size: number = 10, owner?: string, status?: string, keyword?: string) => {
    const params = new URLSearchParams({
      page: page.toString(),
      size: size.toString(),
    });
    if (owner) params.append('owner', owner);
    if (status) params.append('status', status);
    if (keyword) params.append('keyword', keyword);
    return request(`/api/namespaces?${params.toString()}`);
  },
  
  // 获取单个命名空间
  getNamespace: (namespaceId: string) => request(`/api/namespaces/${namespaceId}`),
  
  // 创建命名空间
  createNamespace: (data: any) => request('/api/namespaces', { method: 'POST', body: data }),
  
  // 更新命名空间
  updateNamespace: (namespaceId: string, data: any) => 
    request(`/api/namespaces/${namespaceId}`, { method: 'PUT', body: data }),
  
  // 删除命名空间
  deleteNamespace: (namespaceId: string) => 
    request(`/api/namespaces/${namespaceId}`, { method: 'DELETE' }),
  
  // 更新命名空间状态
  updateNamespaceStatus: (namespaceId: string, status: string) => 
    request(`/api/namespaces/${namespaceId}/status`, { method: 'PUT', body: { status } }),
  
  // 获取命名空间统计
  getNamespaceStats: (namespaceId: string) => request(`/api/namespaces/${namespaceId}/stats`),

  // 获取命名空间状态分布数据
  getNamespaceStatusDistribution: (timeRange: string = 'all') => {
    const params = new URLSearchParams({ timeRange });
    return request(`/api/namespaces/status-distribution?${params.toString()}`);
  },

  // 获取命名空间请求趋势数据
  getNamespaceRequestTrend: (timeRange: string = 'today') => {
    const params = new URLSearchParams({ timeRange });
    return request(`/api/namespaces/request-trend?${params.toString()}`);
  },
};

// 匹配器管理API
export const matcherApi = {
  // 获取命名空间下的匹配器
  getMatchers: (namespaceId: string) => request(`/api/v1/namespaces/${namespaceId}/matchers`),
  
  // 创建匹配器
  createMatcher: (namespaceId: string, data: any) => 
    request(`/api/v1/namespaces/${namespaceId}/matchers`, { method: 'POST', body: data }),
  
  // 更新匹配器
  updateMatcher: (matcherId: string, data: any) => 
    request(`/api/v1/matchers/${matcherId}`, { method: 'PUT', body: data }),
  
  // 删除匹配器
  deleteMatcher: (matcherId: string) => 
    request(`/api/v1/matchers/${matcherId}`, { method: 'DELETE' }),
  
  // 获取所有匹配器
  getAllMatchers: () => request('/api/v1/matchers'),
};

// 规则管理API
export const ruleApi = {
  // 获取命名空间下的规则
  getRules: (namespaceId: string, ruleType?: string) => {
    const params = new URLSearchParams();
    if (ruleType) params.append('rule_type', ruleType);
    return request(`/api/v1/namespaces/${namespaceId}/rules?${params.toString()}`);
  },
  
  // 创建规则
  createRule: (namespaceId: string, data: any) => 
    request(`/api/v1/namespaces/${namespaceId}/rules`, { method: 'POST', body: data }),
  
  // 更新规则
  updateRule: (ruleId: string, data: any) => 
    request(`/api/v1/rules/${ruleId}`, { method: 'PUT', body: data }),
  
  // 删除规则
  deleteRule: (ruleId: string) => 
    request(`/api/v1/rules/${ruleId}`, { method: 'DELETE' }),
  
  // 获取规则类型
  getRuleTypes: () => request('/api/v1/rules/types'),
  
  // 获取所有规则
  getAllRules: (ruleType?: string) => {
    const params = new URLSearchParams();
    if (ruleType) params.append('rule_type', ruleType);
    return request(`/api/v1/rules?${params.toString()}`);
  },
};

// 策略配置API
export const policyApi = {
  // 获取策略列表
  getPolicies: (page: number = 1, size: number = 10, keyword?: string, policyType?: string, status?: string) => {
    const params = new URLSearchParams({
      page: page.toString(),
      size: size.toString(),
    });
    if (keyword) params.append('keyword', keyword);
    if (policyType) params.append('policy_type', policyType);
    if (status) params.append('status', status);
    return request(`/api/policies?${params.toString()}`);
  },
  
  // 获取单个策略
  getPolicy: (policyId: string) => request(`/api/policies/${policyId}`),
  
  // 创建策略
  createPolicy: (data: any) => request('/api/policies', { method: 'POST', body: data }),
  
  // 更新策略
  updatePolicy: (policyId: string, data: any) => 
    request(`/api/policies/${policyId}`, { method: 'PUT', body: data }),
  
  // 删除策略
  deletePolicy: (policyId: string) => 
    request(`/api/policies/${policyId}`, { method: 'DELETE' }),
  
  // 更新策略状态
  updatePolicyStatus: (policyId: string, status: string) => 
    request(`/api/policies/${policyId}/status`, { method: 'PUT', body: { status } }),
  
  // 获取策略模板
  getPolicyTemplates: () => request('/api/policy-templates'),
  
  // 获取策略统计
  getPolicyStats: () => request('/api/policies/stats'),
};

// 流量监控API
export const trafficApi = {
  // 获取流量指标
  getMetrics: (timeRange: string = '1h', granularity: string = 'minute', filters?: any) => {
    const params = new URLSearchParams({
      timeRange,
      granularity,
    });
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value) params.append(key, value as string);
      });
    }
    return request(`/api/traffic/metrics?${params.toString()}`);
  },
  
  // 获取流量趋势
  getTrends: (timeRange: string = '1h', granularity: string = 'minute', filters?: any) => {
    const params = new URLSearchParams({
      timeRange,
      granularity,
    });
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value) params.append(key, value as string);
      });
    }
    return request(`/api/traffic/trends?${params.toString()}`);
  },
  
  // 获取系统告警
  getAlerts: (page: number = 1, size: number = 10, level?: string, status?: string) => {
    const params = new URLSearchParams({
      page: page.toString(),
      size: size.toString(),
    });
    if (level) params.append('level', level);
    if (status) params.append('status', status);
    return request(`/api/traffic/alerts?${params.toString()}`);
  },
  
  // 获取监控筛选选项
  getFilters: () => request('/api/traffic/filters'),
  
  // 确认告警
  acknowledgeAlert: (alertId: string) => 
    request(`/api/traffic/alerts/${alertId}/acknowledge`, { method: 'POST' }),
  
  // 解决告警
  resolveAlert: (alertId: string) => 
    request(`/api/traffic/alerts/${alertId}/resolve`, { method: 'POST' }),
  
  // 获取流量统计
  getStats: () => request('/api/traffic/stats'),
};

// 访问日志API
export const logsApi = {
  // 获取访问日志
  getLogs: (page: number = 1, size: number = 10, filters?: any) => {
    const params = new URLSearchParams({
      page: page.toString(),
      size: size.toString(),
    });
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value) params.append(key, value as string);
      });
    }
    return request(`/api/logs?${params.toString()}`);
  },
  
  // 获取日志统计
  getLogStats: (startTime?: string, endTime?: string) => {
    const params = new URLSearchParams();
    if (startTime) params.append('startTime', startTime);
    if (endTime) params.append('endTime', endTime);
    return request(`/api/logs/stats?${params.toString()}`);
  },
  
  // 导出日志
  exportLogs: (filters?: any, format: string = 'json') => {
    const params = new URLSearchParams({ format });
    if (filters) {
      Object.entries(filters).forEach(([key, value]) => {
        if (value) params.append(key, value as string);
      });
    }
    return request(`/api/logs/export?${params.toString()}`);
  },
  
  // 获取日志筛选选项
  getLogFilters: () => request('/api/logs/filters'),
  
  // 获取单个日志详情
  getLogDetail: (logId: string) => request(`/api/logs/${logId}`),
  
  // 清理日志
  clearLogs: (filters?: any) => 
    request('/api/logs', { method: 'DELETE', body: filters }),
};

// 统一配置API
export const configApi = {
  // 获取Nginx配置
  getNginxConfig: () => request('/api/config/nginx'),
  
  // 更新Nginx配置
  updateNginxConfig: (data: any) => 
    request('/api/config/nginx', { method: 'PUT', body: data }),
  
  // 验证配置
  validateConfig: (data: any) => 
    request('/api/config/validate', { method: 'POST', body: data }),
  
  // 部署配置
  deployConfig: () => request('/api/config/deploy', { method: 'POST' }),
  
  // 获取配置历史
  getConfigHistory: (page: number = 1, size: number = 10) => 
    request(`/api/config/history?page=${page}&size=${size}`),
  
  // 回滚配置
  rollbackConfig: (versionId: string) => 
    request(`/api/config/rollback/${versionId}`, { method: 'POST' }),
  
  // 获取配置状态
  getConfigStatus: () => request('/api/config/status'),
  
  // 获取配置模板
  getConfigTemplates: () => request('/api/config/templates'),
  
  // 导入配置
  importConfig: (configFile: string) => 
    request('/api/config/import', { method: 'POST', body: { config_file: configFile } }),
  
  // 导出配置
  exportConfig: (format: string = 'json') => 
    request(`/api/config/export?format=${format}`),
};

// 认证API
export const authApi = {
  // 用户登录
  login: (username: string, password: string) => 
    request('/api/auth/login', { method: 'POST', body: { username, password } }),
  
  // 用户登出
  logout: () => request('/api/auth/logout', { method: 'POST' }),
  
  // 获取用户信息
  getProfile: () => request('/api/auth/profile'),
  
  // 更新用户信息
  updateProfile: (data: any) => 
    request('/api/auth/profile', { method: 'PUT', body: data }),
  
  // 获取API密钥列表
  getApiKeys: (page: number = 1, size: number = 10, keyword?: string, status?: string) => {
    const params = new URLSearchParams({
      page: page.toString(),
      size: size.toString(),
    });
    if (keyword) params.append('keyword', keyword);
    if (status) params.append('status', status);
    return request(`/api/auth/keys?${params.toString()}`);
  },
  
  // 创建API密钥
  createApiKey: (data: any) => 
    request('/api/auth/keys', { method: 'POST', body: data }),
  
  // 更新API密钥
  updateApiKey: (keyId: string, data: any) => 
    request(`/api/auth/keys/${keyId}`, { method: 'PUT', body: data }),
  
  // 删除API密钥
  deleteApiKey: (keyId: string) => 
    request(`/api/auth/keys/${keyId}`, { method: 'DELETE' }),
  
  // 更新API密钥状态
  updateApiKeyStatus: (keyId: string, status: string) => 
    request(`/api/auth/keys/${keyId}/status`, { method: 'PUT', body: { status } }),
  
  // 获取API密钥使用情况
  getApiKeyUsage: (keyId: string, startTime?: string, endTime?: string) => {
    const params = new URLSearchParams();
    if (startTime) params.append('startTime', startTime);
    if (endTime) params.append('endTime', endTime);
    return request(`/api/auth/keys/${keyId}/usage?${params.toString()}`);
  },
  
  // 获取权限列表
  getPermissions: () => request('/api/auth/permissions'),
  
  // 修改密码
  changePassword: (data: any) => 
    request('/api/auth/change-password', { method: 'POST', body: data }),
};

// 上游服务器API
export const upstreamApi = {
  // 获取上游服务器列表
  getUpstreams: (page: number = 1, size: number = 10, keyword?: string) => {
    const params = new URLSearchParams({
      page: page.toString(),
      size: size.toString(),
    });
    if (keyword) params.append('keyword', keyword);
    return request(`/api/upstreams?${params.toString()}`);
  },
  
  // 获取单个上游服务器
  getUpstream: (serverId: string) => request(`/api/upstreams/${serverId}`),
  
  // 创建上游服务器
  createUpstream: (data: any) => 
    request('/api/upstreams', { method: 'POST', body: data }),
  
  // 更新上游服务器
  updateUpstream: (serverId: string, data: any) => 
    request(`/api/upstreams/${serverId}`, { method: 'PUT', body: data }),
  
  // 删除上游服务器
  deleteUpstream: (serverId: string) => 
    request(`/api/upstreams/${serverId}`, { method: 'DELETE' }),
  
  // 更新上游服务器状态
  updateUpstreamStatus: (serverId: string, status: string) => 
    request(`/api/upstreams/${serverId}/status`, { method: 'PUT', body: { status } }),
};

// 路由规则API
export const locationApi = {
  // 获取路由规则列表
  getLocations: (page: number = 1, size: number = 10, keyword?: string) => {
    const params = new URLSearchParams({
      page: page.toString(),
      size: size.toString(),
    });
    if (keyword) params.append('keyword', keyword);
    return request(`/api/locations?${params.toString()}`);
  },
  
  // 获取单个路由规则
  getLocation: (locationId: string) => request(`/api/locations/${locationId}`),
  
  // 创建路由规则
  createLocation: (data: any) => 
    request('/api/locations', { method: 'POST', body: data }),
  
  // 更新路由规则
  updateLocation: (locationId: string, data: any) => 
    request(`/api/locations/${locationId}`, { method: 'PUT', body: data }),
  
  // 删除路由规则
  deleteLocation: (locationId: string) => 
    request(`/api/locations/${locationId}`, { method: 'DELETE' }),
  
  // 更新路由规则状态
  updateLocationStatus: (locationId: string, status: string) => 
    request(`/api/locations/${locationId}/status`, { method: 'PUT', body: { status } }),
};

export default {
  dashboard: dashboardApi,
  namespace: namespaceApi,
  policy: policyApi,
  traffic: trafficApi,
  logs: logsApi,
  config: configApi,
  auth: authApi,
  upstream: upstreamApi,
  location: locationApi,
};
