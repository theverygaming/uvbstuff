import re
import datetime
import requests
import sillyorm


class Kiwi(sillyorm.model.Model):
    _name = "kiwi"

    # === settings ===
    active = sillyorm.fields.Boolean()
    url = sillyorm.fields.String()
    timeout = sillyorm.fields.Integer()  # timeout in seconds (max time spent until you get kicked)
    timelimit = sillyorm.fields.Integer()  # timelimit in seconds (max time spent on the kiwi in 24h)
    hour_start = sillyorm.fields.Integer()  # starting UTC hour this kiwi can be used from (inclusive)
    hour_end = sillyorm.fields.Integer()  # ending UTC hour this kiwi can be used until (inclusive)
    notes = sillyorm.fields.Text()

    # === State-related variables ===

    state_last_update = sillyorm.fields.Datetime()
    state_alive = sillyorm.fields.Boolean()  # wether the kiwi is reachable
    state_usage = sillyorm.fields.Float()  # how many free slots the kiwi has (value from 0 to 1, 1 is 100%)
    state_snr = sillyorm.fields.Float()  # HF only SNR

    times_used = sillyorm.fields.One2many("kiwi_used", "kiwi")

    def get_status(self):
        for record in self:
            print(f"getting kiwi status for '{record.url}'")
            record.state_last_update = datetime.datetime.now(datetime.timezone.utc)
            record.state_alive = False
            try:
                resp = requests.get(f"{record.url}/status", timeout=2)
                resp.raise_for_status()
                match = re.findall(r"(.*)=(.*)", resp.text)
                if match is None:
                    print("  -> kiwi status in invalid format")
                    continue
                vals = {}
                for (k, v) in match:
                    vals[k] = v
                record.state_alive = vals["status"] == "active" and vals["offline"] == "no"
                record.state_usage = (int(vals["users"]) / int(vals["users_max"])) * 100
                record.state_snr = float(int(vals["snr"].split(",")[1]))  # HF only SNR

            except (requests.exceptions.RequestException, KeyError, ValueError) as e:
                record.state_alive = False
                print(f"  -> Exception caught while getting kiwi status: {repr(e)}")


class KiwiUsed(sillyorm.model.Model):
    _name = "kiwi_used"

    start = sillyorm.fields.Datetime()
    end = sillyorm.fields.Datetime()
    kiwi = sillyorm.fields.Many2one("kiwi")
