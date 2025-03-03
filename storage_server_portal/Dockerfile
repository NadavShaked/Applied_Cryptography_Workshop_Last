# Use the specified Node.js version as the base image
FROM node:18.17.1-alpine AS builder

# Set the working directory
WORKDIR /app

# Copy package.json and package-lock.json to install dependencies
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the application
COPY . .

# Build the Next.js application
RUN npm run build

# Install only production dependencies
RUN npm ci --omit=dev

# Use a minimal Node.js image for production
FROM node:18.17.1-alpine AS runner

# Set the working directory
WORKDIR /app

# Copy the built application from the builder stage
COPY --from=builder /app/.next .next
COPY --from=builder /app/public public
COPY --from=builder /app/package.json package.json
COPY --from=builder /app/node_modules node_modules

# Expose the Next.js default port
EXPOSE 3000

# Set the startup command
CMD ["npm", "run", "dev"]
