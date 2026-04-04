import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import QueryPage from './pages/QueryPage'
import UploadPage from './pages/UploadPage'
import EvalPage from './pages/EvalPage'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<QueryPage />} />
          <Route path="/upload" element={<UploadPage />} />
          <Route path="/eval" element={<EvalPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
