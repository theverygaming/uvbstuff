# SPDX-License-Identifier: AGPL-3.0-only
import logging
import datetime
import flask
from silly.main import env, env_lock
from silly import http

_logger = logging.getLogger(__name__)

status = {
    "url": None,
    "timeslot": None,
}

class AutoreloadRouter(http.Router):
    @http.route("/")
    def index(self):
        env_lock.acquire()
        try:
            return env["template"].render("autoreload.template_index", {})
        finally:
            env_lock.release()

    @http.route("/kiwi")
    def kiwi_index(self):
        env_lock.acquire()
        try:
            return env["template"].render("autoreload.template_kiwi_index", {})
        finally:
            env_lock.release()

    @http.route("/kiwi/instruction", methods=["POST"])
    def kiwi_instruction(self):
        env_lock.acquire()
        try:
            def find_new_kiwi():
                kiwi = env["kiwi"].choose_best()
                if kiwi is None:
                    status["url"] = None
                    status["timeslot"] = None
                    return False
                status["url"] = kiwi.get_tune_url(**{
                    "freq": env["settings_setting"].get_value("autoreload.kiwi_freq", error=True),
                    "mode": env["settings_setting"].get_value("autoreload.kiwi_mode", error=True),
                    "zoom": env["settings_setting"].get_value("autoreload.kiwi_zoom", error=True),
                    "bps": env["settings_setting"].get_value("autoreload.kiwi_band_start", error=True),
                    "bpe": env["settings_setting"].get_value("autoreload.kiwi_band_end", error=True),
                    "colormap": env["settings_setting"].get_value("autoreload.kiwi_colormap", error=True),
                    "volume": env["settings_setting"].get_value("autoreload.kiwi_volume", error=True),
                })
                tnow = datetime.datetime.now(datetime.UTC).replace(tzinfo=None)
                status["timeslot"] = env["kiwi_timeslot"].create({
                    "kiwi": kiwi.id,
                    "start": tnow,
                    "end": tnow,
                })
                return True
            
            def load_new_kiwi():
                if not find_new_kiwi():
                    return {
                        "load": None,
                        "message": {
                            "color": "red",
                            "text": "no usable SDR found!",
                        }
                    }
                return {
                    "load": status["url"],
                    "message": {
                        "color": "green",
                        "text": "new kiwi",
                    }
                }

            request = flask.request.json
            _logger.info("/kiwi/instruction request: %s - current status: %s", request, status)

            # Is the client not showing anything or do we not know what the client is doing?
            if request["iframeContent"] == "" or (request["iframeContent"] != status["url"] and status["url"] is None):
                return load_new_kiwi()

            if request["iframeContent"] == status["url"]:
                status["timeslot"].end = datetime.datetime.now(datetime.UTC).replace(tzinfo=None)
                mins_left_limit = timelimit - status["timeslot"].kiwi.get_used_24h_mins() if (timelimit := status["timeslot"].kiwi.timelimit) != 0 else None
                mins_active = (status["timeslot"].end - status["timeslot"].start).total_seconds() / 60
                mins_left_timeout = status["timeslot"].kiwi.timeout - mins_active
                mins_left = min(mins_left_limit, mins_left_timeout) if mins_left_limit is not None else mins_left_timeout
                if mins_left <= 1.5:
                    return load_new_kiwi()
                return {
                    "message": {
                        "color": "green",
                        "text": f"reload in: {int(mins_left)}min",
                    }
                }

            if request["iframeContent"] != status["url"] and status["url"] is not None:
                status["timeslot"].end = datetime.datetime.now(datetime.UTC).replace(tzinfo=None)
                return {
                    "load": status["url"],
                    "message": {
                        "color": "green",
                        "text": "URL changed",
                    }
                }

            raise Exception("unreachable!!!")
            
        finally:
            env_lock.release()
