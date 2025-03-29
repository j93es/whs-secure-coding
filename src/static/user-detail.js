document.addEventListener("DOMContentLoaded", function () {
  var socket = io();
  const chatElement = document.getElementById("chat");
  var currentUserId = chatElement.dataset.currentUserId;
  var recipientId = chatElement.dataset.recipientUserId;

  socket.on("connect", function () {
    socket.emit("join", { user_id: currentUserId });
  });

  socket.on("private_message", function (data) {
    var chatWindow = document.getElementById("private-messages");
    var msg = document.createElement("li");
    msg.textContent = data.username + ": " + data.message;
    chatWindow.appendChild(msg);
    chatWindow.scrollTop = chatWindow.scrollHeight;
  });

  document.getElementById("send-btn").addEventListener("click", function () {
    var input = document.getElementById("chat-input");
    var message = input.value;
    if (message.trim() !== "") {
      socket.emit("private_message", {
        sender_id: currentUserId,
        recipient_id: recipientId,
        message: message,
      });
      input.value = "";
    }
  });
});
