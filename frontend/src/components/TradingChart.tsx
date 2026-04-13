import { useEffect, useRef } from 'react'
import { createChart, CandlestickData, Time } from 'lightweight-charts'

interface TradingChartProps {
  symbol: string
  data: CandlestickData<Time>[]
  height?: number
}

export default function TradingChart({ symbol, data, height = 200 }: TradingChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!chartContainerRef.current || data.length === 0) return

    try {
      // Create chart
      const chart = createChart(chartContainerRef.current, {
        width: chartContainerRef.current.clientWidth,
        height: height,
        layout: {
          background: { color: '#0a0f1a' },
          textColor: 'rgba(255, 255, 255, 0.7)',
        },
        grid: {
          vertLines: {
            color: 'rgba(16, 185, 129, 0.1)',
            style: 1,
          },
          horzLines: {
            color: 'rgba(16, 185, 129, 0.1)',
            style: 1,
          },
        },
        crosshair: {
          mode: 1,
          vertLine: {
            color: '#10b981',
            width: 1,
            style: 2,
          },
          horzLine: {
            color: '#10b981',
            width: 1,
            style: 2,
          },
        },
        rightPriceScale: {
          borderColor: 'rgba(16, 185, 129, 0.3)',
          scaleMargins: {
            top: 0.1,
            bottom: 0.2,
          },
        },
        timeScale: {
          borderColor: 'rgba(16, 185, 129, 0.3)',
          timeVisible: true,
          secondsVisible: false,
        },
      })

      // Add candlestick series using the correct v5 API
      const series = (chart as any).addSeries('Candlestick', {
        upColor: '#10b981',
        downColor: '#ef4444',
        borderVisible: true,
        borderUpColor: '#10b981',
        borderDownColor: '#ef4444',
        wickVisible: true,
        wickUpColor: '#10b981',
        wickDownColor: '#ef4444',
      })

      series.setData(data)

      // Handle resize
      const handleResize = () => {
        if (chartContainerRef.current) {
          chart.applyOptions({
            width: chartContainerRef.current.clientWidth,
          })
        }
      }

      window.addEventListener('resize', handleResize)

      return () => {
        window.removeEventListener('resize', handleResize)
        chart.remove()
      }
    } catch (error) {
      console.error('Chart error:', error)
    }
  }, [height, data])

  return (
    <div className="w-full">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-xs font-semibold text-white/70">{symbol}</h3>
        <div className="flex gap-1">
          <div className="flex items-center gap-1">
            <div className="w-2 h-2 rounded-full bg-emerald-500" />
            <span className="text-[10px] text-white/40">Up</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-2 h-2 rounded-full bg-red-500" />
            <span className="text-[10px] text-white/40">Down</span>
          </div>
        </div>
      </div>
      <div 
        ref={chartContainerRef} 
        className="rounded-md overflow-hidden"
        style={{ height: `${height}px` }}
      />
    </div>
  )
}
