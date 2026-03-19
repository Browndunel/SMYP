FROM node:20-alpine
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm install --omit=dev
COPY . .
EXPOSE ${API_PORT}
CMD ["node", "index.js"]