# Fastapi-auth

A sample project to achieve user authentication and authorization feature in fast api. 


# Run this project:

## Step:1 Install dependencies:

```
pip install -r requirements.txt
```

## Step:2 Create postgres database and update `app/database.py` file 
<br>

## Step3: Create .env and update .env file. 
#### Take refrence from app/.example.env file
<br>

## Step:3 run server:
```
uvicorn app.main:app --reload



INFO:     Will watch for changes in these directories
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [23870] using watchgod
INFO:     Started server process [23872]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

## To see the APIs documentation: http://localhost:8000/docs

<br> <br>

# Start project with docker:

```
docker-compose up
```

## Run the test cases:
``` 
pytest
```