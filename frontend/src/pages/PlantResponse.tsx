import { useParams } from 'react-router-dom'

export function PlantResponse() {
  const { date } = useParams<{ date: string }>()

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-white mb-2">长势图像对比</h1>
        <p className="text-slate-400">可视化长势评估依据 - {date}</p>
      </div>

      <div className="glass-panel p-6">
        <div className="text-center py-12 text-slate-500">
          <i className="ph-bold ph-images-square text-4xl mb-2" />
          <p>Image comparison coming in Phase 3...</p>
        </div>
      </div>
    </div>
  )
}

export default PlantResponse
