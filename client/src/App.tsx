import { Suspense } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { ToastProvider } from './components/ui/ToastProvider'
import { ThemeProvider } from './components/ui/ThemeProvider'
import { Header } from './components/layout/Header'
import { DirectionalPageTransition } from './components/layout/DirectionalPageTransition'
import { ErrorBoundary } from './components/ui/ErrorBoundary'

import HomePage from './pages/HomePage'
import DocumentConvertPage from './pages/DocumentConvertPage'
import ImageConvertPage from './pages/ImageConvertPage'
import PdfToolsPage from './pages/PdfToolsPage'
import CompressPage from './pages/CompressPage'
import ArchivesPage from './pages/ArchivesPage'
import ScannerPage from './pages/ScannerPage'
import NotFoundPage from './pages/NotFoundPage'

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
          <div className="relative min-h-screen bg-[#F8F9F5] dark:bg-[#121310] text-stone-900 dark:text-stone-100 font-sans transition-colors duration-200 overflow-x-hidden">
            {/* Ambient light fields to enable subtle glass refraction */}
            <div className="pointer-events-none fixed top-12 -left-32 h-[500px] w-[500px] rounded-full bg-gradient-to-br from-kiwi-flesh/[0.05] to-transparent blur-[110px] dark:from-kiwi-lime/[0.06]" />
            <div className="pointer-events-none fixed top-1/3 -right-32 h-[480px] w-[480px] rounded-full bg-gradient-to-bl from-kiwi-lime/[0.05] to-transparent blur-[110px] dark:from-kiwi-flesh/[0.05]" />
            <div className="pointer-events-none fixed -bottom-32 left-1/4 h-[500px] w-[500px] rounded-full bg-gradient-to-tr from-emerald-500/[0.04] to-transparent blur-[120px] dark:from-emerald-400/[0.04]" />

            <div className="relative z-10 pt-16 sm:pt-20">
              <Header />
              <ErrorBoundary>
                <Suspense fallback={<LoadingFallback />}>
                  <DirectionalPageTransition>
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
                  </DirectionalPageTransition>
                </Suspense>
              </ErrorBoundary>
            </div>
          </div>
        </BrowserRouter>
      </ToastProvider>
    </ThemeProvider>
  )
}
