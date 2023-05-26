# Use the official Python base image
FROM python:3.9.5

ENV PYTHONDONTWRITEBYTECODE 1 
ENV PYTHONBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get -y install libgdal-dev postgresql-client && \
    apt-get clean

# Install the Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the application code
COPY . .

# Start the Django development server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
