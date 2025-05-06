import { io } from "socket.io-client";

export const socket = io("http://localhost:30084", {
  transports: ["websocket"],
});
