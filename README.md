# Online Auction & Bidding System

> A backend-focused online auction and bidding platform built with **FastAPI, PostgreSQL, SQLAlchemy, and JWT authentication**, with an emphasis on transactional consistency, concurrency control, and reliable bidding workflows.

> 🚧 **Project Status: In Development**
> This project is actively being developed. Features and documentation will be updated as development progresses.

## Overview

The Online Auction & Bidding System is a backend application designed to simulate an online auction platform where users can register, authenticate, manage their account balance, create and manage auction items, and participate in bidding.

The project focuses not only on implementing REST APIs, but also on solving real backend engineering problems such as **authentication, authorization, database transactions, concurrency, locking, race-condition prevention, and failure handling**.

## Tech Stack

* **Language:** Python
* **Framework:** FastAPI
* **Database:** PostgreSQL
* **ORM:** SQLAlchemy
* **Authentication:** JWT
* **API:** REST
* **Testing/API Client:** Postman
* **Version Control:** Git, GitHub

## Features

### Authentication & Authorization

* User registration and login
* JWT-based authentication
* Protected API endpoints
* User authorization and access control

### User & Account Management

* User profile management
* Account balance management
* Balance validation for bidding operations

### Auction Management

* Create and manage auction items
* Define auction details and lifecycle
* Track active auctions
* Manage auction status

### Bidding System

* Place bids on active auctions
* Validate bidding conditions
* Maintain bid history
* Prevent invalid bids
* Handle concurrent bidding operations safely

### Transaction & Concurrency Management

* Database transactions for critical operations
* Concurrency control for simultaneous bids
* Database locking where required
* Prevention of race conditions
* Failure rollback to maintain database consistency

## Project Architecture

The application follows a modular backend architecture separating API routing, business logic, data validation, and database operations.

```text
auction_system/
│
├── app/
│   ├── routers/
│   ├── services/
│   ├── models/
│   ├── schemas/
│   ├── database/
│   └── main.py
│
├── tests/
│
├── requirements.txt
├── .gitignore
└── README.md
```

## API Documentation

The application uses FastAPI's automatically generated API documentation.

When running locally:

* **Swagger UI:** `/docs`
* **ReDoc:** `/redoc`

## Running Locally

### 1. Clone the repository

```bash
git clone https://github.com/vivekverma328/auction-system.git
cd auction-system
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

Activate it:

**Windows**

```bash
venv\Scripts\activate
```

**Linux/macOS**

```bash
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file and configure the required database and authentication settings.

Example:

```env
DATABASE_URL=postgresql://username:password@localhost:5432/auction_db
SECRET_KEY=your_secret_key
```

### 5. Start the application

```bash
uvicorn app.main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

API documentation:

```text
http://127.0.0.1:8000/docs
```

## Development Roadmap

* [x] FastAPI project setup
* [x] PostgreSQL database integration
* [x] SQLAlchemy models
* [x] User management
* [x] Product management
* [x] JWT authentication
* [x] Login flow
* [x] Account balance management
* [ ] Auction lifecycle
* [ ] Complete bidding workflow
* [ ] Concurrency control and locking
* [ ] Transaction rollback and failure handling
* [ ] Automated testing
* [ ] Dockerization
* [ ] CI/CD
* [ ] Deployment

## Engineering Focus

This project is being developed with a focus on practical backend engineering concepts rather than only CRUD functionality.

Key areas include:

* RESTful API design
* Authentication and authorization
* Relational database design
* SQLAlchemy ORM
* Database transactions
* Concurrency and race conditions
* Pessimistic locking
* Data consistency
* Failure handling and rollback
* Testing and reliability
* Containerization and deployment

## Future Improvements

Planned improvements include caching, background processing, automated testing, Docker-based deployment, CI/CD, monitoring, and other production-oriented backend components.

## Project Status

**🚧 Actively under development**

The repository will be continuously updated as new backend features and production-oriented improvements are implemented.
