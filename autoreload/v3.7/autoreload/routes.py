import datetime
import flask
from silly.main import app, env, env_lock


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


@app.route("/")
def index():
    env_lock.acquire()
    try:
        return env["template"].render("index", {})
    finally:
        env_lock.release()


def _get_kiwilist(env, kiwis=None):
    if kiwis is None:
        kiwis = env["kiwi"].search([])
    kiwilist =  kiwis.read([
        "id",
        "active",
        "fallback",
        "url",
        "timeout",
        "timelimit",
        "hour_start",
        "hour_end",
        "notes",
        "state_last_update",
        "state_alive",
        "state_usage",
        "state_snr",
    ])

    for i, kiwi in enumerate(kiwilist):
        for f in ["id", "timeout", "timelimit", "hour_start", "hour_end", "state_usage", "state_snr"]:
            kiwilist[i][f] = str(kiwi[f])

        for f in ["active", "fallback", "state_alive"]:
            kiwilist[i][f] = None if not kiwi[f] else str(kiwi[f])

        kiwilist[i]["edit_url"] = "/admin/kiwis/edit/" + kiwi["id"]
        kiwilist[i]["used_mins_24h"] = str(int(env["kiwi"].browse(kiwi["id"]).get_used_24h_mins()))
    return kiwilist

def _get_kiwi_tslist(env):
    tsr = env["kiwi_timeslot"].search([])
    tslist =  tsr.read([
        "kiwi",
        "start",
        "end",
    ])
    tslist.sort(key=lambda x: str(x["end"]), reverse=True)
    for i, ts in enumerate(tslist):
        for f in ["start", "end"]:
            tslist[i][f] = str(ts[f])
        tslist[i]["url"] = env["kiwi"].browse(ts["kiwi"]).url
    return tslist

@app.route("/admin")
def admin_index():
    env_lock.acquire()
    try:
        return env["template"].render("admin_index", {"status": status, "kiwilist": _get_kiwilist(env), "tslist": _get_kiwi_tslist(env)})
    finally:
        env_lock.release()

@app.route("/admin/kiwis")
def admin_kiwis():
    env_lock.acquire()
    try:
        return env["template"].render("admin_kiwi_list", {"kiwilist": _get_kiwilist(env)})
    finally:
        env_lock.release()

@app.route("/admin/tslist")
def admin_tslist():
    env_lock.acquire()
    try:
        return env["template"].render("admin_kiwi_ts_list", {"tslist": _get_kiwi_tslist(env)})
    finally:
        env_lock.release()

@app.route("/admin/kiwis/edit/new")
def admin_kiwis_edit_create():
    env_lock.acquire()
    try:
        kiwi = env["kiwi"].create({})
        return env["template"].render("admin_kiwi_edit", {
            "kiwi": _get_kiwilist(env, kiwi)[0],
        })
    finally:
        env_lock.release()

@app.route("/admin/kiwis/edit/<int:kiwi_id>", methods=["GET", "POST", "DELETE"])
def admin_kiwis_edit(kiwi_id):
    env_lock.acquire()
    try:
        kiwi = env["kiwi"].browse(kiwi_id)
        if flask.request.method == "DELETE":
            kiwi.delete()
            resp = flask.Response("you should be redirected")
            resp.headers["HX-Redirect"] = "/admin"
            return resp
        if flask.request.method == "POST":
            kiwi.active = bool(flask.request.form.get("active"))
            kiwi.fallback = bool(flask.request.form.get("fallback"))
            kiwi.url = flask.request.form["url"]
            for k in ["timeout", "timelimit", "hour_start", "hour_end"]:
                val = flask.request.form[k]
                if val == "":
                    val = 0
                kiwi.write({k: int(val)})
            kiwi.notes = flask.request.form["notes"]
            resp = flask.Response("you should be redirected")
            resp.headers["HX-Redirect"] = "/admin"
            return resp
        return env["template"].render("admin_kiwi_edit", {
            "kiwi": _get_kiwilist(env, kiwi)[0],
        })
    finally:
        env_lock.release()

@app.route("/kiwi")
def kiwi_index():
    env_lock.acquire()
    try:
        return env["template"].render("kiwi_index", {})
    finally:
        env_lock.release()

@app.route("/kiwi/instruction", methods=["POST"])
def kiwi_instruction():
    env_lock.acquire()
    try:
        def find_new_kiwi():
            kiwi = env["kiwi"].choose_best()
            if kiwi is None:
                status["url"] = None
                status["timeslot"] = None
                return False
            # TODO: url, timeslot
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
                    "text": f"time left: {int(mins_left)}min",
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
