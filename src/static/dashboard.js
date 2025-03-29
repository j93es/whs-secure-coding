document.addEventListener("DOMContentLoaded", function () {
  const chatElement = document.getElementById("chat");
  const currentUserId = chatElement.dataset.userId;

  const socket = io();

  socket.on("connect", function () {
    console.log("채팅 서버에 연결됨");
    socket.emit("join", { user_id: currentUserId });
  });

  socket.on("message", function (data) {
    const messages = document.getElementById("messages");
    const item = document.createElement("li");
    item.textContent = data.username + ": " + data.message;
    messages.appendChild(item);
    messages.scrollTop = messages.scrollHeight;
  });

  document.getElementById("send-btn").addEventListener("click", function () {
    const input = document.getElementById("chat_input");
    const message = input.value.trim();
    if (message !== "") {
      socket.emit("send_message", {
        sender_id: currentUserId,
        message: message,
      });
      input.value = "";
    }
  });
});
