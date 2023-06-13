# Welcome to this Microservice Example
*This repository is the english copy of a practical project I finished during my studies in business informatics in April 2023. The purpose of this repository is to serve as example when sharing know-how with colleagues and to provide them with a first source of practical contents that (probably?) can't be destroyed.*


# 1. Project Information, Task Description, and Goal
As part of the fourth semester of Business Informatics Data Science, a portfolio examination must be completed for the "Distributed Systems" course and submitted to the lecturer Harald Uebele. This documentation is the result of the developed program design.
The task revolves around the development of a microservice named “Optimize!”, which is supposed to determine the cheapest contiguous time period for electricity consumption using a time specification from the data of an API. The following sub-tasks need to be completed for this:
1. **Development** of the microservice in Python, Java, or Node.js. This includes:
• Provision of a REST API
• Access to another service via its REST API or use of a corresponding library
• Implementation of resilience/error tolerance, external configuration
2. Building a **container image** and deploying the microservice using **Docker**
3. **Deployment** of the microservice in **Kubernetes**
5. **Documentation** of the solution


# 2. Part I: Development of Microservice "Optimize!"
## 2.1 Structure of the application 
The microservice “Optimize!” was developed in Python and, as required, includes the provision of a REST API, access to another service called “Marketdata Simulator,” which simulates the AWATTAR Service API, as well as the implementation of resilience/error tolerance or external configuration. The centerpiece of the submitted code is the file **app.py**: this code implements the microservice “Optimize!”, which receives data in the form of JSON objects from the other API (“Marketdata Simulator”) based on a time specification made by the user and, based on this, determines the cheapest contiguous time period for electricity consumption.
The application consists of:

| Directory     | File                          | Description                                                                                                                      |
|---------------|-------------------------------|----------------------------------------------------------------------------------------------------------------------------------|
| source        | app.py                        | Source code for the microservice “Optimize!”                                                                                     |
| deployment    | marketdata.yaml optimize.yaml | Files for deployment in Kubernetes                                                                                               |
| documentation | swagger.yaml                  | File for API documentation with Swagger                                                                                          |
| n.a.          | Dockerfile                    | File for building the container image                                                                                            |
| n.a.          | .dockerignore                 | File for excluding files and directories during the Docker build process                                                         |
| n.a.          | requirements.txt              | For defining the dependencies of the project with the required Python packages and modules, as well as their respective versions |


## 2.2 Functionality of the code in app.py
**Flask** is used for the provision of the API. Therefore, after importing all the required libraries, Flask is initialized as the first step and the **data endpoint** is defined under the URL “…/api/v1/get_optimal”. To access the API of the “Marketdata Simulator”, which is secured with an API key, access is made using the two environment variables API_URL and API_KEY as follows: <br>
``API_URL = os.getenv("API_URL")``
``API_KEY = os.getenv("API_KEY")`` <br>
These variables are defined for the container in a Kubernetes cluster in the **optimize.yaml file** (Appendix 1). The two variables get their values from the Kubernetes object “ConfigMap” and “Secret”. <br> <br>
For “API_URL”, the value is fetched from the **ConfigMap** named “optimize-api-config” with the key “apiUrl”. The ConfigMap is a Kubernetes resource that stores key-value pairs for application configuration. In this case, the value for “API_URL” is read from the “apiUrl” key of the “optimize-api-config” ConfigMap. For “API_KEY”, the value is fetched from a **Secret** named “optimize-api-key” with the key “apiKey”. A Secret is a Kubernetes resource that stores sensitive information like passwords or API keys and protects them from unauthorized access. In this case, the value for “API_KEY” is read from the “apiKey” key of the “optimize-api-key” Secret.
The route “…/api/v1/get_optimal” is responsible for the main purpose of the microservice: Through the “get_best()” function, a request is sent to the API to obtain the hourly electricity data with start time, end time, and price. Here, the following different **error situations** are captured:

| Error Code    | Details                                             | Description                                                       |
|---------------|-----------------------------------------------------|-------------------------------------------------------------------|
| HTTP Code 500 | Internal Server Error                               | Problems with data retrieval from “Marketdata Simulator”          |
| HTTP Code 408 | Request Timed Out                                   | Time-out after three seconds and three retries                    |
| HTTP Code 422 | Client Error, Unprocessable Entity: API Key missing | Missing API Key during data retrieval from “Marketdata Simulator” |
| HTTP Code 401 | Client Error, Unauthorized: Invalid API Key         | Invalid API Key during data retrieval from “Marketdata Simulator” |
| HTTP Code 404 | Client Error, Not found                             | Requested resource cannot be found, e.g. incorrect URL            |

