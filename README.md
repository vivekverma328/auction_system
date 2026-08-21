# Online Auction & Bidding System

A backend-focused Online Auction & Bidding System built with **FastAPI, PostgreSQL, SQLAlchemy, Redis, JWT authentication, and Alembic**.

The project focuses on building a reliable and concurrent auction backend with authentication, automated auction lifecycle management, transactional bidding, balance reservation and refunds, distributed locking, background workers, failure recovery, database migrations, logging, and automated testing.

---

## Features Implemented

### Authentication & Users

- User registration
- User login
- JWT-based authentication
- OAuth2 authentication flow
- Protected API endpoints
- User account balance management
- User data stored in PostgreSQL

### Auction Management

- Create auctions
- Fetch individual auctions
- Fetch all auctions
- Auction ownership through authenticated users
- Starting-price validation
- Start-time and end-time validation
- Minimum auction duration validation
- Maximum auction duration validation
- Auctions can be scheduled up to 30 days in advance
- Pagination for auction listing

## Automated Auction Lifecycle

Auctions automatically transition through:

```text
SCHEDULED
    ↓
ACTIVE
    ↓
ENDED
```

The lifecycle is controlled using auction `start_time` and `end_time`.

Redis Sorted Sets are used to efficiently identify auctions whose scheduled execution time has arrived.

## Redis-Based Scheduling

Redis Sorted Sets maintain scheduled auction events:

```text
auction:start_schedule
auction:end_schedule
```

Each auction is stored using:

```text
auction:<id>
```

with the scheduled timestamp stored as the sorted-set score.

This allows the worker to efficiently retrieve only auctions whose start or end time has arrived instead of repeatedly scanning the PostgreSQL auctions table.

## Background Worker

The API server and auction worker run as separate processes.

The worker performs two responsibilities:

```text
Redis Due Events
      ↓
Auction Start / End Processing
```

and:

```text
Pending Outbox Events
      ↓
Recovery Scheduling
      ↓
Redis
```

The worker continuously checks Redis for due auction events and periodically processes unhandled transactional outbox events.

## Distributed Locking

Redis distributed locks prevent multiple worker instances from processing the same auction concurrently.

The lock implementation uses:

- Redis `SET NX`
- Automatic expiration
- Unique lock tokens
- Safe Lua-based lock release

Conceptually:

```text
Worker A ── acquire lock ── SUCCESS
Worker B ── acquire lock ── FAILURE
Worker C ── acquire lock ── FAILURE
```

Only the worker that successfully acquires the lock processes the auction event.

## Atomic Auction State Transitions

Auction state transitions are protected at the PostgreSQL level.

For example:

```text
SCHEDULED → ACTIVE
```

is performed only when the current auction status is actually:

```text
SCHEDULED
```

Similarly:

```text
ACTIVE → ENDED
```

is only allowed when the auction is currently:

```text
ACTIVE
```

This prevents stale workers or duplicate events from causing invalid transitions such as:

```text
ENDED → ACTIVE
```

# Bidding Engine

Authenticated users can place bids on active auctions.

The bidding system validates:

- Auction exists
- Auction is currently `ACTIVE`
- Seller cannot bid on their own auction
- Bid must exceed the current highest bid
- Bidder must have sufficient account balance

## Balance Reservation

When a user becomes the highest bidder, the bid amount is reserved immediately from their account balance.

Example:

```text
Bidder Balance = 10,000
Bid Amount      = 1,500

After bid:

Available Balance = 8,500
Reserved Amount   = 1,500
```

This prevents users from placing multiple bids using money that has already been committed to another auction.

## Previous Bidder Refund

When another bidder places a higher bid:

```text
Bidder A → 1,500
Bidder B → 2,000
```

the system performs:

```text
Refund Bidder A
      +
Reserve 2,000 from Bidder B
      +
Update Highest Bid
```

inside the bidding transaction.

## Same Bidder Raising Their Bid

If the current highest bidder increases their own bid:

```text
Previous Bid = 1,500
New Bid      = 2,000
```

the system considers the previously reserved amount while validating the bidder's available balance.

This prevents the same bidder from incorrectly being charged twice.

## Database Row-Level Locking

Concurrent bids are protected using PostgreSQL row-level locks.

The auction row is locked using:

```text
SELECT ... FOR UPDATE
```

Relevant user rows are also locked before balance modifications.

This ensures concurrent bid requests cannot overwrite each other's updates or create inconsistent balances.

## Bid History

All successful bids are stored in PostgreSQL.

Bid history can be retrieved using:

