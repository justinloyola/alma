# Build stage
FROM node:18-alpine as build

WORKDIR /app

# Copy package files and configs
COPY package*.json ./
COPY tsconfig.json ./
COPY tsconfig.paths.json ./
COPY vite.config.ts ./

# Install all dependencies including types
RUN npm install
RUN npm install react-toastify @types/react-toastify

# Copy the rest of the application
COPY . .

# Build the application with environment variables
# Note: These are the default values, they will be overridden by docker-compose
ARG VITE_API_BASE_URL=http://localhost:8000
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

# Print the environment variables for debugging
RUN echo "VITE_API_BASE_URL=$VITE_API_BASE_URL"

# Build the application
RUN npm run build

# Production stage
FROM nginx:stable-alpine

# Copy built assets from build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Remove default nginx config to prevent conflicts
RUN rm /etc/nginx/conf.d/default.conf

# Set permissions for nginx
RUN chown -R nginx:nginx /usr/share/nginx/html && \
    chmod -R 755 /usr/share/nginx/html && \
    chown -R nginx:nginx /var/cache/nginx && \
    chown -R nginx:nginx /var/log/nginx && \
    chown -R nginx:nginx /etc/nginx/nginx.conf && \
    chown -R nginx:nginx /etc/nginx/conf.d && \
    touch /var/run/nginx.pid && \
    chown -R nginx:nginx /var/run/nginx.pid

# Expose port 80
EXPOSE 80

# Use non-root user
USER nginx

# Start nginx in the foreground
CMD ["nginx", "-g", "daemon off;"]
