document.addEventListener("DOMContentLoaded", () => {
  const video = document.getElementById("video");

  navigator.mediaDevices.getUserMedia({ video: true })
    .then(stream => {
      video.srcObject = stream;

      const canvas = document.createElement("canvas");
      const ctx = canvas.getContext("2d");

      setInterval(() => {
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
    })
    .catch(err => alert(err));
});
