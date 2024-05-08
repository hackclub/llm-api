# LLM API

The API powering the Sprig LLM functionality.

# Running the project locally

In order to run the project, you will need the following already setup.

- Python 
- Postgres

After cloning the repository and `cd llm-api`, do the following

Install the dependencies with 
```shell
pip install -r requirements.txt
```


Copy the `.env.example` into a `.env` 
```shell
cp .env.example .env
```

In a new terminal window, start the postgresql server and create a new user with

```sql
CREATE USER <username> WITH ENCRYPTED PASSWORD <password>;
```
and create a database named `sprigllmtest` with
```shell
CREATE DATABASE sprigllmtest;
```
In the `.env` replace the value of `PG_DATABASE_URL` with your connection string of the form `postgresql://<username>:<password>@localhost:5432/sprigllmtest`

Start the development server with 
```shell
uvicorn main:app --reload
```

If you don't get any errors, the app should be running properly.

## CORS 
By default, localhost:3000