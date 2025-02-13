	# Use the official Python 3.11 image as the base image
FROM python:3.10.13
 
# Set environment variables for configuration
ENV FLASK_APP=main.py
ENV FLASK_ENV=production
# Keep virtualenv in project
ENV PIPENV_VENV_IN_PROJECT=1
# Disable spinner for cleaner logs
ENV PIPENV_NOSPIN=1
# Hide emojis in logs
ENV PIPENV_HIDE_EMOJIS=1  

# Set the working directory inside the container
WORKDIR /app
VOLUME ["/app/data"]
 
RUN apt-get update && apt-get install -y \
    libgeos-dev \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install pipenv
RUN pip install --no-cache-dir pipenv

# Copy Pipfile and Pipfile.lock
COPY Pipfile Pipfile.lock ./

# Install dependencies using pipenv
RUN pipenv install --deploy --system 

COPY . /app

RUN chmod +x start.sh

EXPOSE 8080

CMD ["./start.sh"]



# COPY requirements.txt /app/
# RUN pip install --no-cache-dir -r requirements.txt --no-deps && \
#     pip install --no-cache-dir -r requirements.txt

# COPY . /app

# RUN chmod +x start.sh

# EXPOSE 8080

# CMD ["./start.sh"]


#     # Copy the project files to the working directory
# COPY . /app

# RUN apt-get update && apt-get install -y \
#     libgeos-dev
# # Install the project dependencies
# # RUN pip install --no-cache-dir -r requirements.txt

# COPY requirements.txt /app/
# RUN pip install --no-cache-dir -r requirements.txt --no-deps && \
#     pip install --no-cache-dir -r requirements.txt



# RUN pip install --no-cache-dir -r requirements.txt
# # anthropic package is not installed with the previous command
# RUN pip install --no-cache-dir anthropic
# RUN pip install --no-cache-dir vertexai

# # Ensure the start script is executable
# RUN chmod +x start.sh

# # Expose the port on which the Flask app will run
# EXPOSE 8080
 
# # Run the Flask app when the container starts
# # CMD ["flask", "--app", "main.py", "run", "--host=0.0.0.0"]
# CMD ["./start.sh"]

