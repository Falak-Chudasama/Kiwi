import { describe, it, expect } from 'vitest'
import { renderToStaticMarkup } from 'react-dom/server'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import ArchivesPage from '../pages/ArchivesPage'
import DocumentConvertPage from '../pages/DocumentConvertPage'
import { DirectionalPageTransition } from '../components/layout/DirectionalPageTransition'
import { ToastProvider } from '../components/ui/ToastProvider'
import { ThemeProvider } from '../components/ui/ThemeProvider'

describe('DirectionalPageTransition with Archives', () => {
  it('renders archives within DirectionalPageTransition', () => {
    const markup = renderToStaticMarkup(
      <MemoryRouter initialEntries={['/archives']}>
        <ThemeProvider>
          <ToastProvider>
            <DirectionalPageTransition>
              <Routes>
                <Route path="/convert" element={<DocumentConvertPage />} />
                <Route path="/archives" element={<ArchivesPage />} />
              </Routes>
            </DirectionalPageTransition>
          </ToastProvider>
        </ThemeProvider>
      </MemoryRouter>
    )

    expect(markup).toContain('Archive Workspace')
  })
})