Additionally, there is a **validation** of the user request (see Table 3): in particular, whether the requested number of hours q can be fulfilled with the number of available JSON objects from the “Marketdata Simulator”: 

| Error Code    | Details                                                 | Description                                                                       |
|---------------|---------------------------------------------------------|-----------------------------------------------------------------------------------|
| HTTP Code 400 | Client Error, no hours requested                        | The number of requested q hours is either nothing or less than or equal to zero   |
| HTTP Code 400 | Client Error, requested number of hours not satisfiable | The number of requested q hours is greater than the currently available data from |

Subsequently, the cheapest time window for electricity consumption is determined by iterating through the data sets and calculating the average cheapest price in EUR/kWh for the requested q hours. The result is formatted and returned as JSON.
In addition, a **health check endpoint** is implemented under the URL ".../health", which tests the availability of the microservice. Finally, the microservice is run through the main function and listens on (Flask standard) port 5000 on all network interfaces.
Along with the initialization of Flask, Swagger is also used to easily link the **documentation of the API** with the code, which aligns with current best practices. The Swagger documentation is a standard format for documenting RESTful APIs like “Optimize!” and serves to describe available endpoints, parameters, and responses of an API. For this purpose, a so-called "Decorator" @swag_from("...") is also implemented with every defined Flask route @app.route("..."), which is used in the Swagger-Flask extension. This instructs the Flask app to read and use the Swagger document from the specified YAML file to generate the documentation for this API route.

## 2.3 12-Factor-Apps and API Documentation
The methodology and principles of the "Twelve-Factor App" are observed during the development of "Optimize!" in order to meet the objective of a scalable, performant, independent, resilient, and robust application. <br>

1. For Optimize!, there is a single **codebase**, which would serve as a basis for many deployments in case of larger development.
2. The **dependencies** were identified and explicitly declared through the file requirements.txt; these include Flask in version 2.0.0, the requests module in version 2.28.2, and flasgger in version 0.9.5. The venv is **isolated** and ignored via .dockerignore, ensuring pip installs into the project directory and not globally. It is assumed that there are no pre-existing programs or libraries.
3. “Optimize!” and its configuration are independent, allowing operation in different environments. The configuration is not programmed directly in the code, but as explained in chapters 2.1 and 4.1, the API URL is stored in the **config** as an environment variable. The use of ConfigMap and Secret allows sensitive information to be stored separately from the application, increasing security and facilitating the management of configurations.
4. The Marketdata Simulator is accessed via its API and is not part of “Optimize!”'s core function. Managing configuration files ensures that this **backing service** is easily interchangeable without affecting the application and is treated as an **external resource**.
5. There is a **separation of build, release, and run** as far as possible within the scope of a student project: the code is bundled and executed in Kubernetes.
6. “Optimize!” is executed as a stateless **process** via Flask.
7.“Optimize!” is not installed on a web or application server but is made available on a port with **Flask**.
8. **Scaling** by launching additional parallel processes is not yet implemented here, but in principle, it could be implemented with the existing application architecture: more or less performance can be provided with Kubernetes, e.g., by increasing the number of Pods, Pod size, or nodes in the cluster.
9. The API can be **stopped or restarted** at any time by Kubernetes - by stopping or restarting Pods - with Flask as a process.
10. The basis for the best possible **similarity between development and production environments** was created by implementing point 1 (Dependencies, Isolation), 3 (Config), and 4 (Backing Services).
11. The centralization of **logs** is not applicable in the context of this student project; however, logs are centrally stored in Kubernetes.
12. The separation of **admin processes** and business logic is also not applicable within the scope of this student project.
13. Through clean error handling as well as the implementation of methods for higher fault tolerance, such as timeout, retry, and exception handling, specific attention is paid to the **resilience** of “Optimize!”. <br>
Furthermore, "Optimize!" is documented in an easily accessible manner for all other developers by programmatically describing the inputs and outputs via the common **OpenAPI (Swagger)** format, explaining how the application behaves. This documentation of the Optimize! API can be accessed at any time under the path ".../apidocs".

