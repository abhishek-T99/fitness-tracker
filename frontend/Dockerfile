FROM node:20-alpine

WORKDIR /app

# Install deps in their own layer.
COPY package.json package-lock.json* ./
RUN npm install

# Source is mounted at runtime via compose for hot reload; we COPY here too
# so the image is self-contained if someone runs it without a bind mount.
COPY . .

EXPOSE 5173

# `--host` binds 0.0.0.0 so the container is reachable from the host.
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
