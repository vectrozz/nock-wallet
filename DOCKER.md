# Docker Deployment Guide

## 📦 Services

### 1. Backend (Flask API)
- **Port**: 5007
- **Features**: 
  - Transaction management
  - Wallet operations
  - History tracking
- **Volumes**:
  - Application code
  - Transaction files
  - Wallet history
  - Shared wallet data

### 2. Frontend (Vite + Vanilla JS)
- **Port**: 5173
- **Features**:
  - Web interface
  - Real-time updates
  - Transaction management
- **Environment**:
  - `VITE_API_BASE_URL`: Backend API URL

### 3. Nockchain Wallet (To be configured)
- **Purpose**: Nockchain wallet service
- **Volumes**:
  - Wallet data
  - Transaction files (shared with backend)

## 🚀 Quick Start

### Prerequisites
- Docker Engine 20.10+
- Docker Compose 2.0+

### Build and Run

```bash
# Build all services
docker-compose build

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

### Access the Application

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:5007
- **API Health**: http://localhost:5007/api/balance

## 🔧 Development

### Backend Development

```bash
# Rebuild backend only
docker-compose build backend

# Restart backend
docker-compose restart backend

# View backend logs
docker-compose logs -f backend
```

### Frontend Development

```bash
# Rebuild frontend only
docker-compose build frontend

# Restart frontend
docker-compose restart frontend

# View frontend logs
docker-compose logs -f frontend
```

### Hot Reload

Both frontend and backend are configured with volume mounts for hot reload:
- Backend: Changes to `backend/*.py` will restart Flask
- Frontend: Changes to `frontend/*.js`, `frontend/*.html`, `frontend/*.css` will trigger Vite HMR

## 📊 Volumes

### nockchain-wallet-data
Persistent volume for wallet data:
- Private keys
- Wallet state
- Configuration

### Local Mounts
- `./backend/txs`: Transaction files (shared between backend and nockchain-wallet)
- `./backend/wallet_history.json`: Transaction history

## 🌐 Network

All services communicate via the `nockchain-network` bridge network:
- Internal DNS resolution
- Isolated from other Docker networks
- Services can reference each other by service name

## 🛠️ Configuration

### Backend Environment Variables

```env
FLASK_HOST=0.0.0.0
FLASK_PORT=5007
FLASK_DEBUG=True
```

### Frontend Environment Variables

```env
VITE_API_BASE_URL=http://localhost:5007
```

For production, change to your backend URL:
```env
VITE_API_BASE_URL=http://your-domain.com:5007
```

## 🔒 Security Notes

- Never commit sensitive data in volumes
- Use Docker secrets for production
- Change default ports in production
- Set `FLASK_DEBUG=False` in production
- Use HTTPS in production with reverse proxy

## 📝 TODO: Nockchain Wallet Service

The `nockchain-wallet` service configuration needs to be completed:

1. Choose base image (Ubuntu/Debian with Rust support)
2. Install nockchain-wallet CLI
3. Configure wallet initialization
4. Set up proper volume mounts
5. Configure networking with backend

Example structure to implement:
```yaml
nockchain-wallet:
  build:
    context: ./nockchain-wallet
    dockerfile: Dockerfile
  environment:
    - WALLET_CONFIG=/root/.nockchain-wallet
  volumes:
    - nockchain-wallet-data:/root/.nockchain-wallet
    - ./backend/txs:/txs
  command: # Command to keep wallet service running
```

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Check ports
sudo lsof -i :5007
sudo lsof -i :5173

# Stop services using these ports
docker-compose down
```

### Permission Issues
```bash
# Fix permissions on Linux
sudo chown -R $USER:$USER ./backend/txs
sudo chown -R $USER:$USER ./backend/wallet_history.json
```

### Container Won't Start
```bash
# View detailed logs
docker-compose logs backend
docker-compose logs frontend

# Rebuild without cache
docker-compose build --no-cache
```

### Network Issues
```bash
# Recreate network
docker-compose down
docker network prune
docker-compose up -d
```

## 📚 Useful Commands

```bash
# View all containers
docker-compose ps

# Execute command in container
docker-compose exec backend bash
docker-compose exec frontend sh

# View resource usage
docker-compose stats

# Remove all containers and volumes
docker-compose down -v

# Pull latest images
docker-compose pull

# Scale services (if configured)
docker-compose up -d --scale backend=2
```