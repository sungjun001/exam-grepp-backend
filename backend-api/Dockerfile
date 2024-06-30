# --------- requirements ---------

FROM python:3.11 as requirements-stage

WORKDIR /tmp

RUN pip install poetry

COPY ./pyproject.toml ./poetry.lock* /tmp/

RUN poetry export -f requirements.txt --output requirements.txt --without-hashes


# --------- final image build ---------
FROM python:3.11

WORKDIR /code

COPY --from=requirements-stage /tmp/requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

ENV SERVER_NAME=${SERVER_NAME}

COPY ./src/app /code/app

COPY ./scripts/set_workers.sh /scripts/set_workers.sh


# # 논리 CPU 갯수 조회 및 환경 변수 설정
# RUN apt-get update && apt-get install -yq --no-install-recommends \
#     lsb-release \
#     && apt-get clean && rm -rf /var/lib/apt/lists/*


# RUN chmod +x /scripts/set_workers.sh

# CMD ["/scripts/set_workers.sh"]


# -------- replace with comment to run with gunicorn --------
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
# CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker". "-b", "0.0.0.0:8000"]
