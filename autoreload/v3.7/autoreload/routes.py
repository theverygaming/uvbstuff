import flask
from silly.main import app, env, env_lock


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

        for f in ["active", "state_alive"]:
            kiwilist[i][f] = None if not kiwi[f] else str(kiwi[f])

        kiwilist[i]["edit_url"] = "/admin/kiwis/edit/" + kiwi["id"]
    return kiwilist

@app.route("/admin")
def admin_index():
    env_lock.acquire()
    try:
        return env["template"].render("admin_index", {"kiwilist": _get_kiwilist(env)})
    finally:
        env_lock.release()

@app.route("/admin/kiwis")
def admin_kiwis():
    env_lock.acquire()
    try:
        return env["template"].render("admin_kiwi_list", {"kiwilist": _get_kiwilist(env)})
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
        request = flask.request.json
        print(f"/kiwi/instruction request: {request}")
        return {
            "load": None,
            "message": {
                "color": "yellow",
                "text": "hello world!",
            }
        }
    finally:
        env_lock.release()
