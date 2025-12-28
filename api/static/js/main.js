// static/js/main.js
document.addEventListener("DOMContentLoaded", () => {
  // Vote buttons
  document.querySelectorAll("button[data-candidate]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const candidateId = btn.getAttribute("data-candidate");
      const confirmed = await showConfirm(
        `Konfirmasi pilihan`,
        `Apakah kamu yakin memilih kandidat ini?`
      );
      if (!confirmed) return;

      const res = await fetch("/api/vote", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ candidate_id: Number(candidateId) }),
      });
      const data = await res.json();
      if (data.ok && data.redirect) {
        window.location.href = data.redirect;
      } else {
        toast(data.message || "Terjadi kesalahan.");
      }
    });
  });

  // Register form (optional)
  const regForm = document.getElementById("register-form");
  if (regForm) {
    regForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const formData = new FormData(regForm);
      const payload = {
        name: formData.get("name"),
        email: formData.get("email"),
        password: formData.get("password"),
      };
      const res = await fetch("/register", {
        method: "POST",
        body: new URLSearchParams(payload),
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
      });
      const data = await res.json();
      if (data.ok) {
        toast("Registrasi berhasil. Silakan login.");
      } else {
        toast(data.message || "Registrasi gagal.");
      }
    });
  }
});

// Minimal dialog + toast
function showConfirm(title, message) {
  return new Promise((resolve) => {
    const wrap = document.createElement("div");
    wrap.innerHTML = `
      <div style="position:fixed;inset:0;background:rgba(0,0,0,.5);display:grid;place-items:center;z-index:99">
        <div style="background:#15192e;border:1px solid #232846;border-radius:14px;padding:16px;min-width:280px;box-shadow:0 10px 30px rgba(0,0,0,.35)">
          <h3 style="margin:0 0 8px 0">${title}</h3>
          <p style="color:#a7adbf;margin:0 0 12px 0">${message}</p>
          <div style="display:flex;gap:10px;justify-content:flex-end">
            <button id="confirm-no" class="btn-outline">Batal</button>
            <button id="confirm-yes" class="btn-primary">Yakin</button>
          </div>
        </div>
      </div>`;
    document.body.appendChild(wrap);
    wrap.querySelector("#confirm-no").onclick = () => {
      wrap.remove();
      resolve(false);
    };
    wrap.querySelector("#confirm-yes").onclick = () => {
      wrap.remove();
      resolve(true);
    };
  });
}

function toast(message) {
  const el = document.createElement("div");
  el.textContent = message;
  el.style.cssText = `
    position:fixed;left:50%;transform:translateX(-50%);bottom:20px;background:#15192e;color:#e6e8ee;
    border:1px solid #232846;border-radius:12px;padding:10px 14px;box-shadow:0 10px 30px rgba(0,0,0,.35);z-index:99`;
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 2500);
}