# 3. Part II: Docker Deployment

In order for Optimize! to run on different operating systems and/or cloud platforms without additional configuration or installation, a **container** is created: This is an isolated environment in which “Optimize!” is executed along with its dependencies, without directly interacting with the host system or other containers on the same host. **Docker** is used for this purpose as an open-source platform for creating, managing, and deploying applications in containers.

## 3.1 Preparation

To build the container image, a Dockerfile is necessary. In this case, the following **Dockerfile** is created, which is based on a slim base image ("FROM") according to best practices, sets a working directory ("WORKDIR"), copies artifacts into the image ("COPY"), executes the command to build the image ("RUN"), maps a port ("EXPOSE"), and rolls out the image in the container through the start command ("CMD") (see Appendix 2).

Through the .dockerignore file, unnecessary files and directories are excluded according to best practices, which should not be included in the image. These include the “deployment” directory with the files marketdata.yaml and optimize.yaml, as well as the virtual environment venv (see Appendix 3).

## 3.2 Compilation Instructions: Building the Container Image and Starting the Container in the Network

After the preparation, the container **image** can now be built using the following command: <br>
``docker build -t optimizeapp .`` (do NOT forget the point at the end!)

Since "Optimize!" runs inside the container, it is necessary to share the same **network** with the Marketdata Simulator for communication. Use the following command to create a Docker network named “dhbw”: <br>
``docker network create dhbw``

Next, start the Marketdata Simulator in this dhbw network: <br>
``docker run --name marketdata -d -p 8080:8080 --network dhbw haraldu/marketdatasim:1``

As the next step, "Optimize!" also needs to be started within this network. Enter the following command, which runs a Docker container named “optimizeapp” on the “dhbw” network and accesses port 8000 of the host system. The container is started with the environment variables “API_KEY” and “API_URL”, where “API_KEY” is set to “12345” and “API_URL” is set to “http://marketdata:8080/v1/marketdata”. Additionally, the container is started as a background process ("detached mode") with “-d”, and port 5000 in the container is mapped to port 8000 on the host system (“-p 8000:5000”).


``docker run --name optimizeapp -d -p 8000:5000 -e API_KEY=12345 -e API_URL=http://marketdata:8080/v1/marketdata --network dhbw optimizeapp``

For **testing**, the API can now be called with the network name “marketdata”:

``curl http://marketdata:8080/v1/marketdata?apikey=12345``

This set of commands describes the process of building and running the “Optimize!” application within a Docker container, ensuring it can communicate with the Marketdata Simulator through a shared Docker network. The use of Docker containers and networks ensures that the application and its dependencies are isolated and can communicate in a controlled environment.

# Part III: Kubernetes Deployment

The container image created with Docker can now be deployed on Kubernetes using Minikube, which is a local and lightweight Kubernetes implementation. Minikube creates a VM on a local PC (in my case MacOS) and provides a simple cluster that contains only one node.

## 4.1 Preparation

After the Kubernetes cluster infrastructure is set up with Minikube and the image has been built, Kubernetes manifests in the form of YAML files are needed for a successful deployment: these contain the desired configurations and specifications of the application. In the present case, these are the following two files:
1. **marketdata.yaml**: File for creating the Marketdata Simulator Services and Deployments. (Since the YAML file is provided by the lecturer, we will not discuss it further here but focus on the self-created YAML file for "Optimize!").
2. **optimize.yaml**: File for creating the "Optimize!" Services and Deployments, including Configs and Secrets.
<br> <br>

The “**Service**” YAML (see appendix 5) with the name “optimize” and the label “app:optimize” serves to provide a stable IP address and a DNS name for Pods running “Optimize!”. For a successful definition of the Kubernetes Service, spec.selector app=optimize must match app=optimize in the Deployment. The “spec” part defines the specific settings for the service and defines a Kubernetes service named “optimize” that is available on all nodes in the cluster on port 5000 and targets all Pods that have the “app: optimize” label. The “type: NodePort” specification makes “Optimize!” available via a NodePort: this essentially reserves a static port number to allow external access to the application.
<br> <br>

