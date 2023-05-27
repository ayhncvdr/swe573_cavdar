#Use the official Python base image
FROM python:3.10.5

ENV PYTHONDONTWRITEBYTECODE 1 
ENV PYTHONBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get -y install gdal-bin libgdal-dev postgresql-client && \
    apt-get clean

# Install the Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY OSGeo4W/bin/gdal307.dll /OSGeo4W/bin/gdal307.dll

# Copy the application code
COPY . .

# Start the Django development server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

# Use a base image with Conda pre-installed
# FROM continuumio/miniconda3

# WORKDIR /app

# # Create the environment:
# COPY environment.yml .
# RUN conda env create -n environment.yml

# # Make RUN commands use the new environment:
# SHELL ["conda", "run", "-n", "base", "/bin/bash", "-c"]

# # Demonstrate the environment is activated:
# RUN python -c "import django"

# # The code to run when container is started:
# COPY . /app/

