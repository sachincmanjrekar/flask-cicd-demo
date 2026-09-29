import os
from itertools import count

from flask import Flask, jsonify, request

app = Flask(__name__)

_id_counter = count(1)
tasks = {}


@app.get("/health")
def health():
    return jsonify(status="ok")


@app.get("/tasks")
def list_tasks():
    return jsonify(list(tasks.values()))


@app.post("/tasks")
def create_task():
    body = request.get_json(silent=True) or {}
    title = body.get("title")
    if not title:
        return jsonify(error="title is required"), 400

    task_id = next(_id_counter)
    task = {"id": task_id, "title": title, "done": False}
    tasks[task_id] = task
    return jsonify(task), 201


@app.get("/tasks/<int:task_id>")
def get_task(task_id):
    task = tasks.get(task_id)
    if task is None:
        return jsonify(error="not found"), 404
    return jsonify(task)


@app.patch("/tasks/<int:task_id>")
def update_task(task_id):
    task = tasks.get(task_id)
    if task is None:
        return jsonify(error="not found"), 404

    body = request.get_json(silent=True) or {}
    if "title" in body:
        task["title"] = body["title"]
    if "done" in body:
        task["done"] = bool(body["done"])
    return jsonify(task)


@app.delete("/tasks/<int:task_id>")
def delete_task(task_id):
    if tasks.pop(task_id, None) is None:
        return jsonify(error="not found"), 404
    return "", 204


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)
