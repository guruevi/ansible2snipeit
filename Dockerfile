FROM python:3.13-slim

# Set the working directory in the container
WORKDIR /app

# Install python-dev
RUN apt-get update && apt-get install -y python3-dev libsasl2-dev libldap2-dev libssl-dev git build-essential

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Clean up
RUN apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy the rest of the application code into the container
COPY . .
RUN rm -f /app/settings.conf
RUN rm -rf /app/venv
RUN mkdir /app_settings
# This if for our App
RUN ln -s /app_settings/settings.conf /app/settings.conf
# Dell API seems to have this hardcoded
RUN ln -s /app_settings/settings.conf /root/secrets.ini

# Expose the Flask app port and settings file
EXPOSE 5000
VOLUME /app_settings

# Set environment variables for Flask app
ENV FLASK_ENV=production
ENV FLASK_APP=upload_handler.py
ENV FLASK_RUN_HOST=0.0.0.0

# Start the Flask app
CMD ["flask", "run"]
