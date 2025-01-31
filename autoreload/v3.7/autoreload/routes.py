import datetime
import flask
from silly.main import env, env_lock
from silly import http

status = {
    "url": None,
    "timeslot": None,
    "kiwiconf": {
        "freq": "4625",
        "mode": "usb",
        "zoom": "11",
        "bps": "50",
        "bpe": "4000",
        "colormap": "1",
        "volume": "180",
    }
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
                status["url"] = kiwi.get_tune_url(**status["kiwiconf"])
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
            print(f"/kiwi/instruction request: {request} - current status: {status}")

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
