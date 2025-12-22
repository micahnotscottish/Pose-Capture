document.addEventListener("DOMContentLoaded", () => {

  const PASSWORD = "letmein"; // <-- change this

  const entered = prompt("Enter password to continue:");
  if (entered !== PASSWORD) {
    alert("Incorrect password.");
    return; // ⛔ stop everything
  }

  const video = document.getElementById("video");
  const switchBtn = document.getElementById("switchCam");

  let stream = null;
  let facingMode = "environment";

  const canvas = document.createElement("canvas");
  const ctx = canvas.getContext("2d");

  function stopStream() {
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
      stream = null;
    }
  }

  function startCamera() {
    stopStream();

    navigator.mediaDevices.getUserMedia({
      video: { facingMode: { ideal: facingMode } }
    })
    .then(s => {
      stream = s;
      video.srcObject = stream;
    })
    .catch(err => alert(err));
  }

  // Upload loop
  setInterval(() => {
    if (!video.videoWidth) return;

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    ctx.drawImage(video, 0, 0);

    canvas.toBlob(blob => {
      fetch("/upload", {
        method: "POST",
        body: blob
      });
    }, "image/jpeg", 0.6);
  }, 100);

  switchBtn.addEventListener("click", () => {
    facingMode = facingMode === "environment" ? "user" : "environment";
    startCamera();
  });

  startCamera();
});
