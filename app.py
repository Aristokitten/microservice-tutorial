import datetime
import os
import requests
from flask import Flask, request, jsonify, abort
from flasgger import Swagger, swag_from

# ------------------------------------------     Flask     -----------------------------------------
# INITIALIZATION FLASK AND SWAGGER
app = Flask(__name__)
swagger = Swagger(app, template_file="../documentation/swagger.yaml")

# ------------------------------------------ Data Endpoint -----------------------------------------
# ENVIRONMENT VARIABLES
# Retrieving URL and API key as global environment variables
API_URL = os.getenv("API_URL")
API_KEY = os.getenv("API_KEY")

@app.route("/api/v1/get_optimal", methods=["GET"])
@swag_from("../documentation/swagger.yaml")
def get_best():
    # DATAREQUEST TO API AND ERRORS
    # Catching error situation 500, if Marketdata-Service does not respond, incl. three retries
    retries = 3
    response = None
    while retries > 0:
        try:
            # get-Request via composition of URL with string interpolation
            response = requests.get(f"{API_URL}?apikey={API_KEY}", timeout=3)
        except requests.exceptions.Timeout:
            retries = retries - 1
            if retries == 0:
                abort(408, description="Request timed out")
        if response is not None:
            break
    if response is None:
        abort(500, description="HTTP Code 500, Internal Server Error")
    # Catching error situations with status codes 422, 401 und 404
    if response.status_code == 422:
        abort(422, description={"Client Error": "Unprocessable Entity, API Key missing"})
    elif response.status_code == 401:
        abort(401, description={"Client Error": "Unauthorized, Invalid API Key"})
    elif response.status_code == 404:
        abort(404, description={"Client Error": "Not Found"})

    electricity_data = response.json()["data"]

    # VALIDATION OF USER REQUEST Q
    # Testing the request for usefulness
    try:
        q = int(request.args.get("q"))
    except ValueError:
        return jsonify({"Client Error": "No hours requested"}), 400
    if q <= 0:
        return jsonify({"Client Error": "No hours requested"}), 400
    # Testing the feasibility of the request against the availability of JSON objects
    if len(electricity_data) < q:
        return jsonify({"Client Error": "Requested number of hours not satisfiable"}), 400

    # BEST TIME HORIZON
    # Calculation of the q most favorable contiguous hours using a loop over d data sets
    best_sum = float("inf")
    for i in range(len(electricity_data) - q + 1):
        sum_marketprices = sum(d["marketprice"] for d in electricity_data[i:i + q])
        if sum_marketprices < best_sum:
            best_sum = sum_marketprices
            start = electricity_data[i]["start_timestamp"] / 1000
            start_readable = datetime.datetime.fromtimestamp(start)

        # Formatting result
        avg_price = round((best_sum / q) / 1000, 4)
        result = {
            'start': start_readable,
            'duration': q,
            'avg_price': avg_price
        }
        # RETURNING RESULT
        return jsonify(result)

# ------------------------------------------ Healthcheck Endpoint -----------------------------------------
# Zum Test, ob der Microservice verfügbar ist
@app.route("/health", methods=["GET"])
@swag_from("../documentation/swagger.yaml")
def healthcheck():
    return jsonify({'status': 'UP'})

# -------------------------------------------- Run Application ---------------------------------------------
# RUNNING FLASK
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
