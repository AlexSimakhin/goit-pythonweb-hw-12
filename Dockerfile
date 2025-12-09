FROM python:3.13-slim
WORKDIR /app

# Install app deps
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy docs and build Sphinx HTML before app mount
COPY docs/requirements.txt docs/requirements.txt
RUN pip install --no-cache-dir -r docs/requirements.txt
COPY docs/ docs/
RUN sphinx-build -b html docs docs/_build

COPY . .

EXPOSE 8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
