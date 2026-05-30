FROM node:20-slim AS deps
WORKDIR /app
COPY apps/web/package.json ./package.json
RUN npm install

FROM node:20-slim AS build
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY apps/web/ ./
RUN npx prisma generate && npm run build

FROM node:20-slim AS run
WORKDIR /app
ENV NODE_ENV=production
COPY --from=build /app ./
EXPOSE 3000
CMD ["npm", "run", "start"]
