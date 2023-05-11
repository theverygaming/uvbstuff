// https://dmitripavlutin.com/timeout-fetch-request/
async function getRequestAsync(url, timeout) {
    const controller = new AbortController();
    const to = setTimeout(() => controller.abort(), timeout);

    const response = await fetch(url, { signal: controller.signal });
    clearTimeout(to);

    if (response.status >= 200 && response.status < 300) {
        return response.text();
    }
    throw new Error("failed GET request");
}

// kiwibaseurl format: http://kiwi.com:8073/
async function probeKiwi(kiwibaseurl, timeout) {
    let kiwiobj = { alive: false, usage: 0, snr: 0 };
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

function calcScore(config, usage, snr, lastused) {
    let unixmins = Date.now() / 60000;
    let score = snr * config.scoreSNRMult;
    score += ((1 - usage) * config.scoreUsageMult);
    score += (unixmins - lastused) * config.scoreTimeMult;
    return Math.round(score);
}

async function rateKiwis(config, kiwimap) {
    await Promise.all(Array.from(kiwimap, ([key]) => (key)).map(async kiwi => {
        let info = await probeKiwi(kiwi, config.timeout);
        let kiwiobj = kiwimap.get(kiwi);
        let score = -Infinity;
        if (info.alive && info.usage != 1) {
            score = calcScore(config, info.usage, info.snr, kiwiobj.lastused);
        }
        kiwiobj.info = info;
        kiwiobj.score = score;
    }));
}

async function updateTimeLimits(config, kiwimap) {
    await Promise.all(Array.from(kiwimap, ([key]) => (key)).map(async kiwi => {
        let kiwiobj = kiwimap.get(kiwi);
        if (kiwiobj.timelimit == null) {
            return;
        }
        const unixmins = Date.now() / 60000;

        kiwiobj.usetimes = kiwiobj.usetimes.filter((item) => { return (item.t + item.len) >= (unixmins - (24 * 60)); });
        let totalusemins = 0;
        for (const o of kiwiobj.usetimes) {
            totalusemins += o.len;
        }

        if ((totalusemins + config.usageDisallowTolerance) >= kiwiobj.timelimit) {
            kiwiobj.score = -Infinity;
            kiwiobj.leftoverusetime = null;
        } else {
            kiwiobj.leftoverusetime = kiwiobj.timelimit - totalusemins;
        }
    }));
}

async function getBestKiwi(config, kiwimap, plannedUseMins) {
    if (kiwimap.size == 0) {
        throw new Error("no receivers in list");
    }

    await rateKiwis(config, kiwimap);

    let kiwiarr = Array.from(kiwimap, ([key, value]) => ({ key, value }));
    kiwiarr = kiwiarr.filter((item) => { return item.value.score != -Infinity; });
    if (kiwiarr.length == 0) {
        throw new Error("all receivers unusable");
    }

    await updateTimeLimits(config, kiwimap);
    kiwiarr = Array.from(kiwimap, ([key, value]) => ({ key, value }));
    kiwiarr = kiwiarr.filter((item) => { return item.value.score != -Infinity; });
    if (kiwiarr.length == 0) {
        throw new Error("all receiver time limits exceeded");
    }

    kiwiarr.sort((a, b) => {
        if (a.value.score < b.value.score) {
            return 1;
        } else if (a.value.score > b.value.score) {
            return -1;
        }
        return 0; // equal
    });

    console.log("receiver ranking:");
    for (const k of kiwiarr) {
        console.log(`    -> ${k.value.score} ${k.key}`);
    }

    const tltime = ((kiwiarr[0].value.timelimit != null) && (kiwiarr[0].value.leftoverusetime < plannedUseMins)) ? kiwiarr[0].value.leftoverusetime : plannedUseMins;
    const totime = ((kiwiarr[0].value.timeout != null) && (kiwiarr[0].value.timeout < plannedUseMins)) ? kiwiarr[0].value.timeout : plannedUseMins;

    const url = kiwiarr[0].key;
    const time = tltime < totime ? tltime : totime;

    return { url, time };
}

function initAutoreloadMap(kiwis) {
    let kiwimap = new Map();
    for (const kiwi of kiwis) {
        kiwimap.set(kiwi.url, { timelimit: kiwi.timelimit, timeout: kiwi.timeout, info: null, score: -Infinity, lastused: Date.now() / 60000, usetimes: [], leftoverusetime: null });
    }
    return kiwimap;
}
