// 时间范围选项
export type TimeRange = '15m' | '1h' | '24h' | '7d' | 'custom';

// 统计粒度
export type Granularity = 'minute' | '5minute' | 'hour' | 'day';

// 命名空间
export interface Namespace {
  name: string;
  requestCount: number;
  inputTokens: number;
  outputTokens: number;
  avgInputTokensPerReq: number;
  avgOutputTokensPerReq: number;
  percentage: string;
  changeRate: string;
  changeDirection: 'up' | 'down';
  lastActive: string;
}

// 时间桶数据
export interface TimeBucketData {
  time: string;
  requestCount: number;
  successCount: number;
  failCount: number;
  inputTokens: number;
  outputTokens: number;
  avgResponseTime: number;
}

// 系统健康状态
export interface HealthStatus {
  name: string;
  status: 'normal' | 'warning' | 'error';
  message: string;
}

// 趋势图数据
export interface TrendData {
  timestamps: string[];
  requestCounts: number[];
  inputTokens: number[];
  outputTokens: number[];
}

// 核心指标
export interface CoreMetrics {
  totalRequests: number;
  successRate: string;
  growthRate: string;
  inputTokens: number;
  outputTokens: number;
  avgInputTokens: number;
  avgOutputTokens: number;
  peakQPS: number;
  currentQPS: number;
}