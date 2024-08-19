import os, re
from datetime import datetime

import requests
from flask import Blueprint
from flask import request
from flask import jsonify

from src.controllers.logs_controllers import LogsController
from src.configs.auth import token_required


def api_router(db, model_plate):
    router = Blueprint("api_router", __name__, url_prefix="/api")
    controller = LogsController(db, model_plate)

    @router.post("/")
    @token_required
    def create_log():
        file = request.files.get("file")
        path = os.path.join(os.path.dirname(__file__), "uploads", file.filename)
        file.save(path)
        log = None

        try:
            kwargs = dict(
                path=path,
                ias=["plate"],
                identifier=request.form.get("identifier"),
                plate=request.form.get("plate"),
                thumbs=request.form.get("thumbs") == "true",            
            )

            log = controller.create_log(**kwargs)
            os.remove(path)

        finally:
            if log:
                return jsonify(log.to_json())

            return {"error": "Falha ao consultar imagem"}, 500


    @router.post("/autovist/")
    @token_required
    def autovist():
        log = None
        data = {
            "identifier": request.json.get("identifier"),
            "plate": request.json.get("plate"),
            "url": request.json.get("url"),
            "ias": ["plate"],
            "thumbs": False,
            "start": datetime.now(),
        }

        try:
            response = requests.get(data["url"])

            foto_pattern = re.compile('(?<=com/)(.*)(?=\?X)')
            filename = foto_pattern.search(data["url"]).group().split("/")[-1]
            path = os.path.join(os.path.dirname(__file__), "uploads", filename)

            with open(path, 'wb') as f:
                f.write(response.content)

            kwargs = dict(path=path, **data)
            log = controller.create_log(**kwargs)

            os.remove(path)

        except Exception as exc:
            print(exc)

        finally:
            if log:
                return jsonify(log.to_json())

            return {"error": "Falha ao consultar imagem"}, 500


    return router
