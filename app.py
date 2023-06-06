import os
import json
import requests
from flask_cors import CORS
from flask import Flask, jsonify, request

import check
import flow

app = Flask(__name__)
app.config["DEBUG"] = True
CORS(app)


@app.route("/file_send", methods=["POST"])
def file_send():
    file = request.files.get("file")
    ip = request.headers.get("ip")
    print("ip: ", ip)

    dir_path = os.path.dirname(os.path.realpath(__file__))
    dir_path = dir_path + "/data"
    if not os.path.isdir(dir_path):
        os.mkdir(dir_path)
    fileName = file.filename
    fileType = fileName.split(".")[1]

    saved_file_path = os.path.join(dir_path, fileName)
    file.save(saved_file_path)

    data = jsonify(
        {
            "fileName": fileName,
            "ip": ip,
            "type": fileType,
        }
    )
    return data


@app.route("/dependency", methods=["POST"])
def dependency():
    fileName = request.form.get("fileName")
    dependency_own = check.dependency_check(fileName)
    print("/dependency success: ", dependency_own)
    return jsonify({"dependency": dependency_own})


@app.route("/version", methods=["POST"])
def version():
    fileName = request.form.get("fileName")
    versionList = request.form.get("versionList")
    data = {"file": versionList}
    res = requests.post(
        "http://pwnable.co.kr:42598/SearchDep/",
        data=json.dumps(data),
        headers={
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
    )
    print("/version success : ", versionList, res.text)

    return jsonify({"fileName": fileName, "res": res.text})


@app.route("/vulnerability", methods=["POST"])
def vulnerability():
    fileName = request.form.get("fileName")
    module_name = request.form.get("module_name")
    module_version = request.form.get("module_version")

    data = {"name": module_name, "version": module_version}
    res = requests.post(
        "http://pwnable.co.kr:42598/SearchVuln/",
        data=json.dumps(data),
        headers={
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
    )
    print("/vulnerability success : ", module_name, module_version)
    print(res.text)

    return jsonify({"fileName": fileName, "res": res.text})


@app.route("/get_example_flow", methods=["POST"])
def get_example_flow():
    fileNum = int(request.form.get("fileNum"))

    result = flow.get_flow(fileNum)
    return jsonify({"fileNum": fileNum, "result": result})


@app.route("/")
def hello_world():
    """Example Hello World route."""
    name = os.environ.get("NAME", "World")
    return f"Hello {name}!"


if __name__ == "__main__":
    # app.run(host="0.0.0.0", port="5000", debug=True)
    app.run(host="127.0.0.1", port="5000", debug=True)
