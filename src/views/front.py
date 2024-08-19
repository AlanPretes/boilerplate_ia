import os
from datetime import datetime

from flask import Blueprint
from flask import render_template
from flask import redirect
from flask import request
from flask import url_for

from src.controllers.logs_controllers import LogsController
from src.configs.auth import basic_auth
from src.configs.logger import logger


def front_router(db, model_plate):
    router = Blueprint("front_router", __name__)
    controller = LogsController(db, model_plate)

    @router.get("/")
    @basic_auth.required
    def index():
        logger.info("Acesando endpoint index...")

        page = request.args.get("page", 1)
        logs = controller.list_logs(page=page)

        logger.info("Logs carregados com sucesso!")

        return render_template("main.html", **{
            "logs": logs,
            "page": logs.page,
            "pages": logs.pages,
            "total": logs.total,
            "next": logs.next_num,
            "prev": logs.prev_num,
        })
    

    @router.get("/precision")
    @basic_auth.required
    def get_precision():
        results = controller.get_precision()
        return render_template("precision.html", results=results)
    

    @router.route("/new/", methods=["GET", "POST"])
    @basic_auth.required
    def new():
        if request.method == "GET":
            return render_template("new.html")
        
        start = datetime.now()
        file = request.files.get("file")
        path = os.path.join(os.path.dirname(__file__), "uploads", file.filename)
        file.save(path)

        try:
            kwargs = dict(
                path=path,
                ias=["plate"],
                identifier=request.form.get("identifier"),
                plate=request.form.get("plate"),
                thumbs=request.form.get("thumbs") == "true",   
                start=start,         
            )

            controller.create_log(**kwargs)
            os.remove(path)

        finally:
            return redirect(url_for("front_router.index"))

    return router
