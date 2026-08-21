(() => {
  "use strict";
  const MAX_SERVER_BYTES = 16 * 1024 * 1024;
  const COMPRESS_FROM_BYTES = 4 * 1024 * 1024;
  const MAX_SIDE = 2200;

  function showMessage(input, text, danger = false) {
    let message = input.parentElement.querySelector(".mobile-upload-message");
    if (!message) {
      message = document.createElement("div");
      message.className = "mobile-upload-message form-text";
      input.insertAdjacentElement("afterend", message);
    }
    message.classList.toggle("text-danger", danger);
    message.textContent = text;
  }

  function loadImage(file) {
    return new Promise((resolve, reject) => {
      const url = URL.createObjectURL(file);
      const image = new Image();
      image.onload = () => { URL.revokeObjectURL(url); resolve(image); };
      image.onerror = () => { URL.revokeObjectURL(url); reject(new Error("decode")); };
      image.src = url;
    });
  }

  async function compress(file) {
    const image = await loadImage(file);
    const scale = Math.min(1, MAX_SIDE / Math.max(image.naturalWidth, image.naturalHeight));
    const canvas = document.createElement("canvas");
    canvas.width = Math.max(1, Math.round(image.naturalWidth * scale));
    canvas.height = Math.max(1, Math.round(image.naturalHeight * scale));
    canvas.getContext("2d", { alpha: false }).drawImage(image, 0, 0, canvas.width, canvas.height);
    const blob = await new Promise(resolve => canvas.toBlob(resolve, "image/jpeg", 0.88));
    if (!blob) throw new Error("encode");
    return new File([blob], file.name.replace(/\.[^.]+$/, "") + ".jpg", { type: "image/jpeg", lastModified: file.lastModified });
  }

  document.querySelectorAll('input[type="file"][accept*="image"]').forEach(input => {
    input.addEventListener("change", async () => {
      const files = Array.from(input.files || []);
      if (!files.length) return;
      input.disabled = true;
      showMessage(input, "휴대폰 사진을 업로드에 맞게 확인하고 있어요…");
      try {
        const output = [];
        for (const file of files) {
          if (/hei[cf]/i.test(file.type) || /\.hei[cf]$/i.test(file.name)) {
            throw new Error("heic");
          }
          const ready = file.size >= COMPRESS_FROM_BYTES ? await compress(file) : file;
          if (ready.size > MAX_SERVER_BYTES) throw new Error("size");
          output.push(ready);
        }
        const transfer = new DataTransfer();
        output.forEach(file => transfer.items.add(file));
        input.files = transfer.files;
        const before = files.reduce((sum, file) => sum + file.size, 0);
        const after = output.reduce((sum, file) => sum + file.size, 0);
        showMessage(input, after < before ? "사진 용량과 방향을 휴대폰 업로드에 맞게 정리했어요. ✓" : "사진 확인 완료 ✓");
      } catch (error) {
        input.value = "";
        showMessage(input, error.message === "heic" ? "HEIC 사진은 아직 바로 사용할 수 없어요. 휴대폰에서 JPG로 저장하거나 화면 캡처 후 다시 올려주세요." : "사진이 너무 크거나 읽을 수 없어요. 화면 캡처 또는 16MB 이하 JPG로 다시 올려주세요.", true);
      } finally {
        input.disabled = false;
      }
    });
  });
})();
