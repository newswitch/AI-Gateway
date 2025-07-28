import axios from 'axios'

// 创建axios实例
const api = axios.create({
  baseURL: '/api/v1',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer your-token-here' // 默认认证头
  }
})

// 命名空间接口
export interface Namespace {
  namespace_id: number
  namespace_code: string
  namespace_name: string
  description: string
  status: number
  create_time: string
  update_time: string
}

export interface NamespaceCreate {
  namespace_code: string
  namespace_name: string
  description: string
}

export interface NamespaceUpdate {
  namespace_name?: string
  description?: string
  status?: number
}

// 命名空间路由接口
export interface NamespaceRoute {
  route_id: number
  namespace_id: number
  matcher_type: string
  match_field: string
  match_operator: string
  match_value: string
  status: number
  create_time: string
  update_time: string
}

export interface NamespaceRouteCreate {
  namespace_id: number
  matcher_type: string
  match_field: string
  match_operator: string
  match_value: string
}

export interface NamespaceRouteUpdate {
  matcher_type?: string
  match_field?: string
  match_operator?: string
  match_value?: string
  status?: number
}

// 命名空间规则接口
export interface NamespaceRule {
  rule_id: number
  namespace_id: number
  rule_name: string
  rule_type: string
  rule_config: any
  priority: number
  status: number
  create_time: string
  update_time: string
}

export interface NamespaceRuleCreate {
  namespace_id: number
  rule_name: string
  rule_type: string
  rule_config: any
  priority: number
}

export interface NamespaceRuleUpdate {
  rule_name?: string
  rule_type?: string
  rule_config?: any
  priority?: number
  status?: number
}

// 规则类型定义
export interface RuleType {
  type: string
  name: string
  description: string
  config_schema: any
}

// 路由测试接口
export interface RouteTestRequest {
  headers?: Record<string, string>
  query_params?: Record<string, string>
  body?: any
  path?: string
}

export interface RouteTestResponse {
  matched: boolean
  namespace_id?: number
  namespace_code?: string
  namespace_name?: string
  route_id?: number
}

export interface RuleValidationRequest {
  namespace_id: number
  headers?: Record<string, string>
  query_params?: Record<string, string>
  body?: any
  path?: string
}

export interface RuleValidationResponse {
  allowed: boolean
  namespace_id: number
  namespace_code: string
  namespace_name: string
  rules: Array<{
    rule_id: number
    rule_name: string
    rule_type: string
    passed: boolean
    details?: any
  }>
}

// 命名空间API
export const namespaceAPI = {
  // 获取所有命名空间
  getAll: () => api.get<Namespace[]>('/namespaces'),
  
  // 根据ID获取命名空间
  getById: (id: number) => api.get<Namespace>(`/namespaces/${id}`),
  
  // 创建命名空间
  create: (data: NamespaceCreate) => api.post<Namespace>('/namespaces', data),
  
  // 更新命名空间
  update: (id: number, data: NamespaceUpdate) => api.put<Namespace>(`/namespaces/${id}`, data),
  
  // 删除命名空间
  delete: (id: number) => api.delete(`/namespaces/${id}`)
}

// 命名空间路由API
export const namespaceRouteAPI = {
  // 获取命名空间的路由规则
  getByNamespace: (namespaceId: number) => api.get<NamespaceRoute>(`/namespaces/${namespaceId}/route`),
  
  // 创建或更新命名空间路由规则
  createOrUpdate: (namespaceId: number, data: NamespaceRouteCreate) => 
    api.post<NamespaceRoute>(`/namespaces/${namespaceId}/route`, data),
  
  // 删除命名空间路由规则
  delete: (namespaceId: number) => api.delete(`/namespaces/${namespaceId}/route`)
}

// 命名空间规则API
export const namespaceRuleAPI = {
  // 获取命名空间的所有规则
  getByNamespace: (namespaceId: number) => api.get<NamespaceRule[]>(`/namespaces/${namespaceId}/rules`),

  // 根据ID获取规则
  getById: (ruleId: number) => api.get<NamespaceRule>(`/rules/${ruleId}`),

  // 创建规则
  create: (data: NamespaceRuleCreate) => api.post<NamespaceRule>(`/namespaces/${data.namespace_id}/rules`, data),

  // 更新规则
  update: (ruleId: number, data: NamespaceRuleUpdate) => api.put<NamespaceRule>(`/rules/${ruleId}`, data),

  // 删除规则
  delete: (ruleId: number) => api.delete(`/rules/${ruleId}`),

  // 获取规则类型
  getTypes: () => api.get<{rule_types: RuleType[]}>('/rules/types')
}

// 上游服务器管理API
export interface UpstreamServer {
  server_id: number
  server_name: string
  server_type: string
  server_url: string
  api_key?: string
  model_config?: any
  load_balance_weight: number
  max_connections: number
  timeout_connect: number
  timeout_read: number
  timeout_write: number
  health_check_url?: string
  health_check_interval: number
  status: number
  create_time: string
  update_time: string
}

export interface UpstreamServerCreate {
  server_name: string
  server_type: string
  server_url: string
  api_key?: string
  model_config?: any
  load_balance_weight?: number
  max_connections?: number
  timeout_connect?: number
  timeout_read?: number
  timeout_write?: number
  health_check_url?: string
  health_check_interval?: number
  status?: number
}

export interface UpstreamServerUpdate {
  server_name?: string
  server_type?: string
  server_url?: string
  api_key?: string
  model_config?: any
  load_balance_weight?: number
  max_connections?: number
  timeout_connect?: number
  timeout_read?: number
  timeout_write?: number
  health_check_url?: string
  health_check_interval?: number
  status?: number
}