```text
GET /auctions/{auction_id}/bids
```

with pagination support.

# Auction Settlement

When an auction ends:

```text
ACTIVE → ENDED
```

the winning amount has already been reserved from the winning bidder.

The auction settlement process transfers that reserved amount to the seller.

Example:

```text
Winning Bid = 2,000

Winner:
Balance already reduced during bidding

Seller:
Balance += 2,000
```

If an auction receives no bids, it simply transitions to `ENDED` without transferring funds.

# Transactional Outbox Pattern

Auction creation and outbox-event creation occur inside the same PostgreSQL transaction.

```text
POST /auctions
       ↓
PostgreSQL Transaction
       │
       ├── Create Auction
       │
       └── Create AUCTION_CREATED Outbox Event
       │
       ↓
     COMMIT
```

This guarantees that the auction and its scheduling event are persisted together.

## Hybrid Redis + Outbox Scheduling

Redis is used as the normal fast scheduling path.

After the PostgreSQL transaction commits:

```text
Auction + Outbox Event
        ↓
      COMMIT
        ↓
Immediate Redis Scheduling
        ↓
Start + End Sorted Sets
        ↓
Outbox marked processed
```

If Redis is temporarily unavailable:

```text
PostgreSQL COMMIT ✅
        ↓
Redis Scheduling ❌
        ↓
Outbox remains pending
        ↓
Recovery Worker
        ↓
Retry Redis Scheduling
        ↓
Outbox marked processed
```

This design keeps Redis on the normal high-speed execution path while using PostgreSQL transactional outbox events as a reliability and recovery mechanism.

# Failure Safety

The backend uses several layers of protection:

```text
Redis Distributed Locks
        +
PostgreSQL Row-Level Locks
        +
Conditional State Transitions
        +
Database Transactions
        +
Transactional Outbox
        +
Idempotent Redis Scheduling
```

These mechanisms reduce duplicate processing, race conditions, invalid state changes, and lost scheduling events.

# Database Migrations

Database schema changes are managed using **Alembic**.

The database schema includes:

```text
Users
Auctions
Bids
Outbox Events
Alembic Version
```

Schema updates are applied using:

```bash
alembic upgrade head
```

This replaces runtime table creation and provides version-controlled database migrations.

# Logging

Python's built-in logging framework is used for important application and worker events.

Examples include:

```text
INFO    Auction created
INFO    Auction activated
INFO    Bid accepted
INFO    Auction settled
INFO    Outbox event recovered
WARNING Unexpected recoverable conditions
ERROR   Worker or Redis processing failures
```

Logs include:

```text
Timestamp
Log Level
Module Name
Message
```

Sensitive information such as passwords and JWT tokens is not logged.

# Automated Testing

The project includes integration tests using **pytest** and FastAPI's test client.

Current automated coverage includes:

- User registration
- Login
- Invalid login
- Auction creation
- Transactional outbox processing
- Auction retrieval
- Auction pagination
- Successful bidding
- Seller bidding validation
- Low-bid rejection
- Insufficient-balance rejection
- Previous bidder refund
- Same-bidder bid increase
- Bid rejection after auction end
- Seller settlement
- Bid-history pagination
- Concurrent bidding
- Redis failure and outbox recovery

Current test suite:

```text
18 tests passed
```

Tests use a separate PostgreSQL test database to avoid modifying development data.

Run tests using:

```bash
python -m pytest -v
```

# Architecture

```text
                         Client
                           │
                           ▼
                        FastAPI
                           │
                    ┌──────┴──────┐
                    │             │
                Authentication   Routers
                                  │
                                  ▼
                               Services
                                  │
                                  ▼
                             Repositories
                                  │
                                  ▼
                             PostgreSQL
                    ┌─────────────┼─────────────┐
                    │             │             │
                  Users        Auctions        Bids
                                  │
                                  ▼
                            Outbox Events
                                  │
                     Recovery only when needed
                                  │
                                  ▼
                                Redis
                       ┌──────────┼──────────┐
                       │                     │
                 Start Schedule         End Schedule
                       │                     │
                       └─────────┬───────────┘
                                 │
                                 ▼
                         Background Worker
                                 │
                      ┌──────────┴──────────┐
                      ▼                     ▼
                   ACTIVE                 ENDED
```

# Tech Stack

