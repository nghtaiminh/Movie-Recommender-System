## Setup

There are two component to be noticed:

- Recommendation API
- Web server

### Settings

```bash
python3 -m pip install -r requirements.txt
```

### Database Installation

- Create a database with PostgreSQL
- Restore the database with `backup.sql` file.
### Run 

1. Start the recommendation API server:

```bash
cd recommender_api && python api.py
``` 
The server is run on 127.0.0.1:3000

2. Start the web server:

```bash
cd app && python routes.py
``` 

The server is run on 127.0.0.1:5000