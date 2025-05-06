import { io } from "socket.io-client";

export const socket = io("http://cloudhf-notifier:8000", {
  transports: ["websocket"],
});
