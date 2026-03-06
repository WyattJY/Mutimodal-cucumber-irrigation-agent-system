// Export Utilities - CSV/JSON 数据导出工具
import dayjs from 'dayjs'

export interface ExportOptions {
  filename?: string
  includeTimestamp?: boolean
}

/**
 * 导出为 CSV 文件
 */
export function exportToCSV<T extends Record<string, unknown>>(
  data: T[],
  options: ExportOptions = {}
): void {
  if (!data.length) {
    console.warn('No data to export')
    return
  }

  const { filename = 'export', includeTimestamp = true } = options

  // 获取表头
  const headers = Object.keys(data[0])

  // 转换数据为 CSV 行
  const csvRows: string[] = []

  // 添加 BOM 以支持 Excel 正确识别中文
  csvRows.push(headers.join(','))

  for (const row of data) {
    const values = headers.map((header) => {
      const value = row[header]
      // 处理特殊字符
      if (value === null || value === undefined) {
        return ''
      }
      const stringValue = String(value)
      // 如果包含逗号、引号或换行符，用引号包裹
      if (stringValue.includes(',') || stringValue.includes('"') || stringValue.includes('\n')) {
        return `"${stringValue.replace(/"/g, '""')}"`
      }
      return stringValue
    })
    csvRows.push(values.join(','))
  }

  const csvContent = '\uFEFF' + csvRows.join('\n')
  const timestamp = includeTimestamp ? `_${dayjs().format('YYYYMMDD_HHmmss')}` : ''

  downloadFile(csvContent, `${filename}${timestamp}.csv`, 'text/csv;charset=utf-8;')
}

/**
 * 导出为 JSON 文件
 */
export function exportToJSON<T>(
  data: T,
  options: ExportOptions = {}
): void {
  const { filename = 'export', includeTimestamp = true } = options

  const jsonContent = JSON.stringify(data, null, 2)
  const timestamp = includeTimestamp ? `_${dayjs().format('YYYYMMDD_HHmmss')}` : ''

  downloadFile(jsonContent, `${filename}${timestamp}.json`, 'application/json')
}

/**
 * 通用文件下载函数
 */
function downloadFile(content: string, filename: string, mimeType: string): void {
  const blob = new Blob([content], { type: mimeType })
  const url = URL.createObjectURL(blob)

  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()

  // 清理
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

/**
 * Episode 数据转换为导出格式
 */
export interface EpisodeExportRow {
  日期: string
  灌水量: number
  来源: string
  长势趋势: string
  置信度: string
  风险等级: string
  覆盖理由: string
}

export function formatEpisodesForExport(episodes: any[]): EpisodeExportRow[] {
  return episodes.map((ep) => ({
    日期: ep.date,
    灌水量: ep.irrigation_amount || 0,
    来源: ep.source === 'override' ? '人工覆盖' : 'TSMixer',
    长势趋势: formatTrend(ep.response?.trend),
    置信度: ep.response?.confidence ? `${Math.round(ep.response.confidence * 100)}%` : '-',
    风险等级: formatRiskLevel(ep.sanity?.risk_level),
    覆盖理由: ep.override?.reason || '-',
  }))
}

function formatTrend(trend?: string): string {
  const trendMap: Record<string, string> = {
    better: '向好',
    same: '稳定',
    worse: '下降',
  }
  return trendMap[trend || ''] || '-'
}

function formatRiskLevel(level?: string): string {
  const levelMap: Record<string, string> = {
    low: '低',
    medium: '中',
    high: '高',
    critical: '严重',
  }
  return levelMap[level || ''] || '-'
}
