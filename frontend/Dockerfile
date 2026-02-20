# Build stage
FROM node:20-alpine AS build-stage

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies (using npm ci for reliable builds)
RUN npm ci

# Copy the rest of the application code
COPY . .

# Set environment variable for build
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL

# Build the Vue/Vite application
RUN npm run build

# Production stage
FROM nginx:alpine AS production-stage

# Optional: Add custom nginx configuration here if needed
# COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy the built assets from the build stage
COPY --from=build-stage /app/dist /usr/share/nginx/html

# Expose port 80
EXPOSE 80

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]
