import re
import datetime
import requests
import sillyorm


class Kiwi(sillyorm.model.Model):
    _name = "kiwi"

    # === settings ===
    active = sillyorm.fields.Boolean()
    fallback = sillyorm.fields.Boolean()
    url = sillyorm.fields.String()
    timeout = sillyorm.fields.Integer()  # timeout in minutes (max time spent until you get kicked)
    timelimit = sillyorm.fields.Integer()  # timelimit in minutes (max time spent on the kiwi in 24h)
    hour_start = sillyorm.fields.Integer()  # starting UTC hour this kiwi can be used from (inclusive)
    hour_end = sillyorm.fields.Integer()  # ending UTC hour this kiwi can be used until (inclusive)
    notes = sillyorm.fields.Text()

    # === State-related variables ===

    state_last_update = sillyorm.fields.Datetime()
    state_alive = sillyorm.fields.Boolean()  # wether the kiwi is reachable
    state_usage = sillyorm.fields.Float()  # how many free slots the kiwi has (value from 0 to 100%)
    state_snr = sillyorm.fields.Float()  # HF only SNR

    times_used = sillyorm.fields.One2many("kiwi_timeslot", "kiwi")

    def get_status(self):
        for record in self:
            print(f"getting kiwi status for '{record.url}'")
            record.state_last_update = datetime.datetime.now(datetime.UTC).replace(tzinfo=None)
            record.state_alive = False
            try:
                # TODO: try and use multiple threads for this, as this takes forever with a large list to go through
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

    def get_tune_url(self, freq, mode, bps, bpe, zoom, colormap, volume):
        self.ensure_one()
        return f"{self.url}/?f={freq}{mode}z{zoom}&pb={bps},{bpe}&cmap={colormap}&vol={volume}"

    def get_last_used(self):
        self.ensure_one()
        times = [t.end if t.end is not None else t.start for t in self.times_used if t.start is not None or t.end is not None]
        times.sort(reverse=True)
        return times[0] if len(times) != 0 else None
    
    def get_used_24h_mins(self):
        self.ensure_one()
        t_utc = datetime.datetime.now(datetime.UTC).replace(tzinfo=None) - datetime.timedelta(hours=24)
        times = [(t.end - t.start).total_seconds() / 60 for t in self.times_used if t.start is not None and t.end is not None and t.start >= t_utc]
        return sum(times)

    def choose_best(self):
        records = self.env["kiwi"].search([("active", "=", True), "|", ("fallback", "=", True)])
        t_utc = datetime.datetime.now(datetime.UTC).replace(tzinfo=None)
        def rate_kiwis(kiwis, is_fallback=False):
            if not is_fallback:
                kiwis = list(filter(lambda x: t_utc.hour >= x[0].hour_start and t_utc.hour <= x[0].hour_end, kiwis))
            for i, (kiwi, _) in enumerate(kiwis):
                last_used = (t_utc - k_last_used).total_seconds() / 60 if (k_last_used := kiwi.get_last_used()) is not None else 0
                score = (
                    kiwi.state_snr * 1  # SNR score multiplier
                    + (1 - (kiwi.state_usage/100)) * 20  # usage score multiplier (usage is value 0 - 1 1 being lowest usage)
                    + last_used * 1  # time score multiplier (time is minutes passed since kiwi was last used)
                )
                if is_fallback:
                    pass  # TODO: rate the time
                kiwis[i][1] = score
            kiwis.sort(key=lambda x: x[1], reverse=True)
            return kiwis

        records.get_status()
        records = [k for k in records if k.state_alive and (k.timelimit == 0 or (k.timelimit - k.get_used_24h_mins()) > 5)]
        kiwis = rate_kiwis([[k, 0] for k in records if k.active])
        print(kiwis)
        if len(kiwis) == 0:
            kiwis = rate_kiwis([[k, 0] for k in records if k.fallback], True)
            print(kiwis)
            if len(kiwis) == 0:
                return None

        return kiwis[0][0]

class KiwiTimeslot(sillyorm.model.Model):
    _name = "kiwi_timeslot"

    start = sillyorm.fields.Datetime()
    end = sillyorm.fields.Datetime()
    kiwi = sillyorm.fields.Many2one("kiwi")
