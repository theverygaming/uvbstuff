
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
        kiwimap.set(kiwi, kiwiobj);
    }));
}

async function getBestKiwi(config, kiwimap) {
    await rateKiwis(config, kiwimap);
    let kiwiarr = Array.from(kiwimap, ([key, value]) => ({ key, value }));
    kiwiarr = kiwiarr.filter((item) => { return item.value.score != Number.MIN_SAFE_INTEGER; });
    kiwiarr.sort((a, b) => {
        if (a.value.score < b.value.score) {
            return 1;
        } else if (a.value.score > b.value.score) {
            return -1;
        }
        return 0; // equal
    });

    if (kiwiarr.length == 0) {
        return null;
    }

    console.log("kiwi ranking:");
    for (const k of kiwiarr) {
        console.log(`    -> ${k.value.score} ${k.key}`);
    }

    return kiwiarr[0].key;
}

function initAutoreloadMap(urls) {
    let kiwimap = new Map();
    for (const url of urls) {
        kiwimap.set(url, { info: null, score: Number.MIN_SAFE_INTEGER, lastused: Date.now() / 60000 });
    }
    return kiwimap;
}
