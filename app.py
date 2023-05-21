import os
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

    dependency_own = check.dependency_check(fileName)

    ### 이동준 db.py 작성하세요###
    db.something(dependency_own)

    data = jsonify(
        {
            "fileName": fileName,
            "ip": ip,
            "type": fileType,
            "dependency": dependency_own,
        }
    )
    return data


if __name__ == "__main__":
    app.run(host="127.0.0.1", port="5000", debug=True)
