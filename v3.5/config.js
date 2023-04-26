// URL format: http://kiwi.com:8073/ - timeout - 24h usage limit (time limits in minutes, null means no limit)
const kiwilistDay = [
    { url: "http://kiwi4.com:8073/", timeout: null, timelimit: 60 },
    { url: "http://kiwi5.com:8073/", timeout: null, timelimit: null },
    { url: "http://kiwi6.com:8073/", timeout: 1, timelimit: 10 },
];

const kiwilistNight = [
    { url: "http://kiwi0.com:8073/", timeout: null, timelimit: 180 },
    { url: "http://kiwi1.com:8073/", timeout: null, timelimit: 1 },
    { url: "http://kiwi2.com:8073/", timeout: null, timelimit: null },
];

const reloadMinutes = 20; // max time until next reload after finding a receiver
const retryMinutes = 1; // time until retrying when finding a suitable receiver failed 

const kiwiConfig = {
    freq: "4625",
    mode: "usb",
    zoom: "11",
    startPass: "50",
    endPass: "4000",
    colormap: "1",
    volume: "180",
};

const config = {
    timeout: 2000, // timeout when probing kiwi - in milliseconds
    scoreSNRMult: 1, // SNR score multiplier
    scoreUsageMult: 20, // usage score multiplier (usage is value 0 - 1 1 being lowest usage)
    scoreTimeMult: 1, // time score multiplier (time is minutes passed since SDR last used)
    usageDisallowTolerance: 2, // kiwi cannot be used when there is less than x minutes left (value in minutes)
};