import { TimeSpan } from "./timespan.ts";

// https://dmitripavlutin.com/timeout-fetch-request/
async function getRequestAsync(url: string, timeout: number) {
    const controller = new AbortController();
    const to = setTimeout(() => controller.abort(), timeout);

    const response = await fetch(url, { signal: controller.signal });
    clearTimeout(to);

    if (response.status >= 200 && response.status < 300) {
        return response.text();
    }
    throw new Error("failed GET request");
}

interface kiwistatus {
    alive: boolean;
    usage: number; // 0-1 (1 being full)
    snr: number;
}

// kiwibaseurl format: http://kiwi.com:8073/
async function probeKiwi(kiwibaseurl: string, timeout: number) {
    let kiwiobj: kiwistatus = { alive: false, usage: 0, snr: 0 };
    try {
        let resp = await getRequestAsync(kiwibaseurl + "status", timeout);
        let map = new Map();
        for (const match of resp.matchAll(/(.*)=(.*)/g)) {
            map.set(match[1], match[2]);
        }
        if (map.size > 0) {
            kiwiobj.alive = (map.get("status") != "offline") && (map.get("offline") != "yes");
            kiwiobj.usage = parseInt(map.get("users")) / parseInt(map.get("users_max"));
            kiwiobj.snr = parseInt(map.get("snr").split(",")[1]); // HF only SNR
        }
    } catch (err) {
        kiwiobj.alive = false;
    }
    return kiwiobj;
}

export interface kiwiConfig {
    timeout: TimeSpan; // timeout when probing kiwi
    scoreSNRMult: number; // SNR score multiplier
    scoreUsageMult: number; // usage score multiplier (usage is value 0 - 1 1 being lowest usage)
    scoreTimeMult: number; // time score multiplier (time is minutes passed since SDR last used)
    usageDisallowTolerance: TimeSpan, // kiwi cannot be used when there is less than x time left
}

export class kiwi {
    constructor(config: kiwiConfig, url: string, timelimit: TimeSpan, // 24 hour time limit - zero for infinite
        timeout: TimeSpan, // how long a kiwi may be used at a time - zero for infinite
        lastused: Date = new Date(0), // when the kiwi has been used the last time
        usetimes: Array<{ t: Date, len: TimeSpan }> = [], // times when the kiwi has been used
    ) {
        this._config = config;
        this._url = url;
        this._timelimit = timelimit;
        this._timeout = timeout;
        this._lastused = lastused;
        this._usetimes = usetimes;

        this._status = { alive: false, usage: 0, snr: 0 };
        this._statusLastRefresh = new Date(0);

        this._score = Number.MIN_VALUE;
    }

    private async refreshStatus(force: boolean = false) {
        if (TimeSpan.fromDateDiff(this._statusLastRefresh, new Date()).minutes > 5 || force) {
            this._status = await probeKiwi(this._url, this._config.timeout.milliseconds);
            this._statusLastRefresh = new Date();
        }
    }

    private async getLeftoverUseTimeI() {
        if (this._timelimit.milliseconds == 0) {
            return TimeSpan.fromDays(365);
        }

        this._usetimes = this._usetimes.filter((item) => { return (item.t.getTime() + item.len.milliseconds) >= (Date.now() - (24 * 60 * 1000)); });

        let totaluse: TimeSpan = new TimeSpan(0);
        for (const t of this._usetimes) {
            totaluse.add(t.len);
        }
        return TimeSpan.sub(this._timelimit, totaluse);
    }

    public hasTimelimit() {
        return this._timelimit.milliseconds != 0;
    }

    public async getLeftoverUseTime() {
        if (!this.hasTimelimit()) {
            throw new Error("cannot getLeftoverUseTime() if kiwi has no time limit");
        }
        return this.getLeftoverUseTimeI();
    }

    public async isUsable() {
        await this.refreshStatus();
        let leftoverT = await this.getLeftoverUseTimeI();
        return this._status.alive && this._status.usage != 1 && leftoverT.milliseconds > this._config.usageDisallowTolerance.milliseconds;
    }

    public async getScore() {
        await this.refreshStatus();
        if (!await this.isUsable()) {
            this._score = Number.MIN_VALUE;
            return Number.MIN_VALUE;
        }

        let score: number = this._status.snr * this._config.scoreSNRMult;
        score += (1 - this._status.usage) * this._config.scoreUsageMult;
        score += (TimeSpan.fromDateDiff(this._lastused, new Date()).minutes) * this._config.scoreTimeMult;
        this._score = Math.round(score);
        return this._score;
    }

    // only works after getScore() has been called!
    public getScoreSync() {
        return this._score;
    }

    public async getMaxUseTime(plannedUseTime: TimeSpan) {
        let leftover = await this.getLeftoverUseTimeI();
        let tltime = plannedUseTime.milliseconds;
        if (this._timelimit.milliseconds != 0) {
            tltime = Math.min(leftover.milliseconds, plannedUseTime.milliseconds);
        }
        let totime = plannedUseTime.milliseconds;
        if (this._timeout.milliseconds != 0) {
            totime = Math.min(this._timeout.milliseconds, plannedUseTime.milliseconds);
        }

        return TimeSpan.fromMilliseconds(Math.min(tltime, totime));
    }

    // returns false if kiwi is not usable
    public async useNow(length: TimeSpan) {
        await this.refreshStatus(true);
        if (!await this.isUsable()) {
            return false;
        }
        this._lastused = new Date();
        this._usetimes.push({ t: new Date(), len: length });
        return true;
    }

    private _config: kiwiConfig;
    private _url: string;
    private _timelimit: TimeSpan;
    private _timeout: TimeSpan;

    private _status: kiwistatus;
    private _statusLastRefresh: Date;

    private _lastused: Date;
    private _usetimes: Array<{ t: Date, len: TimeSpan }>;

    private _score: number;

    public get url(): string {
        return this._url;
    }

    public get snr(): number {
        if (!this._status.alive) {
            throw new Error("cannot get SNR if kiwi is not alive");
        }
        return this._status.snr;
    }

    public get usagePercent(): number {
        if (!this._status.alive) {
            throw new Error("cannot get usage if kiwi is not alive");
        }
        return this._status.usage * 100;
    }
}

export async function getBestKiwi(kiwiarr: Array<kiwi>) {
    if (kiwiarr.length == 0) {
        throw new Error("no receivers in array");
    }

    // compute scores for all kiwis
    await Promise.all(kiwiarr.map(async k => {
        await k.getScore();
    }));

    // sort kiwis by score
    kiwiarr.sort((a, b) => {
        if (a.getScoreSync() < b.getScoreSync()) {
            return 1;
        } else if (a.getScoreSync() > b.getScoreSync()) {
            return -1;
        }
        return 0; // equal
    });

    if (!await kiwiarr[0].isUsable()) {
        throw new Error("all receivers unusable");
    }

    console.log("receiver ranking:");
    for (const k of kiwiarr) {
        console.log(`    -> score ${k.getScoreSync()} | ${k.snr}dB SNR | ${k.usagePercent}% usage | ${k.url}`);
    }

    return kiwiarr[0];
}