The “**Deployment**” YAML describes the desired state of the configuration, also called “desired state”, and creates the ReplicaSet, which in turn creates Pod(s) based on the template.
<br>In the present case (see appendix 4), a ReplicaSet is generated and, with the template as a blueprint for Pod creation, not only the Pod label “optimize” is set, but the container in the Pod is also described with “spec”. This includes, for example, that it uses the image “optimize:veronikasp”, that the image must be locally available or is created locally in Minikube (ImagePullPolicy “Never”), and that the port, as set in the EXPOSE in the Dockerfile, is running on 5000.
<br>
Furthermore, the file configures within the specification for the environment “env” in the “readinessProbe” the sending of an HTTP GET request to the endpoint “.../health” on port 5000 to check whether the container is ready to process incoming requests. This check is initially performed 5 seconds after the container starts and then repeated every 30 seconds. Also part of the environment is the definition of the two **environment variables** “API_URL” and “API_KEY” required at runtime, which are passed to the container and initialized with the values from the ConfigMap (“optimize-api-config”) and the Secret (“optimize-api-key”). The use of environment variables centralizes configuration and secret information and makes them reusable without having to hard-code them in the container image “optimize.veronikasp”. This ensures increased flexibility and scalability of the application.

<br> <br>
As already explained in detail in chapter “2.2 How the Code in app.py Works”, the optimize.yaml consequently contains two more essential components: the **ConfigMap** for the API URL as a general parameter and the **Secret** for the API Key as a sensitive, protect-worthy content. In summary, through the functionality described in chapter 2.2, the configuration of the environment variables and their protection is ensured. However, it should be noted at this point that a Kubernetes Secret like this is not actually “secret” but only “opaque”, as the API Key within the Secret is stored as a Base64-encoded string (i.e., “MTIzNDU=” for the binary string “12345=”) and is therefore not readable for Kubernetes without decryption. For larger and publicly accessible applications, it is advisable to use additional products for managing secrets and confidential data, such as IBM Cloud Secrets Manager, AWS Secrets Manager, HashiCorp Vault, or CyberArk.

## 4.2 Compilation instructions: performing the deployment and check
After this preparation of the YAML files, you can now deploy in Kubernetes. On a Mac, Minikube should be started in a terminal window; it is advisable to also display the dashboard directly:

```
minikube start
minikube dashboard
```

In a second terminal window, the following commands can now be executed: <br>
```
eval $(minikube docker-env)
docker images
docker build -t optimize:veronikasp .
kubectl apply -f deployment/marketdata.yaml
kubectl apply -f deployment/optimize.yaml
```

Outside of Kubernetes, the URL can be displayed with Minikube using the following command, or to test the running services and call the Marketdata Simulator or "Optimize!" in the following way:
```
minikube service list
minikube service marketdata --url
minikube service optimize --url
```

The images found in the appendix document the successful deployment:
• Appendix 6: The Minikube **Dashboard** shows the two **deployments** "optimize-deployment" and "marketdata", as well as the running **Pods** with the images "optimize:veronikasp" and "haraldu/marketdatasim:1".
• Appendix 7: The **API documentation** can be viewed via the path ".../apidocs" and the two GET functions for the Data and Healthcheck endpoint can be tested.
• Appendix 8: The different paths can be called: from the call of the **get_optimal function** using the example of "q=4" for the four cheapest contiguous electricity hours, through the **health check** to the generation of a Client Error in the exemplary case of an **empty entry** of "q=" or **incorrect, negative entry** of "q=-4".

# 5. Summary and Starting the Service
In summary, a custom microservice called “Optimize!” was first developed locally, then an image was created with Docker and packed into a container, and finally the deployment in Kubernetes was carried out with Minikube. By adhering to the 12-Factor-Apps principles and best practices, "Optimize!" is a lightweight application that has been designed to operate as simply and "noiselessly" as possible - completely independent of the operating environment. <br>
To start the service, the following steps must be executed in the terminal:
```
minikube start
minikube service optimize --url
```

With the URL output and the final overview of paths provided below, the “Optimize!” service can now be used.
| Path                        | Description                  |
|-----------------------------|------------------------------|
| ".../apidocs"               | Swagger documentation of API |
| ".../health"                | Healthcheck Endpoint         |
| ".../api/v1/get_optimal?q=" | Data Endpoint                |











