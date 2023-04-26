
// https://stackoverflow.com/a/48969580
function getRequestAsync(url, timeout) {
    return new Promise(function (resolve, reject) {
        let req = new XMLHttpRequest();
        req.open("GET", url);
        req.timeout = timeout;
        req.onload = () => {
            if (req.status >= 200 && req.status < 300) {
                resolve(req.response);
            } else {
                reject({
                    status: req.status,
                });
            }
        };
        req.onerror = () => {
            reject({
                status: 0,
            });
        };
        req.ontimeout = () => {
            reject({
                status: 0,
            });
        };
        req.send();
    });
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
        let score = Number.MIN_SAFE_INTEGER;
        if (info.alive && info.usage != 1) {
            score = calcScore(config, info.usage, info.snr, kiwiobj.lastused);
        }
        kiwiobj.info = info;
        kiwiobj.score = score;
    }));
}

async function updateTimeLimits(config, kiwimap) {
    await Promise.all(Array.from(kiwimap, ([key]) => (key)).map(async kiwi => {
        console.log("->");
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
            kiwiobj.score = Number.MIN_SAFE_INTEGER;
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
    kiwiarr = kiwiarr.filter((item) => { return item.value.score != Number.MIN_SAFE_INTEGER; });
    if (kiwiarr.length == 0) {
        throw new Error("all receivers unusable");
    }

    await updateTimeLimits(config, kiwimap);
    kiwiarr = Array.from(kiwimap, ([key, value]) => ({ key, value }));
    kiwiarr = kiwiarr.filter((item) => { return item.value.score != Number.MIN_SAFE_INTEGER; });
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
        kiwimap.set(kiwi.url, { timelimit: kiwi.timelimit, timeout: kiwi.timeout, info: null, score: Number.MIN_SAFE_INTEGER, lastused: Date.now() / 60000, usetimes: [{ t: (Date.now() / 60000) - ((24 * 60)), len: 5 }, { t: (Date.now() / 60000) - ((24 * 60)), len: 1 }], leftoverusetime: null });
    }
    return kiwimap;
}
