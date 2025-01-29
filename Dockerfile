FROM python:3.12

# Set the working directory in the container
WORKDIR /app

# Install python-dev
RUN apt-get update && apt-get install -y python3-dev libsasl2-dev libldap2-dev libssl-dev

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Expose the Flask app port
EXPOSE 5000

# Set environment variables for Flask app
ENV FLASK_APP=upload_handler.py
ENV FLASK_RUN_HOST=0.0.0.0

# Start the Flask app
CMD ["flask", "run"]
