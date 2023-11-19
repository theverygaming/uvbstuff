function tune(url) {
    const iframe = document.getElementById("kiwiframe");
    if (!(url instanceof String || typeof url === 'string')) {
        iframe.outerHTML = '<iframe id="kiwiframe" src="about:blank"></iframe>';
        return;
    }

    document.getElementById("overlay").style.display = "block";
    iframe.outerHTML = `<iframe id="kiwiframe" src="${url}"></iframe>`;
    setTimeout(() => { document.getElementById("overlay").style.display = "none"; }, 15 * 1000);
}

function init_ws() {
    const socket = new WebSocket(
        `ws://${location.host}/api/ws/status_client`,
    );
    socket.onclose = (ev) => {
        const el = document.getElementById("status");
        el.style.color = "red";
        el.textContent = "Lost websocket connection";
        setTimeout(() => { init_ws(); }, 1000);
    }
    socket.onmessage = (m) => {
        const data = JSON.parse(m.data);
        console.log(data);
        switch (data.event) {
            case "set_kiwi": {
                const kiwi = data.kiwi;
                console.log(`kiwi ${kiwi.url} for ${kiwi.timeout} ms`);
                if(kiwi.url === "about:blank") {
                    tune(null);
                } else {
                    tune(kiwi.url);
                }
                setTimeout(() => {
                    tune(null);
                    socket.send(JSON.stringify({ event: "get_kiwi" }));
                }, kiwi.timeout);
                break;
            }
            case "set_status": {
                const status = data.status;
                const el = document.getElementById("status");
                el.style.color = status.color;
                el.textContent = status.text;
                break;
            }
        }
    };
    if (socket.readyState != WebSocket.OPEN) {
        socket.onopen = (ev) => {
            socket.send(JSON.stringify({ event: "get_kiwi" }));
        }
    } else {
        socket.send(JSON.stringify({ event: "get_kiwi" }));
    }
}

window.onload = () => {
    init_ws();
};
