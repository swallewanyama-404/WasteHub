FROM node:20-alpine AS build

WORKDIR /app

COPY frontend/package.json ./package.json
COPY frontend/tsconfig.json ./tsconfig.json
COPY frontend/tsconfig.app.json ./tsconfig.app.json
COPY frontend/tsconfig.node.json ./tsconfig.node.json
COPY frontend/vite.config.ts ./vite.config.ts

RUN npm install

COPY frontend/index.html ./index.html
COPY frontend/src ./src

ARG VITE_API_BASE_URL=/api/v1
ARG VITE_DEMO_MODE=true
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
ENV VITE_DEMO_MODE=$VITE_DEMO_MODE

RUN npm run build


FROM nginx:1.27-alpine

COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
