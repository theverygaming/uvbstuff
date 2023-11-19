import { kiwi, kiwiConfig, getBestKiwi } from "./kiwi.ts";
import { TimeSpan } from "./timespan.ts";

import { Application, Router } from "https://deno.land/x/oak@v12.6.1/mod.ts";
import * as uuid from "https://deno.land/std@0.207.0/uuid/mod.ts";

const app = new Application();
const router = new Router();

const connectedClients = new Map();

const config: kiwi.kiwiConfig = {
    timeout: TimeSpan.fromSeconds(5), // timeout when probing kiwi
    scoreSNRMult: 1, // SNR score multiplier
    scoreUsageMult: 30, // usage score multiplier (usage is value 0 - 1 1 being lowest usage)
    scoreTimeMult: 0, // time score multiplier (time is minutes passed since SDR last used)
    usageDisallowTolerance: TimeSpan.fromMinutes(2), // kiwi cannot be used when there is less than x time left
}

const kiwis = [
    new kiwi(config, "http://192.168.2.183:8073/", TimeSpan.fromMinutes(4), TimeSpan.fromMinutes(3)),
    new kiwi(config, "http://ik7fmo.ddns.net:8073/", TimeSpan.fromMinutes(4), TimeSpan.fromMinutes(3)),
    new kiwi(config, "http://agjkjq167gptuzr9.myfritz.net:8073/", TimeSpan.fromMinutes(4), TimeSpan.fromMinutes(3))
];

let currentKiwi = null;
let currentKiwi_start = Date.now();
let currentKiwi_planned = TimeSpan.fromMilliseconds(0);

function getCurrentKiwiLeftoverUseTime() {
    const t_passed = Date.now() - currentKiwi_start;
    const t_leftover = currentKiwi_planned.milliseconds - (t_passed + TimeSpan.fromMinutes(1).milliseconds);
    return t_leftover;
}

async function getCurrentKiwi() {
    const t_passed = Date.now() - currentKiwi_start;
    const t_leftover = getCurrentKiwiLeftoverUseTime();
    if (!(currentKiwi instanceof kiwi) || t_leftover < t_passed) {
        currentKiwi = await getBestKiwi(kiwis);
        currentKiwi_planned = await currentKiwi.getMaxUseTime(TimeSpan.fromMinutes(2));
        await currentKiwi.useNow(currentKiwi_planned);
        currentKiwi_start = Date.now();
        return currentKiwi;
    }
    return currentKiwi;
}

function genKiwiUrl(kw) {
    return kw.url;
}

function errorpage(ctx: any, status: number) {
    ctx.response.status = status;
    let text = `error`;
    let title = `${status}`
    switch (status) {
        case 404:
            text = "Not Found";
            title = text;
            break;
        case 500:
            text = "Internal Server Error";
            title = text;
            break;
    }
    ctx.response.body = `<!DOCTYPE html><html><head><title>${title}</title></head><body><h1>${status} ${text}</h1></body></html>`;
}

router.get("/api/ws/status_client", async (ctx: any) => {
    try {
        const socket = await ctx.upgrade();
        socket.uuid = uuid.v1.generate();
        connectedClients.set(socket.uuid, socket);

        socket.onclose = () => {
            connectedClients.delete(socket.uuid);
        };

        socket.onopen = () => {
            for (const client of connectedClients.values()) {
                client.send(JSON.stringify({ event: "test event", uuid: socket.uuid }));
            }
        };

        socket.onmessage = async (m: any) => {
            const data = JSON.parse(m.data);
            switch (data.event) {
                case "get_kiwi": {
                    socket.send(JSON.stringify({ event: "set_status", status: { color: "green", text: "hello world" } }));
                    try {
                        const kw = await getCurrentKiwi();
                        socket.send(JSON.stringify({ event: "set_kiwi", kiwi: { url: genKiwiUrl(kw), timeout: getCurrentKiwiLeftoverUseTime() } }));
                    } catch (e) {
                        // TODO: if fallback
                        socket.send(JSON.stringify({ event: "set_status", status: { color: "red", text: "Internal server error: " + e.toString() } }));
                        // TODO: error retry time
                        socket.send(JSON.stringify({ event: "set_kiwi", kiwi: { url: "about:blank", timeout: 30000 } }));
                    }
                    break;
                }
            }
        };
    } catch (e) {
        errorpage(ctx, 500);
    }
});

router.get("/api/status", (ctx: any) => {
    ctx.response.type = "application/json";
    ctx.response.body = JSON.stringify({
        kiwis
    });
});

app.use(router.routes());
app.use(router.allowedMethods());
app.use(async (ctx) => {
    try {
        // TODO: figure out how to do it better
        await ctx.send({
            root: `${Deno.cwd()}/public`,
            index: "index.html",
        });
    } catch (e) {
        errorpage(ctx, 404);
    }
});

await app.listen({ port: 8080 });
