# ==========================================
# Instalação de dependências
# ==========================================
FROM node:20-alpine AS deps
WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci

# ==========================================
# Build
# ==========================================
FROM node:20-alpine AS builder
WORKDIR /app

# Copia as dependências instaladas no estágio 1
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Faz o build do Next.js
RUN npm run build

# ==========================================
# Execução
# ==========================================
FROM node:20-alpine AS runner
WORKDIR /app

# Define ambiente como produção
ENV NODE_ENV production

COPY --from=builder /app/public ./public
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json

EXPOSE 3000

# Executa o servidor nativo do Next.js
CMD ["npm", "run", "start"]