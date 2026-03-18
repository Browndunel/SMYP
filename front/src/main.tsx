import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App' // Il va chercher le composant dans App.tsx
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
    <React.StrictMode>
        <App />
    </React.StrictMode>
)