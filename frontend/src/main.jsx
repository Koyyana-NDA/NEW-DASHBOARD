import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'      // matches App.jsx exactly
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)
