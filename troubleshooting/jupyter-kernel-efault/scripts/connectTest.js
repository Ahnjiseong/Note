const net = require("net");

const server = net.createServer();

server.listen(9005, "192.168.219.195", () => {
    console.log("SUCCESS");
    server.close();
});