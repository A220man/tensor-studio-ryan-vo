FROM node:24-alpine AS builder

WORKDIR /build

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --frozen-lockfile

COPY frontend/ .
ARG VITE_API_URL=http://127.0.0.1:8000/api/v1
ENV VITE_API_URL=${VITE_API_URL}
RUN npm run build

FROM node:24-alpine AS runner

WORKDIR /app
USER 65532:65532

RUN npm install -g serve
COPY --from=builder --chown=65532:65532 /build/dist /app/dist

EXPOSE 80
CMD ["serve", "-s", "dist", "-l", "tcp://0.0.0.0:80"]