FROM node:20-slim

WORKDIR /app

COPY package.json ./
RUN npm install

COPY . .

EXPOSE 5173
# Dev-сервер Vite с прокси на backend (раздел 2.5.1).
CMD ["npm", "run", "dev", "--", "--host"]
