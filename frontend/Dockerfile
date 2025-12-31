FROM node:20-slim

WORKDIR /app
COPY . .
RUN npm install && npm run build

CMD ["npx", "vite", "preview", "--host"]
