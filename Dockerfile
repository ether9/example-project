FROM python:3.11-slim

WORKDIR /app

# Copy the server script (full load simulation server)
COPY server.py .

EXPOSE 8080

# Run python with -u (unbuffered) so prints flush to logs in real-time
CMD ["python", "-u", "server.py"]