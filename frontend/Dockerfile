FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm ci

# Copy application code
COPY . .

# Expose port
EXPOSE 3000

# Run in development mode (for production, use: npm run build && npm start)
CMD ["npm", "run", "dev"]
