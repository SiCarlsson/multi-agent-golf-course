FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install packages
RUN npm install

# Copy the entire frontend source code
COPY . .

# Build the app
RUN npm run build

# Install serve package to build app
RUN npm install -g serve

# Expose port
EXPOSE 5173

# Serve the production build
CMD ["serve", "-s", "dist", "-l", "5173"]
