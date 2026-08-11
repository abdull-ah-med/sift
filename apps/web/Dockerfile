# syntax=docker/dockerfile:1

FROM node:22-bookworm-slim AS runtime
WORKDIR /app
COPY apps/web/package.json ./
RUN npm install --omit=dev --ignore-scripts || true
COPY apps/web ./
EXPOSE 3000
CMD ["node", "-e", "require('http').createServer((_,r)=>r.end('sift-web scaffold')).listen(3000)"]
