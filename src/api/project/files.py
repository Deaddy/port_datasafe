import logging
import os
import json
import requests
from RDS import Util, ROParser

from lib.datasafe import Datasafe
from flask import jsonify, request, g, abort
from io import BytesIO, BufferedReader

logger = logging.getLogger()


# FIXME: all endpoints need server tests, but POST cannot currently be tested through pactman, because it only supports json as content type
def index(project_id):
    abort(500)


def get(project_id, file_id):
    abort(500)


def post(project_id):
    # trigger upload on datasafe
    req = request.get_json(force=True, silent=True, cache=True)

    if req is None:
        req = request.form.to_dict()

    logger.debug("got request body: {}", req)

    try:
        service, userId, password = Util.parseUserId(req["userId"])
        if service != "port-datasafe":
            logger.debug("got wrong service token")
            raise ValueError
    except ValueError:
        token = Util.loadToken(req["userId"], "port-datasafe")
        userId = token.user.username
        password = token.access_token

    owncloud_token = Util.loadToken(req["username"], "port-owncloud")

    data = Util.parseToken(owncloud_token)
    data.update({
        "filepath": "{}/ro-crate-metadata.json".format(req["folder"])
    })

    logger.debug("send data: {}".format(data))

    metadata = json.loads(
        BytesIO(
            requests.get(
                "http://circle1-{}/storage/file".format("port-owncloud"),
                json=data,
                verify=(os.environ.get("VERIFY_SSL", "True") == "True"),
            ).content
        )
        .read()
        .decode("UTF-8")
    )

    logger.debug("got metadata: {}".format(metadata))
    doc = ROParser(metadata)

    logger.debug("parsed metadata: {}".format(doc))

    datasafe = Datasafe(
        userId,
        owncloud_token.access_token,
        doc.getElement(doc.rootIdentifier, expand=True, clean=True),
        req["folder"],
        os.getenv("DATASAFE_PUBLICKEY"),
        os.getenv("DATASAFE_PRIVATEKEY")
    )

    logger.debug("Trigger file upload")
    success = datasafe.triggerUploadForProject()
    logger.debug(f"Finished trigger, result was: {success}")

    return jsonify({"success": success}), 200 if success else 500


def patch(project_id, file_id):
    abort(500)


def delete(project_id, file_id=None):
    abort(500)
