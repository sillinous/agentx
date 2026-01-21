FROM node:20-alpine

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm install

# Copy application
COPY . .

# Build
RUN npm run build

EXPOSE 3001

CMD ["npm", "start"]
