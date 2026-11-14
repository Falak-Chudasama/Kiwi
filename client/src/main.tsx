import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'

// Transparently handle any stale chunk reload after builds
window.addEventListener('vite:preloadError', (event) => {
  event.preventDefault()
  window.location.reload()
})

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
