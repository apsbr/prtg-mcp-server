FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MCP_TRANSPORT=streamable-http \
    MCP_HOST=0.0.0.0 \
    MCP_PORT=8000 \
    MCP_STATELESS_HTTP=true

WORKDIR /app

COPY pyproject.toml README.md ./
COPY server.py ./

RUN pip install --no-cache-dir .

EXPOSE 8000

CMD ["python", "server.py"]
