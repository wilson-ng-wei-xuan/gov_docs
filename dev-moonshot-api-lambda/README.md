# Moonshot API

Implement an API using FastAPI and deploy it using either Application Load Balancer (ALB) or API Gateway.

## API Endpoints

## Test

### Local Testing

Copy `.env.dev` to `.env` and run the API in local machine.

```bash
cd src
cp .env.dev .env
python -m uvicorn app.main:app --port 8080 --reload
```
