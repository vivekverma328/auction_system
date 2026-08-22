# Online Auction & Bidding System

A backend-focused auction platform built with **FastAPI, PostgreSQL, SQLAlchemy, Redis, JWT authentication, Alembic, Pytest, and Docker**.

The project focuses on reliable backend engineering: authenticated auction creation, automated lifecycle transitions, transactional bidding, concurrency control, Redis-based scheduling, failure recovery, testing, logging, and containerized local setup.

---

## Key Features

### Authentication & Users
- User registration and login
- JWT-based authentication with OAuth2
- Protected API endpoints
- Account balance management

### Auction Management
- Create and fetch auctions
- Auction ownership through authenticated users
- Start/end time validation
- Minimum and maximum auction duration validation
- Auctions can be scheduled up to 30 days in advance
- Pagination for auction listings

### Automated Auction Lifecycle

```text
SCHEDULED
    ↓
ACTIVE
    ↓
ENDED
```

Auction start and end times are scheduled using **Redis Sorted Sets**, and a separate background worker processes due events.

### Bidding Engine
- Bids allowed only on `ACTIVE` auctions
- Seller cannot bid on their own auction
- Bid must exceed the current highest bid
- Bidder must have sufficient balance
- Winning bid amount is reserved immediately
- Previous highest bidder is refunded automatically
- Same bidder can safely raise their bid
- Bid history with pagination

### Concurrency & Reliability
The system uses:

- PostgreSQL `SELECT ... FOR UPDATE`
- Redis distributed locks using `SET NX`
- Unique lock tokens with safe Lua-based release
- Conditional auction state transitions
- Database transactions
- Transactional outbox pattern
- Idempotent Redis scheduling

These mechanisms help prevent invalid state transitions, lost updates, duplicate processing, and inconsistent balances.

### Auction Settlement
When an auction ends, the reserved winning amount is transferred to the seller. If the auction receives no bids, it simply transitions to `ENDED`.

---

## Hybrid Redis + Transactional Outbox

Auction creation and outbox event creation happen in the same PostgreSQL transaction:

```text
POST /auctions
      ↓
Create Auction
      +
Create AUCTION_CREATED Outbox Event
      ↓
COMMIT
```

After commit, Redis is used as the normal fast scheduling path:

```text
PostgreSQL Commit
      ↓
Immediate Redis Scheduling
      ↓
Start + End Sorted Sets
      ↓
Outbox marked processed
```

If Redis is unavailable:

```text
PostgreSQL Commit ✅
      ↓
Redis Scheduling ❌
      ↓
Outbox remains pending
      ↓
Recovery Worker
      ↓
Retry Redis Scheduling
```

This keeps Redis fast while PostgreSQL provides a durable recovery path.

---

## Architecture

```text
                    Client
                      │
                      ▼
                   FastAPI
                      │
              Routers / Services
                      │
                 Repositories
                      │
                      ▼
                  PostgreSQL
          ┌───────────┼───────────┐
          │           │           │
        Users      Auctions      Bids
                      │
                      ▼
                Outbox Events
                      │
             Recovery when needed
                      │
                      ▼
                    Redis
            ┌─────────┴─────────┐
            │                   │
      Start Schedule       End Schedule
            │                   │
            └─────────┬─────────┘
                      ▼
              Background Worker
                ┌─────┴─────┐
                ▼           ▼
              ACTIVE       ENDED
```

---

## Tech Stack

- **Language:** Python
- **Framework:** FastAPI
- **Database:** PostgreSQL
- **ORM:** SQLAlchemy
- **Migrations:** Alembic
- **Scheduling / Locking:** Redis
- **Authentication:** JWT + OAuth2
- **Concurrency Control:** PostgreSQL row-level locking
- **Testing:** Pytest + FastAPI TestClient
- **Logging:** Python logging
- **Containerization:** Docker + Docker Compose
- **API Testing:** Postman
- **Version Control:** Git + GitHub

---

## Automated Testing

The project currently has **18 passing integration tests** covering:

- Registration and login
- Auction creation and retrieval
- Pagination
- Transactional outbox behavior
- Successful and invalid bidding scenarios
- Previous bidder refund
- Same-bidder bid increase
- Auction settlement
- Bid history
- Concurrent bidding
- Redis failure and outbox recovery

Run tests with:

```bash
python -m pytest -v
```

Tests use a separate PostgreSQL test database through `TEST_DATABASE_URL`.

---

## Project Structure

```text
auction_system/
├── app/
│   ├── core/
│   ├── models/
│   ├── schemas/
│   ├── routers/
│   ├── services/
│   ├── repositories/
│   ├── redis/
│   ├── workers/
│   ├── database.py
│   └── main.py
├── alembic/
├── tests/
├── Dockerfile
├── docker-compose.yml
├── alembic.ini
├── requirements.txt
└── README.md
```

---

## Run with Docker

Docker Compose starts the complete backend stack:

```text
FastAPI API
Background Worker
PostgreSQL
Redis
Alembic Migration Service
```

### 1. Configure environment variables

Create `.env.docker` with values similar to:

```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_DB=auction_system_db

DATABASE_URL=postgresql://postgres:your_password@db:5432/auction_system_db

REDIS_HOST=redis
REDIS_PORT=6379
```

Also include the JWT/security variables required by the application.

Do not commit `.env` or `.env.docker`.

### 2. Start the application

```bash
docker compose up --build
```

Docker Compose starts PostgreSQL and Redis, waits for health checks, runs Alembic migrations, and then starts the API and worker.

Swagger UI:

```text
http://localhost:8000/docs
```

### 3. Stop containers

```bash
docker compose down
```

PostgreSQL and Redis data are stored in Docker volumes and remain available across normal restarts.

A fresh clone on another machine starts with an empty database, while Alembic automatically creates the complete schema.

---

## Run Without Docker

Create and activate a virtual environment:

```bash
python -m venv .venv
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Apply migrations:

```bash
alembic upgrade head
```

Start FastAPI:

```bash
uvicorn app.main:app --reload
```

Start the worker in another terminal:

```bash
python -m app.workers.auction_workers
```

PostgreSQL and Redis must already be running and configured through environment variables.

---

## Example Auction Flow

```text
Seller creates auction
        ↓
SCHEDULED
        ↓
Redis schedules start/end
        ↓
ACTIVE
        ↓
Users place bids
        ↓
Highest bidder funds reserved
        ↓
Higher bid arrives
        ↓
Previous bidder refunded
        ↓
New highest bidder funds reserved
        ↓
ENDED
        ↓
Winning amount transferred to seller
```

---

## Current Status

Backend Phase 1 is complete:

- Authentication
- Auction management
- Redis scheduling
- Background worker
- Distributed locking
- Transactional outbox
- Bidding engine
- Balance reservation and refunds
- Concurrent bid protection
- Settlement
- Pagination
- Alembic migrations
- Automated tests
- Logging
- Docker
- Docker Compose

---

## Future Work

Planned next phases:

- Frontend application
- Real-time bidding updates with WebSockets
- Backend and frontend deployment
- GitHub Actions
- CI/CD pipeline
- Production database and Redis services
- Monitoring and observability