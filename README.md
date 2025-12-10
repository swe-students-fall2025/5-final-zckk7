# Smart Apartment System

[![WebApp CI/CD](https://github.com/swe-students-fall2025/5-final-zckk7/actions/workflows/webapp.yml/badge.svg)](https://github.com/swe-students-fall2025/5-final-zckk7/actions/workflows/webapp.yml)
[![Sensor Simulator CI/CD](https://github.com/swe-students-fall2025/5-final-zckk7/actions/workflows/sensor_simulator.yml/badge.svg)](https://github.com/swe-students-fall2025/5-final-zckk7/actions/workflows/sensor_simulator.yml)
[![Alert System CI/CD](https://github.com/swe-students-fall2025/5-final-zckk7/actions/workflows/alert_system.yml/badge.svg)](https://github.com/swe-students-fall2025/5-final-zckk7/actions/workflows/alert_system.yml)

Smart apartment management platform with real-time sensor monitoring, automated alerts, maintenance requests, package tracking, and community features.

## Docker Images

- WebApp: `docker.io/helen2012sh/smart-apartment-webapp:latest`
- Sensor Simulator: `docker.io/helen2012sh/smart-apartment-simulator:latest`
- Alert Engine: `docker.io/helen2012sh/smart-apartment-alert-engine:latest`

## Team Members

- [Siqi Zhu](https://github.com/HelenZhutt)

## Getting Started

### Prerequisites

- Docker and Docker Compose
- MongoDB Atlas account or local MongoDB instance
- Python 3.11+ (for local development)
- Docker Hub account (for CI/CD)

### GitHub Secrets Configuration (Required for CI/CD)

Before CI/CD pipelines can work, configure GitHub Secrets:

**Required Secrets:**
- `DOCKER_USERNAME`: Your Docker Hub username (e.g., `helen2012sh`)
- `DOCKER_PASSWORD`: Your Docker Hub Personal Access Token

**Optional (for Digital Ocean deployment):**
- `DIGITALOCEAN_HOST`: Your DigitalOcean droplet IP address
- `DIGITALOCEAN_USERNAME`: SSH username (usually `root`)
- `DIGITALOCEAN_SSH_KEY`: Private SSH key for deployment
- `MONGODB_URI`: MongoDB connection string for production
- `MONGODB_DB`: Database name for production

To add secrets: Go to repository Settings → Secrets and variables → Actions → New repository secret

### Environment Setup

1. Copy `env.example` to `.env`:
```bash
cp env.example .env
```

2. Edit `.env` and set your MongoDB connection string:
```
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/?appName=Cluster0
MONGODB_DB=smart_apartment_db
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/?appName=Cluster0
DB_NAME=smart_apartment_db
```

### Running with Docker Compose

```bash
docker-compose up -d
```

This starts:
- Web application on http://localhost:5001
- Sensor simulator (generates sensor data)
- Alert engine (monitors and creates alerts)

### Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
pip install -r sensor_simulator/requirements.txt
pip install -r alert_system/requirements.txt
```

2. Set environment variables (or use `.env` file)

3. Initialize database:
```bash
python init_db.py
```

4. Run services separately:
```bash
python app.py
python -m sensor_simulator
python alert_system/alert_engine.py
```

### Database Initialization

Run `init_db.py` to create initial users and sample data:
```bash
python init_db.py
```

Default admin credentials are created by the init script.

### Testing

Run tests with coverage:
```bash
pytest tests/ --cov=app --cov-report=term
pytest sensor_simulator/tests/ --cov=sensor_simulator --cov-report=term
pytest alert_system/tests/ --cov=alert_system --cov-report=term
```
