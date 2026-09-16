# pytest runs inside this container against bind-mounted source, with no rebuild between
# edits, so the image carries the test runner and not just a runtime.
FROM python:3.14-slim@sha256:ce40764625a4ff50df3548277632e7f96c4e77fe75fa848aae9885476e7df5a4
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY pytest.ini ./
COPY src ./src
ENV PYTHONPATH=/app/src
CMD ["python", "-m", "app"]
