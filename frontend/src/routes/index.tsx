import { createBrowserRouter, Navigate } from 'react-router-dom'
import { Layout } from '@/components/layout'

// Pages
import Dashboard from '@/pages/Dashboard'
import DailyDecision from '@/pages/DailyDecision'
import History from '@/pages/History'
import Knowledge from '@/pages/Knowledge'
import PlantResponse from '@/pages/PlantResponse'
import Settings from '@/pages/Settings'
import Vision from '@/pages/Vision'
import Predict from '@/pages/Predict'
import NotFound from '@/pages/NotFound'

export const router = createBrowserRouter([
  {
    path: '/',
    element: <Layout />,
    children: [
      {
        index: true,
        element: <Dashboard />,
      },
      {
        path: 'daily/:date',
        element: <DailyDecision />,
      },
      {
        path: 'history',
        element: <History />,
      },
      {
        // Redirect old weekly route to history
        path: 'weekly',
        element: <Navigate to="/history" replace />,
      },
      {
        path: 'knowledge',
        element: <Knowledge />,
      },
      {
        path: 'plant-response/:date',
        element: <PlantResponse />,
      },
      {
        path: 'vision',
        element: <Vision />,
      },
      {
        path: 'predict',
        element: <Predict />,
      },
      {
        path: 'settings',
        element: <Settings />,
      },
      {
        path: '404',
        element: <NotFound />,
      },
      {
        path: '*',
        element: <Navigate to="/404" replace />,
      },
    ],
  },
])

export default router
