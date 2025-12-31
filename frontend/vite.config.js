import {defineConfig} from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
    plugins: [react()],
    server: {
        proxy: {
            '/products': 'http://backend:5000',
            '/cart': 'http://backend:5000',
            '/checkout': 'http://backend:5000',
            '/auth': 'http://backend:5000',
            '/orders': 'http://backend:5000', 
            '/payment': 'http://backend:5000'
        }
    }
})