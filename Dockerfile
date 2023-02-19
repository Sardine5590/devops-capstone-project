FROM python:3.9-slim

# CREATE WORKING DIRECTORY AND INSTALL DEPENDENCIES
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# COPY APP
COPY service/ ./service/

# Switch to a non-root user
RUN useradd --uid 1000 theia && chown -R theia /app
USER theia

# RUN IT
EXPOSE 8080
CMD ["gunicorn", "--bind=0.0.0:8080", "--log-level=info", "service:app"]