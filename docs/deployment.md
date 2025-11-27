# Deployment Guide

Production deployment strategies for Whale Knowledge Base.

## Deployment Options

### Option 1: Docker Compose (Single Server)

Best for small to medium deployments on a single server.

### Option 2: Kubernetes

Best for large-scale deployments requiring high availability and auto-scaling.

### Option 3: Cloud Services

Best for managed infrastructure with minimal operations.

## Prerequisites

### Required Services

- **PostgreSQL** database (or managed service)
- **Pinecone** account with index created
- **Domain name** (for production)
- **SSL certificate** (Let's Encrypt recommended)

### Optional Services

- **Jina Reader API** key (for web scraping)
- **Redis** (for caching)
- **Nginx** (for reverse proxy)
- **Monitoring** (Prometheus, Grafana)

## Docker Compose Deployment

### Production docker-compose.yml

Create a production-ready `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    container_name: whale-postgres
    restart: always
    environment:
      POSTGRES_USER: whale_user
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: whale_knowledge
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    networks:
      - whale-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U whale_user"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: whale-backend
    restart: always
    environment:
      DATABASE_URL: postgresql://whale_user:${POSTGRES_PASSWORD}@postgres:5432/whale_knowledge
      PINECONE_API_KEY: ${PINECONE_API_KEY}
      PINECONE_ENVIRONMENT: ${PINECONE_ENVIRONMENT}
      PINECONE_INDEX_NAME: ${PINECONE_INDEX_NAME}
      JINA_API_KEY: ${JINA_API_KEY}
      EMBEDDING_MODEL: sentence-transformers/all-MiniLM-L6-v2
      EMBEDDING_DIMENSION: 384
      LOG_LEVEL: info
    depends_on:
      postgres:
        condition: service_healthy
    networks:
      - whale-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/stats/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      args:
        NEXT_PUBLIC_API_URL: ${API_URL}
    container_name: whale-frontend
    restart: always
    environment:
      NEXT_PUBLIC_API_URL: ${API_URL}
      NODE_ENV: production
    depends_on:
      - backend
    networks:
      - whale-network
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G

  nginx:
    image: nginx:alpine
    container_name: whale-nginx
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
      - ./logs:/var/log/nginx
    depends_on:
      - frontend
      - backend
    networks:
      - whale-network

volumes:
  postgres_data:

networks:
  whale-network:
    driver: bridge
```

### Nginx Configuration

Create `nginx.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=general_limit:10m rate=100r/s;

    # Upstream servers
    upstream backend {
        server backend:8000;
    }

    upstream frontend {
        server frontend:3000;
    }

    # Redirect HTTP to HTTPS
    server {
        listen 80;
        server_name yourdomain.com;
        return 301 https://$server_name$request_uri;
    }

    # HTTPS server
    server {
        listen 443 ssl http2;
        server_name yourdomain.com;

        # SSL configuration
        ssl_certificate /etc/nginx/ssl/fullchain.pem;
        ssl_certificate_key /etc/nginx/ssl/privkey.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;
        ssl_prefer_server_ciphers on;

        # Security headers
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;

        # Frontend
        location / {
            proxy_pass http://frontend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_cache_bypass $http_upgrade;
            limit_req zone=general_limit burst=20 nodelay;
        }

        # Backend API
        location /api/ {
            rewrite ^/api/(.*) /$1 break;
            proxy_pass http://backend;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            limit_req zone=api_limit burst=5 nodelay;

            # Timeouts for long-running requests
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }

        # Health check endpoint (no rate limiting)
        location /api/stats/health {
            rewrite ^/api/(.*) /$1 break;
            proxy_pass http://backend;
        }

        # Increase max upload size
        client_max_body_size 50M;
    }
}
```

### Environment Variables

Create `.env.prod`:

```bash
# PostgreSQL
POSTGRES_PASSWORD=your_secure_password_here

# Pinecone
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_ENVIRONMENT=us-west1-gcp
PINECONE_INDEX_NAME=whale-knowledge

# Optional: Jina Reader
JINA_API_KEY=your_jina_api_key

# API URL (for frontend)
API_URL=https://yourdomain.com/api

# Deployment
NODE_ENV=production
LOG_LEVEL=info
```

### Deploy

```bash
# Copy environment file
cp .env.prod .env

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f
```

### SSL Certificate with Let's Encrypt

```bash
# Install certbot
sudo apt-get update
sudo apt-get install certbot

# Get certificate
sudo certbot certonly --standalone -d yourdomain.com

# Copy certificates
sudo mkdir -p ./ssl
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ./ssl/
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ./ssl/

# Set up auto-renewal
sudo certbot renew --dry-run
```

## Kubernetes Deployment

### Prerequisites

- Kubernetes cluster (EKS, GKE, AKS, or self-hosted)
- kubectl configured
- Helm (optional, for easier deployment)

### Kubernetes Manifests

**namespace.yaml:**
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: whale-knowledge
```

**secrets.yaml:**
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: whale-secrets
  namespace: whale-knowledge
type: Opaque
stringData:
  postgres-password: your_secure_password
  pinecone-api-key: your_pinecone_api_key
  jina-api-key: your_jina_api_key
```

**postgres-deployment.yaml:**
```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: whale-knowledge
spec:
  serviceName: postgres
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15-alpine
        env:
        - name: POSTGRES_USER
          value: whale_user
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: whale-secrets
              key: postgres-password
        - name: POSTGRES_DB
          value: whale_knowledge
        ports:
        - containerPort: 5432
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
  volumeClaimTemplates:
  - metadata:
      name: postgres-storage
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 20Gi
---
apiVersion: v1
kind: Service
metadata:
  name: postgres
  namespace: whale-knowledge
spec:
  ports:
  - port: 5432
  clusterIP: None
  selector:
    app: postgres
```

**backend-deployment.yaml:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  namespace: whale-knowledge
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: your-registry/whale-backend:latest
        env:
        - name: DATABASE_URL
          value: postgresql://whale_user:$(POSTGRES_PASSWORD)@postgres:5432/whale_knowledge
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: whale-secrets
              key: postgres-password
        - name: PINECONE_API_KEY
          valueFrom:
            secretKeyRef:
              name: whale-secrets
              key: pinecone-api-key
        - name: PINECONE_ENVIRONMENT
          value: us-west1-gcp
        - name: PINECONE_INDEX_NAME
          value: whale-knowledge
        ports:
        - containerPort: 8000
        livenessProbe:
          httpGet:
            path: /stats/health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /stats/health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
---
apiVersion: v1
kind: Service
metadata:
  name: backend
  namespace: whale-knowledge
spec:
  type: ClusterIP
  ports:
  - port: 8000
    targetPort: 8000
  selector:
    app: backend
```

**frontend-deployment.yaml:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
  namespace: whale-knowledge
spec:
  replicas: 2
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
    spec:
      containers:
      - name: frontend
        image: your-registry/whale-frontend:latest
        env:
        - name: NEXT_PUBLIC_API_URL
          value: https://yourdomain.com/api
        ports:
        - containerPort: 3000
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
---
apiVersion: v1
kind: Service
metadata:
  name: frontend
  namespace: whale-knowledge
spec:
  type: ClusterIP
  ports:
  - port: 3000
    targetPort: 3000
  selector:
    app: frontend
```

**ingress.yaml:**
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: whale-ingress
  namespace: whale-knowledge
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - yourdomain.com
    secretName: whale-tls
  rules:
  - host: yourdomain.com
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: backend
            port:
              number: 8000
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend
            port:
              number: 3000
```

### Deploy to Kubernetes

```bash
# Create namespace
kubectl apply -f namespace.yaml

# Create secrets
kubectl apply -f secrets.yaml

# Deploy PostgreSQL
kubectl apply -f postgres-deployment.yaml

# Deploy backend and frontend
kubectl apply -f backend-deployment.yaml
kubectl apply -f frontend-deployment.yaml

# Create ingress
kubectl apply -f ingress.yaml

# Check status
kubectl get pods -n whale-knowledge
kubectl get services -n whale-knowledge
kubectl get ingress -n whale-knowledge

# View logs
kubectl logs -n whale-knowledge -l app=backend -f
```

### Horizontal Pod Autoscaler

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: backend-hpa
  namespace: whale-knowledge
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

## Cloud Service Deployments

### AWS Deployment

**Services Used:**
- **ECS Fargate** - Container hosting
- **RDS PostgreSQL** - Managed database
- **ALB** - Load balancing
- **S3** - Static assets
- **CloudFront** - CDN
- **Secrets Manager** - Credentials

**Architecture:**
```
CloudFront → ALB → ECS Fargate (Frontend + Backend)
                         ↓
                   RDS PostgreSQL
                         ↓
                    Pinecone API
```

### Google Cloud Platform

**Services Used:**
- **Cloud Run** - Container hosting
- **Cloud SQL** - Managed PostgreSQL
- **Cloud Load Balancing** - Load balancer
- **Cloud Storage** - Static assets
- **Secret Manager** - Credentials

### Azure Deployment

**Services Used:**
- **Container Instances** - Container hosting
- **Azure Database for PostgreSQL** - Managed database
- **Application Gateway** - Load balancer
- **Blob Storage** - Static assets
- **Key Vault** - Credentials

## Database Management

### Backup Strategy

**Automated Backups:**
```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/whale_knowledge_$TIMESTAMP.sql"

# Create backup
docker exec whale-postgres pg_dump -U whale_user whale_knowledge > $BACKUP_FILE

# Compress
gzip $BACKUP_FILE

# Upload to S3 (optional)
aws s3 cp $BACKUP_FILE.gz s3://your-bucket/backups/

# Keep only last 7 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete

echo "Backup completed: $BACKUP_FILE.gz"
```

**Cron Job:**
```bash
# Add to crontab
0 2 * * * /path/to/backup.sh
```

### Restore from Backup

```bash
# Extract backup
gunzip whale_knowledge_20240115.sql.gz

# Restore
docker exec -i whale-postgres psql -U whale_user whale_knowledge < whale_knowledge_20240115.sql
```

### Migration Strategy

```bash
# Export from old database
pg_dump -h old-host -U whale_user whale_knowledge > export.sql

# Import to new database
psql -h new-host -U whale_user whale_knowledge < export.sql
```

## Monitoring and Logging

### Prometheus Monitoring

**prometheus.yml:**
```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'whale-backend'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: /metrics
```

### Grafana Dashboard

**Key Metrics:**
- Request rate
- Response time
- Error rate
- Database connection pool
- Memory usage
- CPU usage

### Logging

**Centralized Logging with ELK:**
```yaml
# docker-compose.yml addition
elasticsearch:
  image: elasticsearch:8.5.0
  environment:
    - discovery.type=single-node
  volumes:
    - elastic_data:/usr/share/elasticsearch/data

logstash:
  image: logstash:8.5.0
  volumes:
    - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf

kibana:
  image: kibana:8.5.0
  ports:
    - "5601:5601"
```

## Security Hardening

### Application Security

**Enable Authentication:**
```python
# backend/app/main.py
from fastapi import Depends, HTTPException, Header

async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return x_api_key

@app.post("/query/", dependencies=[Depends(verify_api_key)])
async def query(request: QueryRequest):
    # Protected endpoint
    pass
```

**Input Sanitization:**
```python
from bleach import clean

def sanitize_input(text: str) -> str:
    return clean(text, strip=True)
```

**Rate Limiting:**
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/query/")
@limiter.limit("10/minute")
async def query(request: Request, query: QueryRequest):
    pass
```

### Infrastructure Security

**Firewall Rules:**
```bash
# Allow only necessary ports
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 22/tcp  # SSH (restrict to specific IPs)
ufw enable
```

**Fail2Ban:**
```bash
# Install fail2ban
apt-get install fail2ban

# Configure for nginx
cat > /etc/fail2ban/jail.local <<EOF
[nginx-limit-req]
enabled = true
filter = nginx-limit-req
logpath = /var/log/nginx/*error.log
maxretry = 5
bantime = 3600
EOF

# Restart fail2ban
systemctl restart fail2ban
```

## Performance Tuning

### Backend Optimization

**Increase Workers:**
```bash
# Dockerfile
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

**Connection Pooling:**
```python
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True
)
```

### Database Optimization

**Create Indexes:**
```sql
CREATE INDEX idx_documents_industry ON documents(industry);
CREATE INDEX idx_documents_created_at ON documents(created_at);
CREATE INDEX idx_chunks_document_id ON chunks(document_id);
```

**Vacuum and Analyze:**
```bash
# Add to cron
0 3 * * 0 docker exec whale-postgres vacuumdb -U whale_user -d whale_knowledge -z
```

## Disaster Recovery

### Backup Plan

1. **Database:** Daily automated backups to S3
2. **Pinecone:** Export vectors monthly
3. **Config:** Version controlled in git
4. **Secrets:** Backed up in secure vault

### Recovery Procedure

1. Restore database from backup
2. Rebuild Pinecone index if needed
3. Redeploy containers
4. Verify health checks
5. Test critical functionality

### High Availability Setup

**Multi-Region Deployment:**
- Primary region: US-West
- Secondary region: US-East
- Database replication between regions
- Global load balancer (Route53, Cloud DNS)

## Cost Optimization

### Pinecone

- Use serverless for variable loads
- Delete unused indexes
- Monitor query costs

### Database

- Right-size instance
- Use read replicas for queries
- Enable auto-scaling

### Compute

- Use spot instances for non-critical workloads
- Auto-scale based on traffic
- Shut down dev environments when not in use

## Next Steps

- Review [Configuration](configuration.md) for tuning options
- Check [Architecture](architecture.md) for system design
- See [API Reference](api-reference.md) for endpoint details
- Read [Getting Started](getting-started.md) for local development
