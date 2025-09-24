import type { TrendData } from '../types';

// 默认 API 基础 URL
const DEFAULT_API_BASE_URL = 'http://localhost:3000';

/**
 * 建立SSE连接，实时获取趋势数据
 * @param callback 数据更新回调函数
 * @param timeRange 时间范围
 * @param granularity 统计粒度
 * @returns 关闭连接的函数
 */
export const connectTrendSSE = (
  callback: (data: TrendData) => void,
  timeRange: string = '15m',
  granularity: string = 'minute'
) => {
  const baseUrl = import.meta.env.VITE_API_BASE_URL || DEFAULT_API_BASE_URL;
  const url = new URL('/api/trends/sse', baseUrl);
  url.searchParams.append('range', timeRange);
  url.searchParams.append('granularity', granularity);
  
  const eventSource = new EventSource(url.toString());
  
  eventSource.addEventListener('message', (event) => {
    try {
      const data = JSON.parse(event.data) as TrendData;
      callback(data);
    } catch (error) {
      console.error('Failed to parse SSE data:', error);
    }
  });
  
  eventSource.addEventListener('error', (error) => {
    console.error('SSE connection error:', error);
    eventSource.close();
  });
  
  return () => {
    eventSource.close();
  };
};

/**
 * 建立SSE连接，实时获取核心指标
 * @param callback 数据更新回调函数
 * @returns 关闭连接的函数
 */
export const connectMetricsSSE = (
  callback: (data: any) => void
) => {
  const baseUrl = import.meta.env.VITE_API_BASE_URL || DEFAULT_API_BASE_URL;
  const url = new URL('/api/metrics/sse', baseUrl);
  
  const eventSource = new EventSource(url.toString());
  
  eventSource.addEventListener('message', (event) => {
    try {
      const data = JSON.parse(event.data);
      callback(data);
    } catch (error) {
      console.error('Failed to parse metrics SSE data:', error);
    }
  });
  
  eventSource.addEventListener('error', (error) => {
    console.error('Metrics SSE connection error:', error);
    eventSource.close();
  });
  
  return () => {
    eventSource.close();
  };
};