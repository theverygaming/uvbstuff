# SPDX-License-Identifier: AGPL-3.0-only
import logging
import re
import datetime
import requests
import sillyorm

_logger = logging.getLogger(__name__)

# TODO: allow deleting kiwis
# TODO: let the user force a reload from the admin UI

def _is_in_hour_range(start, end, hour):
    # In case of a midnight transistion in the start-end range
    if start > end:
        return hour >= start or hour <= end
    # normal case
    return hour >= start and hour <= end


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

    def get_status(self):
        for record in self:
            _logger.info("getting kiwi status for kiwi with URL %s", record.url)
            record.state_last_update = datetime.datetime.now(datetime.UTC).replace(tzinfo=None)
            record.state_alive = False
            try:
                # TODO: try and use multiple threads for this, as this takes forever with a large list to go through
                resp = requests.get(f"{record.url}/status", timeout=2)
                resp.raise_for_status()
                match = re.findall(r"(.+)=(.+)", resp.text)
                if match is None:
                    _logger.warning("  -> kiwi status in invalid format")
                    continue
                vals = {}
                for (k, v) in match:
                    vals[k] = v
                record.state_alive = vals["status"] == "active" and vals["offline"] == "no"
                # Avoid divide by zero when users_max is zero, which can be the case
                if int(vals["users_max"]) != 0:
                    record.state_usage = (int(vals["users"]) / int(vals["users_max"])) * 100
                else:
                    record.state_usage = 100.0
                record.state_snr = float(int(vals["snr"].split(",")[1]))  # HF only SNR

            except (requests.exceptions.RequestException, KeyError, ValueError) as e:
                record.state_alive = False
                _logger.error("  -> Exception caught while getting kiwi status: %s", repr(e))

    def get_tune_url(self, freq, mode, bps, bpe, zoom, colormap, volume):
        self.ensure_one()
        return f"{self.url}/?f={freq}{mode}z{zoom}&pb={bps},{bpe}&cmap={colormap}&vol={volume}"

    def get_last_used(self):
        self.ensure_one()
        times = self.env["kiwi_timeslot"].search(
            [
                ("kiwi", "=", self.id),
                "&",
                ("start", "!=", None),
                "&",
                ("end", "!=", None),
            ],
            order_by="end",
            order_asc=False,
        )
        return times[0].end if len(times) != 0 else None

    def get_used_24h_mins(self):
        self.ensure_one()
        t_utc = datetime.datetime.now(datetime.UTC).replace(tzinfo=None) - datetime.timedelta(hours=24)
        times = self.env["kiwi_timeslot"].search(
            [
                ("kiwi", "=", self.id),
                "&",
                ("start", ">=", t_utc),
                "&",
                ("start", "!=", None),
                "&",
                ("end", "!=", None),
            ],
            order_by="end",
            order_asc=False,
        )
        times = [(t.end - t.start).total_seconds() / 60 for t in times]
        return sum(times)

    def choose_best(self):
        # FIXME: this seems to choose a kiwi even if all kiwis are are 100% usage
        records = self.env["kiwi"].search([("active", "=", True), "|", ("fallback", "=", True)])
        t_utc = datetime.datetime.now(datetime.UTC).replace(tzinfo=None)
        def rate_kiwis(kiwis, is_fallback=False):
            # in case of fallback all hour constraints will be ignored
            if not is_fallback:
                kiwis = list(filter(lambda x: _is_in_hour_range(x[0].hour_start, x[0].hour_end, t_utc.hour), kiwis))
            for i, (kiwi, _) in enumerate(kiwis):
                last_used = (t_utc - k_last_used).total_seconds() / 60 if (k_last_used := kiwi.get_last_used()) is not None else 0
                score = (
                    kiwi.state_snr * 1  # SNR score multiplier
                    + (1 - (kiwi.state_usage/100)) * 20  # usage score multiplier (usage is value 0 - 1 1 being lowest usage)
                    + last_used * 1  # time score multiplier (time is minutes passed since kiwi was last used)
                )
                if is_fallback:
                    # in case of fallback all hour constraints will be ignored,
                    # it would be nice if a fallback with fitting hours would be chosen.
                    pass  # TODO: rate the time
                _logger.info(
                    "Rated kiwi with URL '%s' and ID %d - SNR: %f usage: %f%% minutes since used: %f -- score: %d",
                    kiwi.url,
                    kiwi.id,
                    kiwi.state_snr,
                    kiwi.state_usage,
                    last_used,
                    score,
                )
                kiwis[i][1] = score
            kiwis.sort(key=lambda x: x[1], reverse=True)
            return kiwis

        # FIXME: take a closer look at this stuff
        records.get_status()
        records = [k for k in records if k.state_alive and (k.timelimit == 0 or (k.timelimit - k.get_used_24h_mins()) > 5)]
        _logger.info("Rating kiwis")
        kiwis = rate_kiwis([[k, 0] for k in records if k.active])
        if len(kiwis) == 0:
            _logger.info("No usable kiwis found! Checking if there is any usable fallback ones...")
            kiwis = rate_kiwis([[k, 0] for k in records if k.fallback], True)
            if len(kiwis) == 0:
                _logger.info("No fallback kiwi found either :(")
                return None

        return kiwis[0][0]

class KiwiTimeslot(sillyorm.model.Model):
    _name = "kiwi_timeslot"

    start = sillyorm.fields.Datetime()
    end = sillyorm.fields.Datetime()
    kiwi = sillyorm.fields.Many2one("kiwi")
