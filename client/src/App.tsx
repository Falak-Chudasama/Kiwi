import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { ToastProvider } from './components/ui/ToastProvider'
import { Header } from './components/layout/Header'
import HomePage from './pages/HomePage'
import DocumentConvertPage from './pages/DocumentConvertPage'
import ImageConvertPage from './pages/ImageConvertPage'
import PdfToolsPage from './pages/PdfToolsPage'
import CompressPage from './pages/CompressPage'
import ArchivesPage from './pages/ArchivesPage'
import EnginesPage from './pages/EnginesPage'

export default function App() {
  return (
    <ToastProvider>
      <BrowserRouter>
        <div className="min-h-screen bg-[#FAF8ED]">
          <Header />
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/convert" element={<DocumentConvertPage />} />
            <Route path="/documents" element={<DocumentConvertPage />} />
            <Route path="/images" element={<ImageConvertPage />} />
            <Route path="/pdf" element={<PdfToolsPage />} />
            <Route path="/compress" element={<CompressPage />} />
            <Route path="/archives" element={<ArchivesPage />} />
            <Route path="/engines" element={<EnginesPage />} />
          </Routes>
        </div>
      </BrowserRouter>
    </ToastProvider>
  )
}
