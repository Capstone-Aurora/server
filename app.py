import os
import sys
from flask_cors import CORS
from flask import Flask, jsonify, request

import check
import db


app = Flask(__name__)
app.config["DEBUG"] = True
CORS(app)


@app.route("/file_send", methods=["POST"])
def file_send():
    file = request.files.get("file")
    ip = request.headers.get("ip")

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


@app.route("/get_dependency", methods=["POST"])
def get_dependency():
    fileName = request.args.get("fileName")
    # dependency_own = check.dependency_check(fileName)
    dependency_own = fileName

    ### 이동준 db.py 작성하세요###
    # db.something(dependency_own)
    return jsonify({"dependency": dependency_own})


@app.route("/get_detail", methods=["GET"])
def get_detail():
    fileName = request.args.get("dependency_own")
    detail = db.get_detail(fileName)
    return jsonify({"detail": detail})


@app.route("/get_tree_png", methods=["GET"])
def get_tree_png():
    fileName = request.args.get("dependency_own")
    tree_png = db.get_tree_png(fileName)
    return jsonify({"tree_png": tree_png})


@app.route("/get_vuln", methods=["GET"])
def get_vuln():
    fileName = request.args.get("fileName")
    vuln = db.get_vuln(fileName)
    return jsonify({"vuln": vuln})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port="5000", debug=True)
