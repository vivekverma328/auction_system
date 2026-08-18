# Online Auction & Bidding System

A backend-focused Online Auction & Bidding System built with **FastAPI, PostgreSQL, SQLAlchemy, Redis, and JWT authentication**.

The project focuses on building a reliable auction backend with authentication, scheduled auction lifecycle management, concurrency control, distributed locking, background workers, and failure-safe event processing.

The bidding engine is currently under development.

---

## Features Implemented

### Authentication & Users

* User registration and login
* JWT-based authentication
* OAuth2 authentication flow
* Protected API endpoints
* User data stored in PostgreSQL

### Auction Management

* Create auctions
* Fetch individual auctions
* Fetch all auctions
* Auction ownership through authenticated users
* Start-time and end-time validation
* Minimum and maximum auction-duration validation
* Auctions can be scheduled up to 30 days in advance

### Automated Auction Lifecycle

Auctions automatically transition through:

```text
SCHEDULED
    ↓
ACTIVE
    ↓
ENDED
```

The transitions happen based on the configured `start_time` and `end_time`.

### Redis-Based Scheduling

Redis Sorted Sets are used to maintain scheduled auction events.

```text
auction:start_schedule
auction:end_schedule
```

Auction timestamps are stored as Redis sorted-set scores, allowing the worker to efficiently retrieve auctions whose scheduled time has arrived.

### Background Worker

A separate worker process continuously handles:

```text
Pending Outbox Events
        ↓
Redis Scheduling
        ↓
Due Auction Starts
        ↓
SCHEDULED → ACTIVE
        ↓
Due Auction Ends
        ↓
ACTIVE → ENDED
```

The API server and worker run as separate processes.

### Distributed Locking

Redis distributed locks prevent multiple workers from processing the same auction concurrently.

Locks use:

* Redis `SET NX`
* Automatic lock expiration
* Unique lock tokens
* Safe lock release using a Lua script

This allows multiple worker instances to run while ensuring only one worker processes a particular auction event at a time.

### Atomic Database State Transitions

Auction state transitions are performed using conditional database updates.

For example:

```text
SCHEDULED → ACTIVE
```

is executed only when the current database status is actually `SCHEDULED`.

Similarly:

```text
ACTIVE → ENDED
```

is allowed only when the current status is `ACTIVE`.

This prevents invalid transitions such as:

```text
ENDED → ACTIVE
```

and protects against race conditions between multiple workers.

### Transactional Outbox Pattern

Auction creation and event creation happen inside the same PostgreSQL transaction.

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

The background worker reads unprocessed outbox events and schedules the auction in Redis.

```text
Outbox Event
     ↓
Redis Start Schedule
Redis End Schedule
     ↓
processed_at updated
```

If Redis is temporarily unavailable, the outbox event remains pending and can be retried later.

This prevents an auction from being permanently created in PostgreSQL without being scheduled in Redis.

---

## Architecture

```text
Client / Postman
       ↓
     FastAPI
       ↓
    Routers
       ↓
    Services
       ↓
  Repositories
       ↓
   PostgreSQL
       │
       ├── Users
       ├── Auctions
       └── Outbox Events
              ↓
        Background Worker
              ↓
            Redis
        ┌─────┴─────┐
        ↓           ↓
 Start Schedule   End Schedule
        ↓           ↓
     ACTIVE       ENDED
```

---

## Tech Stack

* **Language:** Python
* **Backend Framework:** FastAPI
* **Database:** PostgreSQL
* **ORM:** SQLAlchemy
* **Caching / Scheduling:** Redis
* **Authentication:** JWT, OAuth2
* **API Style:** REST APIs
* **Server:** Uvicorn
* **Testing / Development:** Postman
* **Version Control:** Git, GitHub

---

## Project Structure

```text
app/
│
├── models/
│   ├── users.py
│   ├── auctions.py
│   └── outbox.py
│
├── schemas/
│   ├── users.py
│   └── auctions.py
│
├── routers/
│   ├── users.py
│   ├── auth.py
│   └── auctions.py
│
├── services/
│   └── auctions.py
│
├── repositories/
│   ├── auctions.py
│   └── outbox.py
│
├── redis/
│   ├── client.py
│   ├── scheduler.py
│   └── lock.py
│
├── workers/
│   └── auction_workers.py
│
├── database.py
└── main.py
```

---

## Running the Project

### 1. Create and activate a virtual environment

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Start PostgreSQL

Configure the PostgreSQL connection used by the application.

### 4. Start Redis

Ensure a Redis server is running and accessible by the application.

### 5. Start FastAPI

```bash
uvicorn app.main:app --reload
```

API documentation is available through FastAPI's Swagger UI after the server starts.

### 6. Start the Auction Worker

Open another terminal using the same virtual environment:

```bash
python -m app.workers.auction_workers
```

The worker processes outbox events and automatically handles scheduled auction lifecycle transitions.

---

## Auction Lifecycle Example

An auction is created with:

```text
status = SCHEDULED
start_time = future timestamp
end_time = future timestamp
```

The application creates:

```text
Auction
+
AUCTION_CREATED Outbox Event
```

The worker processes the outbox event and adds:

```text
auction:<id> → start timestamp
auction:<id> → end timestamp
```

to Redis.

At `start_time`:

```text
SCHEDULED → ACTIVE
```

At `end_time`:

```text
ACTIVE → ENDED
```

Processed Redis scheduling entries are removed after successful handling.

---

## Concurrency & Reliability

The current implementation uses multiple layers of protection:

```text
Redis Distributed Lock
        +
Conditional PostgreSQL Updates
        +
Transactional Outbox
        +
Idempotent Redis Scheduling
```

This allows multiple workers to operate safely while reducing duplicate processing and preventing invalid auction-state transitions.

---

## Upcoming Development

The next major module is the bidding engine, including:

* Bid placement APIs
* Bid validation
* Concurrent bidding
* Highest-bid consistency
* Database transactions and row-level locking
* Bid history
* Balance handling
* Failure rollback
* Pagination
* Caching
* Logging and monitoring
* Automated testing
* Docker
* CI/CD

---

## Current Status

Completed:

```text
Authentication
    ↓
Auction Creation
    ↓
Transactional Outbox
    ↓
Redis Scheduling
    ↓
Background Workers
    ↓
Distributed Locking
    ↓
Atomic State Transitions
    ↓
SCHEDULED → ACTIVE → ENDED
```

Next:

```text
Bidding Engine
```