export const upstreamServerAPI = {
  // 获取所有上游服务器
  getAll: () => api.get<UpstreamServer[]>('/upstream-servers'),

  // 根据ID获取上游服务器
  getById: (serverId: number) => api.get<UpstreamServer>(`/upstream-servers/${serverId}`),

  // 创建上游服务器
  create: (data: UpstreamServerCreate) => api.post<UpstreamServer>('/upstream-servers', data),

  // 更新上游服务器
  update: (serverId: number, data: UpstreamServerUpdate) => api.put<UpstreamServer>(`/upstream-servers/${serverId}`, data),

  // 删除上游服务器
  delete: (serverId: number) => api.delete(`/upstream-servers/${serverId}`)
}

// 代理规则管理API
export interface ProxyRule {
  rule_id: number
  rule_name: string
  rule_type: string
  match_pattern: string
  target_server_id: number
  rewrite_path?: string
  add_headers?: Record<string, string>
  priority: number
  status: number
  create_time: string
  update_time: string
}

export interface ProxyRuleCreate {
  rule_name: string
  rule_type: string
  match_pattern: string
  target_server_id: number
  rewrite_path?: string
  add_headers?: Record<string, string>
  priority?: number
  status?: number
}

export interface ProxyRuleUpdate {
  rule_name?: string
  rule_type?: string
  match_pattern?: string
  target_server_id?: number
  rewrite_path?: string
  add_headers?: Record<string, string>
  priority?: number
  status?: number
}

export const proxyRuleAPI = {
  // 获取所有代理规则
  getAll: () => api.get<ProxyRule[]>('/proxy-rules'),

  // 根据ID获取代理规则
  getById: (ruleId: number) => api.get<ProxyRule>(`/proxy-rules/${ruleId}`),

  // 创建代理规则
  create: (data: ProxyRuleCreate) => api.post<ProxyRule>('/proxy-rules', data),

  // 更新代理规则
  update: (ruleId: number, data: ProxyRuleUpdate) => api.put<ProxyRule>(`/proxy-rules/${ruleId}`, data),

  // 删除代理规则
  delete: (ruleId: number) => api.delete(`/proxy-rules/${ruleId}`)
}

// Nginx配置管理API
export interface NginxConfig {
  config_id: number
  config_type: string
  config_name: string
  config_value?: any
  description?: string
  status: number
  create_time: string
  update_time: string
}

export interface NginxConfigCreate {
  config_type: string
  config_name: string
  config_value?: any
  description?: string
  status?: number
}

export interface NginxConfigUpdate {
  config_type?: string
  config_name?: string
  config_value?: any
  description?: string
  status?: number
}

export const nginxConfigAPI = {
  // 获取所有Nginx配置
  getAll: () => api.get<NginxConfig[]>('/nginx-configs'),

  // 根据类型获取Nginx配置
  getByType: (configType: string) => api.get<NginxConfig[]>(`/nginx-configs?config_type=${configType}`),

  // 根据ID获取Nginx配置
  getById: (configId: number) => api.get<NginxConfig>(`/nginx-configs/${configId}`),

  // 创建Nginx配置
  create: (data: NginxConfigCreate) => api.post<NginxConfig>('/nginx-configs', data),

  // 更新Nginx配置
  update: (configId: number, data: NginxConfigUpdate) => api.put<NginxConfig>(`/nginx-configs/${configId}`, data),

  // 删除Nginx配置
  delete: (configId: number) => api.delete(`/nginx-configs/${configId}`)
}

// 命名空间使用情况监控API
export interface NamespaceUsage {
  namespace_id: number
  namespace_name: string
  namespace_code: string
  current_time: number
  time_window: string
  window_minutes: number
  metrics: {
    token_usage?: {
      current_usage: number
      max_limit: number
      usage_percentage: number
      window_start: number
      window_end: number
      remaining: number
    }
    qps_usage?: {
      current_usage: number
      max_limit: number
      usage_percentage: number
      window_start: number
      window_end: number
      remaining: number
    }
    concurrent_usage?: {
      current_usage: number
      max_limit: number
      usage_percentage: number
      remaining: number
    }
  }
}

export interface NamespaceUsageOverview {
  total_namespaces: number
  namespaces: Array<{
    namespace_id: number
    namespace_name: string
    namespace_code: string
    usage: NamespaceUsage
  }>
}

export interface MonitoringTimeline {
  timestamp: number
  usage: number
  time: string
}

export interface NamespaceMonitoring {
  namespace_id: number
  current_time: number
  metrics: {
    token_timeline?: MonitoringTimeline[]
    qps_timeline?: MonitoringTimeline[]
    concurrent_timeline?: MonitoringTimeline[]
  }
}

export const namespaceMonitoringAPI = {
  // 获取命名空间使用情况
  getUsage: (namespaceId: number, timeWindow: string = '30m') => 
    api.get<NamespaceUsage>(`/namespaces/${namespaceId}/usage?time_window=${timeWindow}`),

  // 获取所有命名空间使用情况概览
  getUsageOverview: () => api.get<NamespaceUsageOverview>('/namespaces/usage/overview'),

  // 获取命名空间实时监控数据
  getMonitoring: (namespaceId: number, metricType: string = 'all') => 
    api.get<NamespaceMonitoring>(`/namespaces/${namespaceId}/monitoring?metric_type=${metricType}`)
}

// 路由测试API
export const routeAPI = {
  // 路由到命名空间
  routeToNamespace: (requestData: RouteTestRequest) => 
    api.post<RouteTestResponse>('/route/namespace', requestData),
  
  // 验证命名空间规则
  validateNamespaceRules: (namespaceId: number, requestData: RuleValidationRequest) => 
    api.post<RuleValidationResponse>(`/namespaces/${namespaceId}/validate`, requestData)
} 