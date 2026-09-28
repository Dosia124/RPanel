# ui_login.py — страница входа / первого запуска
LOGIN_HTML = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>RPanel</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{--bg:#0c0e14;--surface:#161a24;--text:#e9ecf3;--dim:#8a93a6;--accent:#7c9aff;--danger:#ff6161}
body{background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;height:100vh;display:flex;align-items:center;justify-content:center;overflow:hidden}
body::before{content:'';position:fixed;inset:0;background:radial-gradient(60% 50% at 80% -10%,rgba(124,154,255,.14),transparent 60%),radial-gradient(50% 40% at 10% 110%,rgba(124,154,255,.08),transparent 60%)}
.card{position:relative;width:min(380px,92vw);background:var(--surface);border:1px solid rgba(255,255,255,.07);border-radius:22px;padding:38px 34px;box-shadow:0 30px 80px rgba(0,0,0,.5);animation:in .35s ease}
@keyframes in{from{transform:translateY(14px) scale(.98);opacity:0}}
.icon{width:64px;height:64px;border-radius:20px;background:rgba(124,154,255,.14);color:var(--accent);display:flex;align-items:center;justify-content:center;margin:0 auto 18px}
h1{font-size:22px;font-weight:700;text-align:center;margin-bottom:6px}
.sub{color:var(--dim);font-size:13.5px;text-align:center;margin-bottom:24px;line-height:1.5}
.field{position:relative;margin-bottom:12px}
.field input{width:100%;background:#0f1219;border:1px solid rgba(255,255,255,.1);border-radius:12px;padding:14px 46px 14px 14px;color:var(--text);font-size:15px;outline:none;transition:border-color .2s;font-family:inherit}
.field input:focus{border-color:var(--accent)}
.eye{position:absolute;right:8px;top:50%;transform:translateY(-50%);background:none;border:none;color:var(--dim);cursor:pointer;padding:6px;display:flex;border-radius:8px}
.eye:hover{color:var(--text)}
.err{color:var(--danger);font-size:13px;text-align:center;margin:2px 0 10px;display:none}
.err.show{display:block}
.go{width:100%;background:var(--accent);border:none;color:#fff;padding:14px;border-radius:12px;font-size:15px;font-weight:600;cursor:pointer;transition:filter .2s,transform .1s;font-family:inherit}
.go:hover{filter:brightness(1.12)} .go:active{transform:scale(.985)}
.foot{margin-top:20px;color:var(--dim);font-size:11.5px;text-align:center;line-height:1.6}
</style>
</head>
<body>
<form class="card" method="POST" action="/login" id="form">
  <div class="icon">
    <svg xmlns="http://www.w3.org/2000/svg" width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
  </div>
  <h1 id="title">Unlock RPanel</h1>
  <p class="sub" id="sub">Enter your password to continue</p>
  <div class="field">
    <input type="password" id="pw" name="password" placeholder="Password" autocomplete="current-password" autofocus>
    <button type="button" class="eye" id="eye" tabindex="-1" title="Show / hide">
      <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
    </button>
  </div>
  <div class="field" id="confirm" style="display:none">
    <input type="password" id="pw2" name="confirm" placeholder="Repeat password">
  </div>
  <div class="err" id="err"></div>
  <button class="go" id="go" type="submit">Unlock</button>
  <p class="foot">Files are stored encrypted on this machine (AES · Fernet).<br>The password cannot be recovered — don't forget it.</p>
</form>
<script>
const FIRST = %%FIRST%% === 1, ERR = "%%ERROR%%";
if (FIRST) {
  document.getElementById('title').textContent = 'Create RPanel';
  document.getElementById('sub').textContent = 'Choose a strong password — it encrypts everything';
  document.getElementById('confirm').style.display = 'block';
  document.getElementById('go').textContent = 'Create vault';
  document.getElementById('pw').setAttribute('autocomplete', 'new-password');
}
if (ERR) { const e = document.getElementById('err'); e.textContent = ERR; e.classList.add('show'); }
document.getElementById('eye').onclick = function () {
  const p = document.getElementById('pw');
  p.type = p.type === 'password' ? 'text' : 'password';
};
document.getElementById('form').addEventListener('submit', function () {
  const b = document.getElementById('go');
  b.disabled = true;
  setTimeout(function () { b.disabled = false; }, 4000);
});
</script>
</body>
</html>'''