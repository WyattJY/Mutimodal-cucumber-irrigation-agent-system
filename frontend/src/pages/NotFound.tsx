import { Link } from 'react-router-dom'

export function NotFound() {
  return (
    <div className="min-h-[60vh] flex items-center justify-center">
      <div className="text-center">
        <div className="text-9xl font-bold gradient-text mb-4">404</div>
        <h1 className="text-2xl font-bold text-white mb-2">页面未找到</h1>
        <p className="text-slate-400 mb-8">您访问的页面不存在或已被移除</p>
        <Link to="/" className="btn-primary px-8 py-3">
          <i className="ph-bold ph-house" />
          返回首页
        </Link>
      </div>
    </div>
  )
}

export default NotFound