- **Language:** Python
- **Backend Framework:** FastAPI
- **Database:** PostgreSQL
- **ORM:** SQLAlchemy
- **Database Migrations:** Alembic
- **Scheduling:** Redis Sorted Sets
- **Distributed Locking:** Redis
- **Authentication:** JWT + OAuth2
- **Concurrency Control:** PostgreSQL Row-Level Locking
- **API Style:** REST APIs
- **Server:** Uvicorn
- **Testing:** Pytest, FastAPI TestClient
- **Logging:** Python Logging
- **API Testing:** Postman
- **Version Control:** Git, GitHub

# Project Structure

```text
auction_system/
│
├── app/
│   │
│   ├── core/
│   │   ├── dependencies.py
│   │   ├── logging_config.py
│   │   └── security.py
│   │
│   ├── models/
│   │   ├── base.py
│   │   ├── users.py
│   │   ├── auctions.py
│   │   ├── bids.py
│   │   └── outbox.py
│   │
│   ├── schemas/
│   │   ├── users.py
│   │   ├── auctions.py
│   │   └── bids.py
│   │
│   ├── routers/
│   │   ├── users.py
│   │   ├── auth.py
│   │   ├── auctions.py
│   │   └── bids.py
│   │
│   ├── services/
│   │   ├── users.py
│   │   ├── auctions.py
│   │   └── bids.py
│   │
│   ├── repositories/
│   │   ├── users.py
│   │   ├── auctions.py
│   │   ├── bids.py
│   │   └── outbox.py
│   │
│   ├── redis/
│   │   ├── client.py
│   │   ├── scheduler.py
│   │   └── lock.py
│   │
│   ├── workers/
│   │   └── auction_workers.py
│   │
│   ├── database.py
│   └── main.py
│
├── alembic/
│
├── tests/
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_auctions.py
│   ├── test_bidding.py
│   ├── test_concurrency.py
│   └── test_outbox_recovery.py
│
├── alembic.ini
├── requirements.txt
└── README.md
```

# Running the Project

## 1. Create a virtual environment

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

## 2. Install Dependencies

```bash
pip install -r requirements.txt
```

## 3. Configure Environment Variables

Configure the required PostgreSQL, Redis, and JWT environment variables.

Example:

```text
DATABASE_URL
REDIS_HOST
REDIS_PORT
```

Authentication-related secret values should also be configured through environment variables.

Do not commit environment files containing secrets to GitHub.

## 4. Start PostgreSQL

Ensure PostgreSQL is running and the configured database exists.

Apply database migrations:

```bash
alembic upgrade head
```

## 5. Start Redis

Ensure Redis is running and accessible using the configured Redis host and port.

## 6. Start FastAPI

```bash
uvicorn app.main:app --reload
```

Swagger API documentation is available at:

```text
http://127.0.0.1:8000/docs
```

## 7. Start the Auction Worker

Open another terminal using the same virtual environment:

```bash
python -m app.workers.auction_workers
```

The worker handles scheduled lifecycle events and transactional-outbox recovery.

## 8. Run Automated Tests

Configure a separate PostgreSQL test database using:

```text
TEST_DATABASE_URL
```

Then run:

```bash
python -m pytest -v
```

# Example Auction Flow

```text
Seller Creates Auction
        ↓
Auction = SCHEDULED
        ↓
Auction + Outbox Event committed
        ↓
Redis Start / End scheduling
        ↓
start_time reached
        ↓
SCHEDULED → ACTIVE
        ↓
Users place bids
        ↓
Highest bidder funds reserved
        ↓
Higher bid arrives
        ↓
Previous bidder refunded
        ↓
New bidder funds reserved
        ↓
end_time reached
        ↓
ACTIVE → ENDED
        ↓
Winning amount transferred to seller
```

# Current Status

Completed:

```text
Authentication
        ↓
Auction Management
        ↓
Redis Scheduling
        ↓
Background Workers
        ↓
Distributed Locking
        ↓
Transactional Outbox
        ↓
Hybrid Redis + Outbox Recovery
        ↓
Bidding Engine
        ↓
Balance Reservation & Refund
        ↓
Concurrent Bid Protection
        ↓
Auction Settlement
        ↓
Pagination
        ↓
Alembic Migrations
        ↓
Automated Testing
        ↓
Logging
```

# Upcoming Development

Immediate next step:

```text
Docker
    ↓
Docker Compose
```

Future phases:

- Frontend application
- Real-time bidding updates
- WebSockets
- Deployment
- GitHub Actions
- CI/CD pipeline
- Production database and Redis services
- Monitoring and observability
- Additional performance improvements

## Development Status

The backend core is functionally complete for the current development phase.

The next milestone is containerizing the backend using Docker and Docker Compose before moving toward frontend development and deployment.
