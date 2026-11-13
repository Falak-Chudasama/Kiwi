import { Suspense, lazy } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { ToastProvider } from './components/ui/ToastProvider'
import { ThemeProvider } from './components/ui/ThemeProvider'
import { Header } from './components/layout/Header'

const HomePage = lazy(() => import('./pages/HomePage'))
const DocumentConvertPage = lazy(() => import('./pages/DocumentConvertPage'))
const ImageConvertPage = lazy(() => import('./pages/ImageConvertPage'))
const PdfToolsPage = lazy(() => import('./pages/PdfToolsPage'))
const CompressPage = lazy(() => import('./pages/CompressPage'))
const ArchivesPage = lazy(() => import('./pages/ArchivesPage'))
const ScannerPage = lazy(() => import('./pages/ScannerPage'))
const NotFoundPage = lazy(() => import('./pages/NotFoundPage'))

function LoadingFallback() {
  return (
    <div className="flex min-h-[40vh] items-center justify-center">
      <div className="h-5 w-5 animate-spin rounded-full border-2 border-stone-300 dark:border-stone-700 border-t-kiwi-flesh dark:border-t-kiwi-lime" />
    </div>
  )
}

export default function App() {
  return (
    <ThemeProvider>
      <ToastProvider>
        <BrowserRouter>
          <div className="min-h-screen bg-[#F8F9F5] dark:bg-[#121310] text-stone-900 dark:text-stone-100 font-sans transition-colors duration-200">
            <Header />
            <Suspense fallback={<LoadingFallback />}>
              <Routes>
                <Route path="/" element={<HomePage />} />
                <Route path="/convert" element={<DocumentConvertPage />} />
                <Route path="/documents" element={<DocumentConvertPage />} />
                <Route path="/images" element={<ImageConvertPage />} />
                <Route path="/pdf" element={<PdfToolsPage />} />
                <Route path="/compress" element={<CompressPage />} />
                <Route path="/archives" element={<ArchivesPage />} />
                <Route path="/scan" element={<ScannerPage />} />
                <Route path="/scanner" element={<ScannerPage />} />
                <Route path="*" element={<NotFoundPage />} />
              </Routes>
            </Suspense>
          </div>
        </BrowserRouter>
      </ToastProvider>
    </ThemeProvider>
  )
}
