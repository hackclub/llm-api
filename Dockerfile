FROM ubuntu:22.04

RUN apt-get update

# install the python runtime and pip

RUN apt-get install -y python3 python3-pip libpq-dev --fix-missing
# END install python runtime

WORKDIR /app

COPY requirements.txt . 

RUN pip3 install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--reload", "--host", "0.0.0.0"]