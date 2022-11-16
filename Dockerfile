FROM selenium/standalone-chrome:107.0-20221104

USER root
WORKDIR /app
RUN apt update && apt install python3-pip -y
RUN pip install -U pip setuptools

COPY . .
RUN pip install -e .
CMD ["python3", "./src/zimmerangebote/get_offers.py"]
