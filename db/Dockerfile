FROM postgres:latest

# Set environment variables (optional, change as needed)
ENV POSTGRES_USER=quick
ENV POSTGRES_PASSWORD=123qwe

# Copy the SQL script into the container
COPY . /docker-entrypoint-initdb.d/
# Expose PostgreSQL default port
EXPOSE 5432
