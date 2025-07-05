# Multi-stage Dockerfile for SvelteKit frontend
# Optimized for both development and production

# Base stage with common dependencies
FROM node:20-alpine AS base
WORKDIR /app
RUN apk add --no-cache curl

# Development stage with hot reloading
FROM base AS development
ENV NODE_ENV=development

# Copy package files
COPY package*.json ./

# Install all dependencies including dev dependencies
RUN npm ci

# Copy application code
COPY . .

# Expose Vite dev server port
EXPOSE 5173

# Start development server with hot reloading
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]

# Builder stage for production
FROM base AS builder
ENV NODE_ENV=production

# Copy package files
COPY package*.json ./

# Install production dependencies
RUN npm ci --only=production

# Copy application code
COPY . .

# Build the application
RUN npm run build

# Production stage - minimal runtime
FROM base AS production
ENV NODE_ENV=production

# Create non-root user
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nodejs -u 1001

# Copy built application from builder
COPY --from=builder --chown=nodejs:nodejs /app/build /app/build
COPY --from=builder --chown=nodejs:nodejs /app/package*.json /app/

# Install only production runtime dependencies
RUN npm ci --only=production && \
    npm cache clean --force

# Use non-root user
USER nodejs

# Expose production port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:3000/ || exit 1

# Start production server
CMD ["node", "build"]