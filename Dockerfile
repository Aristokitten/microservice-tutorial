# Using a slim base image as best practice
FROM python:3.8-slim

# Setting the working directory in the container image
WORKDIR /optimizeapp

# Copying the source code in the container image
COPY . .

# Installing the dependencies specified in requirements.txt
RUN pip install -r requirements.txt

# Portmapping for connecting from outside the container
EXPOSE 5000

# Setting the working directory for COPY, ADD, RUN, CMD
WORKDIR /optimizeapp/source

# Command for running the image that is rolled out in the container
CMD ["python", "app.py"]

