from flask import Flask, jsonify, request
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import time

app = Flask(__name__)

REQUEST_COUNT = Counter(
    "flask_http_request_total", "Total HTTP requests", ["method", "endpoint", "status"]
)

REQUEST_LATENCY = Histogram(
    "flask_http_request_duration_seconds", "HTTP request latency", ["endpoint"]
)


@app.before_request
def start_timer():
    from flask import g

    g.start_time = time.time()


@app.after_request
def record_metrics(response):
    from flask import g, request

    latency = time.time() - g.start_time
    REQUEST_COUNT.labels(
        method=request.method, endpoint=request.path, status=response.status_code
    ).inc()
    REQUEST_LATENCY.labels(endpoint=request.path).observe(latency)
    return response


@app.route("/metrics")
def metrics():
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}


tasks = []
VALID_PRIORITIES = ["low", "medium", "high"]


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "version": "1.0.0"})


@app.route("/tasks", methods=["GET"])
def get_tasks():
    return jsonify({"tasks": tasks, "count": len(tasks)})


@app.route("/tasks", methods=["POST"])
def create_task():
    data = request.get_json()
    if not data or "title" not in data:
        return jsonify({"error": "title is required"}), 400
    priority = data.get("priority", "medium")
    if priority not in VALID_PRIORITIES:
        return jsonify({"error": f"priority must be one of {VALID_PRIORITIES}"}), 400
    task = {
        "id": len(tasks) + 1,
        "title": data["title"],
        "done": False,
        "priority": priority,
    }
    tasks.append(task)
    return jsonify(task), 201


@app.route("/tasks/<int:task_id>", methods=["PUT"])
def update_task(task_id):
    task = next((t for t in tasks if t["id"] == task_id), None)
    if not task:
        return jsonify({"error": "task not found"}), 404
    task["done"] = request.get_json().get("done", task["done"])
    return jsonify(task)


@app.route("/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    task = next((t for t in tasks if t["id"] == task_id), None)
    if not task:
        return jsonify({"error": "task not found"}), 404
    tasks.remove(task)
    return jsonify({"message": "task deleted"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
