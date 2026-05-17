import { useNavigate } from 'react-router-dom'

export default function NotFound() {
  const navigate = useNavigate()
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-6xl font-bold text-blue-600">404</h1>
        <p className="text-gray-500 mt-4 text-lg">Sahifa topilmadi</p>
        <button
          onClick={() => navigate('/login')}
          className="mt-6 px-6 py-2.5 bg-blue-600 text-white rounded-xl
                     hover:bg-blue-700 transition text-sm font-medium"
        >
          Bosh sahifaga qaytish
        </button>
      </div>
    </div>
  )
}
