ARG BASE_IMAGE=236382736970.dkr.ecr.ap-northeast-1.amazonaws.com/blpt-artifacts/python_uvicorn:latest
FROM $BASE_IMAGE

WORKDIR /src

ENV PYTHONPATH=/src

# Copy using poetry.lock* in case it doesn't exist yet
COPY pyproject.toml poetry.lock /src/

RUN poetry install --no-root

COPY . /src

# Start the server. start.sh from base image build
CMD ["/start.sh"]