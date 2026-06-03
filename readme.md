# URL Shortening Service
*Project from: [roadmap.sh](https://roadmap.sh/projects/url-shortening-service)*

RESTful API that allows users to shorten long URLs.
### Tech Stack
FastAPI(Python framework), PostgreSQL(for databases), Redis(for caching)



## Features
- Using Redis as a high-performance cache
- Rate Limiter
- Base62 encoding to generate short codes from the ID database.
   ### User can:
- Create a new short URL

- Retrieve an original URL from a short URL

- Be redirected to the original URL from the short URL.

- Update an existing short URL

- Delete an existing short URL

- Get statistics on the short URL (number of times accessed)


## Installation and Setup

### 1. Clone the repository:
```bash
git clone https://github.com/Ficserbiyy/shorty-url.git
```

### 2. Create a .env file in the root directory and add Environment Variables:
```.env
DB_PASSWORD=password
DB_USER=postgres
DB_NAME=shorty
DB_HOST=db
REDIS_URL=redis://redis:6379
```

### 3. Use [Docker](https://docs.docker.com/get-started/get-docker/) to Launch the application:
```bash
docker-compose up --build  # First launch only or after updating the code 
docker-compose up          # For regular use
```

### 4. Go to http://127.0.0.1:8000/docs to see the automatic interactive API documentation.
**To redirect, you need to go to the exact address.** For example, http://localhost:8000/1 if shortcode = 1
