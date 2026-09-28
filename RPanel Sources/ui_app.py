# ui_app.py — основной интерфейс
APP_HTML = r'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>RPanel</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{--bg:#0c0e14;--bg-soft:#0f1219;--surface:#161a24;--surface-2:#202634;--border:rgba(255,255,255,.07);--border-2:rgba(255,255,255,.14);--text:#e9ecf3;--dim:#8a93a6;--accent:#7c9aff;--accent-soft:rgba(124,154,255,.15);--danger:#ff6161;--danger-soft:rgba(255,97,97,.15);--ok:#42d392;--grid:170px;--radius:14px;--shadow:0 14px 40px rgba(0,0,0,.5)}
body.light{--bg:#f3f5f9;--bg-soft:#eaeef5;--surface:#ffffff;--surface-2:#eceff5;--border:rgba(15,20,40,.09);--border-2:rgba(15,20,40,.16);--text:#1a2030;--dim:#6a7286;--accent:#4f6ef7;--accent-soft:rgba(79,110,247,.12);--danger:#e5484d;--danger-soft:rgba(229,72,77,.12);--shadow:0 14px 40px rgba(20,30,60,.18)}
html,body{height:100%}
body{background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;overflow:hidden}
body::before{content:'';position:fixed;inset:0;pointer-events:none;z-index:0;background:radial-gradient(60% 50% at 85% -10%,var(--accent-soft),transparent 60%),radial-gradient(45% 40% at 0% 110%,var(--accent-soft),transparent 60%)}
::-webkit-scrollbar{width:9px;height:9px}
::-webkit-scrollbar-thumb{background:var(--surface-2);border-radius:5px}
::-webkit-scrollbar-track{background:transparent}
svg{flex-shrink:0}

#topbar{position:fixed;top:0;left:0;right:0;z-index:50;display:flex;align-items:center;gap:8px;flex-wrap:wrap;padding:10px 14px;background:rgba(12,14,20,.8);backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);border-bottom:1px solid var(--border)}
body.light #topbar{background:rgba(243,245,249,.85)}
.logo{display:flex;align-items:center;gap:8px;font-weight:800;font-size:15px;margin-right:4px}
.logo svg{color:var(--accent)}
.spacer{flex:1}
.count{color:var(--dim);font-size:12px;white-space:nowrap}
.btn{display:inline-flex;align-items:center;gap:7px;background:var(--surface);border:1px solid var(--border);color:var(--text);padding:8px 12px;border-radius:10px;cursor:pointer;font-size:13px;font-weight:500;transition:background .15s,border-color .15s,color .15s;white-space:nowrap;font-family:inherit}
.btn:hover{background:var(--surface-2);border-color:var(--border-2)}
.btn.active{background:var(--accent-soft);color:var(--accent);border-color:transparent}
.btn.wide{width:100%;justify-content:center;margin-top:6px}
.btn.accentbtn{background:var(--accent);color:#fff;border-color:transparent}
.btn.accentbtn:hover{filter:brightness(1.1)}
.btn.dangerbtn{background:var(--danger);color:#fff;border-color:transparent}
.btn.dangerbtn:hover{filter:brightness(1.08)}
.iconbtn{width:38px;height:38px;justify-content:center;padding:0;position:relative}
.iconbtn.danger:hover{background:var(--danger-soft);color:var(--danger);border-color:transparent}
select.btn{appearance:none;-webkit-appearance:none;padding-right:26px;background-image:url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="10" height="6" viewBox="0 0 10 6"><path d="M1 1l4 4 4-4" stroke="%238a93a6" stroke-width="1.5" fill="none" stroke-linecap="round"/></svg>');background-repeat:no-repeat;background-position:right 10px center;cursor:pointer}
select.btn option{background:var(--surface);color:var(--text)}
.badge{position:absolute;top:-6px;right:-6px;background:var(--accent);color:#fff;font-size:10px;font-weight:700;min-width:17px;height:17px;border-radius:9px;display:none;align-items:center;justify-content:center;padding:0 4px;border:2px solid var(--bg)}

.vdrop{position:relative}
.menu{display:none;position:absolute;top:calc(100% + 8px);left:0;min-width:210px;background:var(--surface);border:1px solid var(--border);border-radius:14px;padding:6px;box-shadow:var(--shadow);z-index:120;max-height:340px;overflow-y:auto}
.menu.show{display:block;animation:menuin .14s ease}
@keyframes menuin{from{opacity:0;transform:translateY(-5px)}}
.mitem{display:flex;align-items:center;gap:10px;padding:9px 10px;border-radius:9px;cursor:pointer;font-size:13.5px;color:var(--text);user-select:none}
.mitem:hover{background:var(--surface-2)}
.mitem.active{color:var(--accent);font-weight:600}
.mitem.accent{color:var(--accent)}
.mitem.danger{color:var(--danger)}
.mitem input{accent-color:var(--accent);width:15px;height:15px;margin:0;cursor:pointer}
.msep{height:1px;background:var(--border);margin:6px 4px}
.vcount{color:var(--dim);font-size:11px;background:var(--surface-2);padding:2px 7px;border-radius:6px}

.searchwrap{position:relative;display:flex;align-items:center;gap:6px;background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:0 4px 0 10px;transition:border-color .2s}
.searchwrap:focus-within{border-color:var(--accent)}
.searchwrap>svg{color:var(--dim)}
#search{background:none;border:none;outline:none;color:var(--text);font-size:13px;padding:9px 2px;width:170px;transition:width .25s;font-family:inherit}
.searchwrap:focus-within #search{width:250px}
#search::placeholder{color:var(--dim)}
.minibtn{background:var(--surface-2);border:none;color:var(--dim);font-size:10px;font-weight:700;letter-spacing:.4px;padding:4px 7px;border-radius:6px;cursor:pointer}
.minibtn:hover{color:var(--accent)}
.sugg{min-width:230px;max-height:260px}
.sitem{display:flex;justify-content:space-between;align-items:center;padding:8px 10px;border-radius:8px;cursor:pointer;font-size:13px}
.sitem:hover,.sitem.active{background:var(--surface-2)}
.scount{color:var(--dim);font-size:11px;background:var(--bg-soft);padding:1px 6px;border-radius:5px}

#gallery{position:relative;z-index:1;display:grid;grid-template-columns:repeat(auto-fill,minmax(var(--grid),1fr));gap:12px;padding:80px 16px 110px;height:100vh;overflow-y:auto;align-content:start}
.mcard{position:relative;aspect-ratio:1;border-radius:var(--radius);overflow:hidden;cursor:pointer;border:1px solid var(--border);background:linear-gradient(110deg,var(--surface) 8%,var(--surface-2) 18%,var(--surface) 33%);background-size:200% 100%;animation:shimmer 1.6s linear infinite;transition:transform .18s,box-shadow .18s,border-color .15s}
@keyframes shimmer{to{background-position:-200% 0}}
.mcard.loaded{animation:none;background:var(--surface)}
.mcard:hover{transform:translateY(-3px);box-shadow:var(--shadow);border-color:var(--border-2)}
.mcard.selected{border:2px solid var(--accent)}
.mcard img{width:100%;height:100%;object-fit:cover;display:block;opacity:0;transition:opacity .35s}
.mcard img.loaded{opacity:1}
.card-ov{position:absolute;left:0;right:0;bottom:0;padding:26px 10px 8px;background:linear-gradient(transparent,rgba(0,0,0,.78));display:flex;align-items:center;gap:6px;opacity:0;transition:opacity .2s}
.mcard:hover .card-ov,.mcard.fav .card-ov{opacity:1}
.card-name{flex:1;font-size:11.5px;color:#fff;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;text-shadow:0 1px 3px rgba(0,0,0,.9)}
.star{background:none;border:none;color:rgba(255,255,255,.85);cursor:pointer;padding:3px;display:flex}
.star.on{color:#ffcf5c}
.tbadge{position:absolute;top:8px;left:8px;background:rgba(0,0,0,.55);color:#fff;font-size:10px;font-weight:600;padding:3px 8px;border-radius:7px;letter-spacing:.3px}
.check{position:absolute;top:8px;right:8px;width:24px;height:24px;border-radius:8px;background:rgba(0,0,0,.45);border:1.5px solid rgba(255,255,255,.75);color:#fff;display:none;align-items:center;justify-content:center;z-index:3}
body.select-mode .mcard .check{display:flex}
.mcard.selected .check{background:var(--accent);border-color:var(--accent)}
.empty{grid-column:1/-1;text-align:center;padding:90px 20px;color:var(--dim)}
.eicon{margin-bottom:16px;color:var(--surface-2)}
.etitle{font-size:19px;font-weight:700;color:var(--text);margin-bottom:8px}
.etext{font-size:13.5px;line-height:1.7;margin-bottom:22px}
.empty .btn{margin:0 auto}

#viewer{position:fixed;inset:0;z-index:100;display:none;flex-direction:column;background:rgba(6,7,12,.93);backdrop-filter:blur(10px);-webkit-backdrop-filter:blur(10px)}
#viewer.open{display:flex}
#v-top{display:flex;align-items:center;gap:12px;padding:14px 20px;color:#fff;font-size:13px}
#v-counter{color:var(--dim);white-space:nowrap}
#v-name{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;opacity:.9}
#v-stage{flex:1;position:relative;display:flex;align-items:center;justify-content:center;overflow:hidden;min-height:0;cursor:grab}
#v-stage.dragging{cursor:grabbing}
#v-img,#v-video{max-width:92%;max-height:92%;border-radius:6px;transition:transform .09s linear;user-select:none;-webkit-user-drag:none;will-change:transform}
#v-video{max-width:96%;max-height:96%;background:#000}
#v-audio{width:min(560px,88vw)}
#sl-progress{position:absolute;bottom:0;left:0;height:3px;width:0;background:var(--accent);border-radius:0 3px 3px 0;z-index:8}
#v-controls{display:flex;justify-content:center;align-items:center;gap:10px;flex-wrap:wrap;padding:16px 12px 18px}
.vc{display:flex;gap:4px;background:var(--surface);border:1px solid var(--border);border-radius:14px;padding:6px}
.vbtn{width:42px;height:42px;border-radius:10px;background:transparent;border:none;color:var(--text);display:flex;align-items:center;justify-content:center;cursor:pointer;transition:background .15s,color .15s}
.vbtn:hover{background:var(--surface-2)}
.vbtn.danger:hover{background:var(--danger-soft);color:var(--danger)}
.vbtn.on{color:#ffcf5c}
#v-top,#v-controls,.hint,#tag-overlay{transition:opacity .25s}
#viewer.hideui #v-top,#viewer.hideui #v-controls,#viewer.hideui .hint,#viewer.hideui #tag-overlay{opacity:0;pointer-events:none}
.hint{position:fixed;bottom:8px;right:16px;color:var(--dim);font-size:11px;z-index:105}
#tag-overlay{position:absolute;bottom:28px;left:50%;transform:translateX(-50%);width:min(640px,92vw);background:var(--surface);border:1px solid var(--border);border-radius:16px;padding:14px;display:none;z-index:9;box-shadow:var(--shadow)}
#tag-overlay.show{display:block}
#tag-list{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:10px;max-height:120px;overflow-y:auto}
.notags{color:var(--dim);font-size:12.5px}
.tchip{display:inline-flex;align-items:center;gap:7px;background:var(--accent-soft);color:var(--accent);padding:5px 10px;border-radius:8px;font-size:12px;cursor:pointer}
.tchip:hover{background:var(--danger-soft);color:var(--danger)}
.tchip .tx{font-weight:700}
.tagrow{display:flex;gap:8px;margin-bottom:10px}
.tagrow input{flex:1;background:var(--bg-soft);border:1px solid var(--border);border-radius:10px;color:var(--text);padding:10px 12px;font-size:13px;outline:none;font-family:inherit}
.tagrow input:focus{border-color:var(--accent)}

#bulkbar{position:fixed;bottom:20px;left:50%;transform:translateX(-50%);z-index:60;display:none;align-items:center;gap:8px;background:var(--surface);border:1px solid var(--border);padding:8px 10px;border-radius:16px;box-shadow:var(--shadow)}
#bulkbar.show{display:flex}

.modal{position:fixed;inset:0;z-index:200;display:none;align-items:center;justify-content:center;background:rgba(5,6,10,.62);backdrop-filter:blur(6px);-webkit-backdrop-filter:blur(6px);padding:16px}
.modal.open{display:flex}
.modal-card{background:var(--surface);border:1px solid var(--border);border-radius:20px;padding:24px;width:min(460px,94vw);max-height:92vh;overflow-y:auto;animation:pop .18s ease}
@keyframes pop{from{transform:scale(.96);opacity:0}}
.mtitle{font-size:19px;font-weight:800;margin-bottom:16px}
.mtitle.sub{font-size:14.5px;margin:0 0 12px}
.mdiv{height:1px;background:var(--border);margin:18px 0}
.srow{display:flex;justify-content:space-between;align-items:center;gap:14px;padding:8px 0;font-size:13.5px}
.srow input[type=range]{width:180px;accent-color:var(--accent)}
.srow input[type=checkbox]{width:17px;height:17px;accent-color:var(--accent);cursor:pointer}
.srow input[type=number]{width:76px;background:var(--bg-soft);border:1px solid var(--border);color:var(--text);padding:7px;border-radius:8px;text-align:center;font-size:13px;outline:none;font-family:inherit}
.tinput{width:100%;background:var(--bg-soft);border:1px solid var(--border);color:var(--text);padding:10px 12px;border-radius:10px;font-size:13.5px;outline:none;margin-bottom:10px;font-family:inherit}
.tinput:focus{border-color:var(--accent)}
.strow{display:flex;justify-content:space-between;font-size:13px;padding:5px 0;color:var(--dim)}
.strow b{color:var(--text)}
.dlgtext{color:var(--dim);font-size:13.5px;line-height:1.6;margin-bottom:16px;overflow-wrap:anywhere}
.dlgbtns{display:flex;gap:10px;justify-content:flex-end}
.keys-table{width:100%;border-collapse:collapse;font-size:13px;margin-bottom:8px}
.keys-table td{padding:6px 8px;border-bottom:1px solid var(--border);color:var(--dim)}
.keys-table td:first-child{color:var(--text);font-weight:600;white-space:nowrap;width:130px}
kbd{background:var(--surface-2);border:1px solid var(--border-2);border-radius:5px;padding:1px 6px;font-family:inherit;font-size:11.5px}

.r34card{width:min(1000px,96vw);height:min(780px,94vh);display:flex;flex-direction:column;padding:18px}
.r34head{display:flex;justify-content:space-between;align-items:center;margin-bottom:12px}
.r34head .mtitle{margin:0}
.r34search{display:flex;gap:8px;margin-bottom:8px;position:relative}
.r34search input{flex:1;background:var(--bg-soft);border:1px solid var(--border);border-radius:10px;color:var(--text);padding:10px 14px;font-size:13.5px;outline:none;font-family:inherit}
.r34search input:focus{border-color:var(--accent)}
#r34-sugg{position:absolute;top:calc(100% + 4px);left:0;right:120px;min-width:200px;max-height:240px;overflow-y:auto;z-index:5}
#r34-recent{margin-bottom:10px}
.r34body{flex:1;display:flex;gap:14px;min-height:0}
.r34media{flex:1;position:relative;background:var(--bg-soft);border-radius:14px;display:flex;align-items:center;justify-content:center;overflow:hidden;min-width:0}
.r34media img,.r34media video{max-width:100%;max-height:100%;border-radius:6px;display:none}
.r34empty{color:var(--dim);font-size:14px;text-align:center;padding:20px;line-height:1.7}
.r34side{width:290px;display:flex;flex-direction:column;gap:10px;min-height:0}
.r34info{display:flex;justify-content:space-between;color:var(--dim);font-size:12px}
#r34-status{color:var(--ok);font-weight:600}
#r34-chips{flex:1;overflow-y:auto;min-height:0}
.chips{display:flex;flex-wrap:wrap;gap:6px}
.rchip{background:var(--surface-2);color:var(--text);padding:4px 9px;border-radius:8px;font-size:11.5px;cursor:pointer;border:1px solid transparent}
.rchip:hover{border-color:var(--accent);color:var(--accent)}
.r34actions{display:grid;grid-template-columns:1fr 1fr;gap:8px}
@media(max-width:760px){.r34body{flex-direction:column}.r34side{width:auto}}

#toasts{position:fixed;top:70px;right:16px;z-index:400;display:flex;flex-direction:column;gap:8px;max-width:min(330px,80vw)}
.toast{background:var(--surface);border:1px solid var(--border);border-left:3px solid var(--accent);padding:11px 14px;border-radius:12px;font-size:13px;box-shadow:var(--shadow);display:flex;gap:9px;align-items:center;animation:slidein .25s ease;overflow-wrap:anywhere}
.toast.ok{border-left-color:var(--ok)}
.toast.err{border-left-color:var(--danger)}
.toast .ticon{color:var(--dim);display:flex}
.toast.ok .ticon{color:var(--ok)}
.toast.err .ticon{color:var(--danger)}
.toast.out{opacity:0;transform:translateX(24px);transition:.3s}
@keyframes slidein{from{transform:translateX(24px);opacity:0}}

#uprog{position:fixed;left:0;right:0;bottom:0;z-index:350;display:none;background:var(--surface);border-top:1px solid var(--border);padding:10px 18px}
.uplabel{display:flex;justify-content:space-between;font-size:12px;color:var(--dim);margin-bottom:7px}
#uprog .bar{height:4px;background:var(--surface-2);border-radius:2px;overflow:hidden}
#uprog .fill{height:100%;width:0;background:var(--accent);transition:width .2s;border-radius:2px}

#dropzone{position:fixed;inset:12px;z-index:300;display:none;flex-direction:column;gap:14px;align-items:center;justify-content:center;background:var(--accent-soft);backdrop-filter:blur(5px);border:2.5px dashed var(--accent);border-radius:24px;color:var(--accent);font-size:17px;font-weight:700;pointer-events:none}
#boot{position:fixed;inset:0;z-index:500;display:flex;flex-direction:column;gap:18px;align-items:center;justify-content:center;background:var(--bg);transition:opacity .4s}
#boot.hide{opacity:0;pointer-events:none}
#boot .spinner{position:static}
.bootlogo{color:var(--accent);animation:pulse 1.6s ease infinite}
@keyframes pulse{50%{opacity:.5}}
.spinner{width:32px;height:32px;border:3px solid var(--surface-2);border-top-color:var(--accent);border-radius:50%;animation:spin .8s linear infinite;position:absolute}
@keyframes spin{to{transform:rotate(360deg)}}

@media(max-width:900px){.count{display:none}.lbl{display:none}#gallery{padding-top:128px}}
@media(max-width:600px){.logo span{display:none}#search{width:110px}.searchwrap:focus-within #search{width:150px}.hint{display:none}}
</style>
</head>
<body>

<div id="topbar">
  <div class="logo">
    <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
    <span>RPanel</span>
  </div>
  <div class="vdrop" id="vault-dd">
    <button class="btn" type="button">
      <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>
      <span class="lbl" id="vault-name">…</span>
    </button>
    <div class="menu" id="vault-menu"></div>
  </div>
  <select id="sort-sel" class="btn" title="Sort">
    <option value="new">New first</option>
    <option value="old">Old first</option>
    <option value="name">Name A–Z</option>
    <option value="name_desc">Name Z–A</option>
    <option value="fav">Favorites</option>
    <option value="random">Random</option>
  </select>
  <div class="vdrop" id="filter-dd">
    <button class="btn" type="button">
      <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/></svg>
      <span class="lbl" id="filter-label">All</span>
    </button>
    <div class="menu" id="filter-menu">
      <label class="mitem"><input type="checkbox" data-type="image" checked> Images</label>
      <label class="mitem"><input type="checkbox" data-type="gif" checked> GIFs</label>
      <label class="mitem"><input type="checkbox" data-type="video" checked> Videos</label>
      <label class="mitem"><input type="checkbox" data-type="audio" checked> Audio</label>
      <div class="msep"></div>
      <label class="mitem"><input type="checkbox" id="fav-only"> Favorites only</label>
    </div>
  </div>
  <div class="searchwrap">
    <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
    <input id="search" type="text" placeholder="Search tags or files…" autocomplete="off" spellcheck="false">
    <button type="button" class="minibtn" id="search-mode" title="Match mode: all terms / any term">ALL</button>
    <div class="menu sugg" id="sugg"></div>
  </div>
  <span class="count" id="count-label"></span>
  <div class="spacer"></div>
  <button class="btn iconbtn" id="btn-r34" type="button" title="Rule34 explorer">
    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="4"/><circle cx="8.5" cy="8.5" r="1.2" fill="currentColor"/><circle cx="15.5" cy="15.5" r="1.2" fill="currentColor"/><circle cx="15.5" cy="8.5" r="1.2" fill="currentColor"/><circle cx="8.5" cy="15.5" r="1.2" fill="currentColor"/><circle cx="12" cy="12" r="1.2" fill="currentColor"/></svg>
  </button>
  <button class="btn iconbtn" id="btn-upload" type="button" title="Upload files">
    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
  </button>
  <input type="file" id="file-input" multiple hidden>
  <button class="btn iconbtn" id="btn-import" type="button" title="Import from inbox folder">
    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
    <span class="badge" id="inbox-badge"></span>
  </button>
  <button class="btn iconbtn" id="btn-trash" type="button" title="Trash">
    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
    <span class="badge" id="trash-badge"></span>
  </button>
  <button class="btn iconbtn" id="btn-select" type="button" title="Select mode (S)">
    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 11 12 14 22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg>
  </button>
  <button class="btn iconbtn" id="btn-settings" type="button" title="Settings">
    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
  </button>
  <button class="btn iconbtn" id="btn-lock" type="button" title="Lock now">
    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
  </button>
  <button class="btn iconbtn danger" id="btn-power" type="button" title="Shut down">
    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18.36 6.64a9 9 0 1 1-12.73 0"/><line x1="12" y1="2" x2="12" y2="12"/></svg>
  </button>
</div>

<div id="gallery"></div>

<div id="viewer">
  <div id="v-top"><span id="v-counter"></span><span id="v-name"></span></div>
  <div id="v-stage">
    <img id="v-img" alt="" draggable="false">
    <video id="v-video" controls playsinline></video>
    <audio id="v-audio" controls></audio>
    <div id="sl-progress"></div>
    <div id="tag-overlay">
      <div id="tag-list"></div>
      <div class="tagrow">
        <input id="tag-input" type="text" placeholder="Add tags — Enter, space or comma" autocomplete="off" spellcheck="false">
        <button class="btn" id="tag-add" type="button">Add</button>
      </div>
      <button class="btn accentbtn wide" id="tag-save" type="button">Save tags</button>
    </div>
  </div>
  <div id="v-controls">
    <div class="vc">
      <button class="vbtn" id="v-prev" type="button" title="Previous (←)"><svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"/></svg></button>
      <button class="vbtn" id="v-play" type="button" title="Slideshow (Space)"></button>
      <button class="vbtn" id="v-next" type="button" title="Next (→)"><svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"/></svg></button>
    </div>
    <div class="vc">
      <button class="vbtn" id="v-zoomout" type="button" title="Zoom out (X)"><svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/><line x1="8" y1="11" x2="14" y2="11"/></svg></button>
      <button class="vbtn" id="v-zoomin" type="button" title="Zoom in (Z)"><svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/><line x1="11" y1="8" x2="11" y2="14"/><line x1="8" y1="11" x2="14" y2="11"/></svg></button>
      <button class="vbtn" id="v-reset" type="button" title="Reset view (C)"><svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/></svg></button>
      <button class="vbtn" id="v-full" type="button" title="Fullscreen"><svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"/></svg></button>
    </div>
    <div class="vc" id="v-mainctl">
      <button class="vbtn" id="v-fav" type="button" title="Favorite (F)"></button>
      <button class="vbtn" id="v-tags" type="button" title="Tags (T)"><svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"/><line x1="7" y1="7" x2="7.01" y2="7"/></svg></button>
      <button class="vbtn" id="v-export" type="button" title="Export / download (E)"><svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg></button>
    </div>
    <div class="vc" id="v-trashctl" style="display:none">
      <button class="vbtn" id="v-restore" type="button" title="Restore to vault"><svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"/></svg></button>
      <button class="vbtn danger" id="v-purge" type="button" title="Delete forever"><svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg></button>
    </div>
    <div class="vc">
      <button class="vbtn danger" id="v-delete" type="button" title="Delete (Del)"><svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg></button>
      <button class="vbtn" id="v-close" type="button" title="Close (Esc)"><svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button>
    </div>
  </div>
  <div class="hint">←/→ nav · wheel zoom · drag pan · F fav · T tags · E export · Space play/slides · H hide UI · ? shortcuts</div>
</div>

<div id="bulkbar">
  <span class="count" id="bulk-count"></span>
  <button class="btn" id="bulk-all" type="button">Select all</button>
  <button class="btn" id="bulk-tag" type="button">Tag</button>
  <button class="btn" id="bulk-fav" type="button">Favorite</button>
  <button class="btn" id="bulk-restore" type="button" style="display:none">Restore</button>
  <button class="btn" id="bulk-purgeall" type="button" style="display:none">Empty trash</button>
  <button class="btn dangerbtn" id="bulk-del" type="button">Delete</button>
  <button class="btn" id="bulk-exit" type="button">Done</button>
</div>

<div id="uprog">
  <div class="uplabel"><span id="uprog-text">Uploading…</span><span id="uprog-pct"></span></div>
  <div class="bar"><div class="fill" id="uprog-fill"></div></div>
</div>

<div class="modal" id="settings-modal">
  <div class="modal-card">
    <div class="mtitle">Settings</div>
    <div class="srow"><span>Theme</span><button class="btn" id="set-theme" type="button">Dark</button></div>
    <div class="srow"><span>Thumbnail size</span><input type="range" id="set-grid" min="110" max="320" step="10"></div>
    <div class="srow"><span>Auto-lock after (min, 0 = off)</span><input type="number" id="set-autolock" min="0" max="240"></div>
    <div class="mdiv"></div>
    <div class="mtitle sub">Slideshow</div>
    <div class="srow"><span>Start automatically in viewer</span><input type="checkbox" id="set-ss"></div>
    <div class="srow"><span>Interval (seconds)</span><input type="number" id="set-interval" min="1" max="120"></div>
    <div class="srow"><span>Autoplay media in viewer</span><input type="checkbox" id="set-autoplay"></div>
    <div class="mdiv"></div>
    <div class="mtitle sub">Rule34 API (optional)</div>
    <input class="tinput" id="r34-key" placeholder="API key">
    <input class="tinput" id="r34-uid" placeholder="User ID">
    <button class="btn wide" id="r34cfg-save" type="button">Save API config</button>
    <div class="mdiv"></div>
    <div class="mtitle sub">Change password</div>
    <input type="password" class="tinput" id="pw-old" placeholder="Current password" autocomplete="current-password">
    <input type="password" class="tinput" id="pw-new" placeholder="New password (min 6 chars)" autocomplete="new-password">
    <input type="password" class="tinput" id="pw-new2" placeholder="Repeat new password" autocomplete="new-password">
    <button class="btn wide" id="pw-btn" type="button">Change password</button>
    <div class="mdiv"></div>
    <div class="mtitle sub">This vault</div>
    <div id="stats"></div>
    <div class="srow"><span>Export whole vault (ZIP)</span><span style="display:flex;align-items:center;gap:10px"><label style="display:flex;align-items:center;gap:5px;font-size:12px;color:var(--dim)"><input type="checkbox" id="exp-trash"> trash</label><button class="btn" id="btn-export-vault" type="button">Export</button></span></div>
    <div class="mdiv"></div>
    <button class="btn dangerbtn wide" id="shutdown-btn" type="button">Shut down vault</button>
    <button class="btn wide" id="settings-close" type="button">Close</button>
  </div>
</div>

<div class="modal" id="r34-modal">
  <div class="modal-card r34card">
    <div class="r34head">
      <div class="mtitle">Rule34 Explorer</div>
      <button class="btn iconbtn" id="r34-close" type="button" title="Close"><svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button>
    </div>
    <div class="r34search">
      <input id="r34-q" type="text" placeholder="Search tags… (space separated)" autocomplete="off" spellcheck="false">
      <button class="btn accentbtn" id="r34-go" type="button">Find</button>
      <div class="menu sugg" id="r34-sugg"></div>
    </div>
    <div class="chips" id="r34-recent"></div>
    <div class="r34body">
      <div class="r34media">
        <div class="spinner" id="r34-spin" style="display:none"></div>
        <img id="r34-img" alt="">
        <video id="r34-video" controls loop muted playsinline></video>
        <div class="r34empty" id="r34-empty">Type tags and hit Find.<br>Saved posts go straight into your encrypted vault.</div>
      </div>
      <div class="r34side">
        <div class="r34info"><span id="r34-counter"></span><span id="r34-status"></span></div>
        <div class="chips" id="r34-chips"></div>
        <div class="vdrop" id="r34-vault-dd">
          <button class="btn" type="button" style="width:100%;justify-content:flex-start">
            <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>
            <span id="r34-vault-label" style="flex:1;text-align:left;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">Current vault</span>
            <span class="vcount" id="r34-vault-cnt">1</span>
          </button>
          <div class="menu" id="r34-vault-menu" style="left:auto;right:0;width:100%"></div>
        </div>
        <div class="r34actions">
          <button class="btn" id="r34-prev" type="button">← Prev</button>
          <button class="btn" id="r34-next" type="button">Next →</button>
          <button class="btn accentbtn" id="r34-savebtn" type="button">Save to vault</button>
          <button class="btn" id="r34-open" type="button">Post page</button>
        </div>
      </div>
    </div>
  </div>
</div>

<style>
.spinner{width:32px;height:32px;border:3px solid var(--surface-2);border-top-color:var(--accent);border-radius:50%;animation:mvspin .8s linear infinite;position:absolute}
#boot .spinner{position:static}
@keyframes mvspin{to{transform:rotate(360deg)}}
.tchip .tx{font-weight:700}
</style>

<div class="modal" id="dialog">
  <div class="modal-card" style="width:min(400px,94vw)">
    <div class="mtitle" id="dlg-title"></div>
    <p class="dlgtext" id="dlg-text"></p>
    <input class="tinput" id="dlg-input" style="display:none">
    <div class="dlgbtns">
      <button class="btn" id="dlg-cancel" type="button">Cancel</button>
      <button class="btn" id="dlg-ok" type="button">OK</button>
    </div>
  </div>
</div>

<div class="modal" id="keys-modal">
  <div class="modal-card">
    <div class="mtitle">Keyboard shortcuts</div>
    <table class="keys-table">
      <tr><td><kbd>/</kbd></td><td>Focus search</td></tr>
      <tr><td><kbd>S</kbd></td><td>Select mode on/off</td></tr>
      <tr><td><kbd>←</kbd> <kbd>→</kbd></td><td>Previous / next media</td></tr>
      <tr><td><kbd>Space</kbd></td><td>Play / pause, or start slideshow</td></tr>
      <tr><td><kbd>Z</kbd> / <kbd>X</kbd></td><td>Zoom in / out</td></tr>
      <tr><td><kbd>C</kbd></td><td>Reset zoom &amp; position</td></tr>
      <tr><td><kbd>W</kbd> <kbd>A</kbd> <kbd>S</kbd> <kbd>D</kbd></td><td>Pan the image</td></tr>
      <tr><td>Mouse wheel</td><td>Zoom at cursor</td></tr>
      <tr><td>Drag / double-click</td><td>Pan / quick zoom</td></tr>
      <tr><td><kbd>F</kbd></td><td>Toggle favorite</td></tr>
      <tr><td><kbd>T</kbd></td><td>Tag editor</td></tr>
      <tr><td><kbd>E</kbd></td><td>Export (decrypt &amp; download)</td></tr>
      <tr><td><kbd>H</kbd></td><td>Hide interface</td></tr>
      <tr><td><kbd>Del</kbd></td><td>Delete (to trash)</td></tr>
      <tr><td><kbd>Esc</kbd></td><td>Close</td></tr>
    </table>
    <button class="btn wide" id="keys-close" type="button">Close</button>
  </div>
</div>

<div id="toasts"></div>
<div id="dropzone">
  <svg xmlns="http://www.w3.org/2000/svg" width="44" height="44" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
  <div>Drop files to add them to the vault</div>
</div>
<div id="boot">
  <div class="bootlogo">
    <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
  </div>
  <div class="spinner"></div>
  <div class="etext">Opening RPanel...</div>
</div>

<script>
'use strict';
const $=id=>document.getElementById(id);
const enc=encodeURIComponent;
function svgIcon(inner,size,fill){
  return '<svg xmlns="http://www.w3.org/2000/svg" width="'+size+'" height="'+size+'" viewBox="0 0 24 24" fill="'+(fill?'currentColor':'none')+'" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'+inner+'</svg>';
}
const STAR=svgIcon('<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>',16);
const STAR_F=svgIcon('<polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>',16,true);
const CHECK=svgIcon('<polyline points="20 6 9 17 4 12"/>',14);
const PLAY=svgIcon('<polygon points="5 3 19 12 5 21 5 3"/>',18,true);
const PAUSE=svgIcon('<rect x="6" y="4" width="4" height="16" rx="1"/><rect x="14" y="4" width="4" height="16" rx="1"/>',18,true);
const SUN=svgIcon('<circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>',16);
const MOON=svgIcon('<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>',16);
const OKI=svgIcon('<polyline points="20 6 9 17 4 12"/>',15);
const ERRI=svgIcon('<line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>',15);
const INFOI=svgIcon('<circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/>',15);
function phSVG(inner){
  return 'data:image/svg+xml;utf8,'+encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="128" height="128" viewBox="0 0 24 24" fill="none" stroke="#6a7286" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"><rect x="1.5" y="1.5" width="21" height="21" rx="4" fill="#202634" stroke="none"/>'+inner+'</svg>');
}
const PH={
  image:phSVG('<rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="M21 15l-5-5L5 21"/>'),
  video:phSVG('<polygon points="6 3 20 12 6 21 6 3"/>'),
  audio:phSVG('<path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/>')
};

const EXT_OK=new Set(['jpg','jpeg','png','gif','bmp','webp','mp4','mkv','webm','mov','mp3','wav','ogg','m4a','flac']);
const DEFAULTS={theme:'dark',grid:170,sort:'new',mode:'all',favOnly:false,types:{image:true,gif:true,video:true,audio:true},ss:false,interval:4,autoplay:false};
let S=Object.assign({},DEFAULTS);
try{
  const st=JSON.parse(localStorage.getItem('mv2')||'{}');
  Object.assign(S,st);
  S.types=Object.assign({},DEFAULTS.types,st.types||{});
}catch(e){}
let files=[],filtered=[],vaults=[],currentVault=null,vstats={};
let trashMode=false,selectMode=false,selection=new Set(),lastSel=null;
let tagIndex=[],searchQuery='',sugIdx=-1,searchTimer=null,r34Timer=null;
const VW={open:false,i:0,scale:1,tx:0,ty:0,trash:false};
let slideshowOn=false,slideshowTimer=null;
const r34={posts:[],i:0,tags:'',saved:new Set()};
let dropDepth=0,io=null,editTags=[],dlgResolve=null;
const coll=new Intl.Collator(undefined,{numeric:true,sensitivity:'base'});

function save(){localStorage.setItem('mv2',JSON.stringify(S));}
async function api(url,opts){
  const r=await fetch(url,opts);
  if(r.status===403){location.href='/';throw new Error('locked');}
  return r;
}
async function post(url,body){
  const r=await api(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body||{})});
  try{return await r.json();}catch(e){return {};}
}
function ext(n){const i=n.lastIndexOf('.');return i<0?'':n.slice(i+1).toLowerCase();}
function fmtSize(n){
  if(n>1073741824)return (n/1073741824).toFixed(2)+' GB';
  if(n>1048576)return (n/1048576).toFixed(1)+' MB';
  return Math.max(1,Math.round(n/1024))+' KB';
}

window.addEventListener('DOMContentLoaded',init);
function init(){
  applySettings();
  wireTopbar();wireViewer();wireModals();wireR34();wireDragDrop();
  fetchFiles().then(function(){$('boot').classList.add('hide');});
  setInterval(ping,20000);
}
async function ping(){
  try{
    const r=await fetch('/api/ping',{method:'POST'});
    if(r.status===403){toast('Vault locked','err');setTimeout(function(){location.href='/';},700);}
  }catch(e){}
}
function toast(msg,type){
  type=type||'info';
  const t=document.createElement('div');t.className='toast '+type;
  const i=document.createElement('span');i.className='ticon';
  i.innerHTML=type==='ok'?OKI:(type==='err'?ERRI:INFOI);
  const s=document.createElement('span');s.textContent=msg;
  t.appendChild(i);t.appendChild(s);
  $('toasts').appendChild(t);
  setTimeout(function(){t.classList.add('out');setTimeout(function(){t.remove();},350);},3400);
}

async function fetchFiles(trash){
  if(trash===undefined)trash=trashMode;
  try{
    const r=await api('/api/files'+(trash?'?trash=1':''));
    const d=await r.json();
    files=d.files||[];vaults=d.vaults||[];currentVault=d.current;vstats=d.stats||{};RP_vaultNames=d.all_names||[];RP_syncSaved();RP_renderVaults();RP_updateSaveBtn();
    const ib=d.inbox_count||0;
    $('inbox-badge').textContent=ib;$('inbox-badge').style.display=ib?'flex':'none';
    const tb=(vstats.trash||0);
    $('trash-badge').textContent=tb;$('trash-badge').style.display=tb?'flex':'none';
    buildTagIndex();
    if(S.sort==='random')files.forEach(function(f){f._r=Math.random();});
    renderVaultMenu();renderGallery();
  }catch(e){
    if(String(e&&e.message)!=='locked')toast('Could not load the vault','err');
  }
}
function buildTagIndex(){
  const c={};
  files.forEach(function(f){(f.tags||[]).forEach(function(t){c[t]=(c[t]||0)+1;});});
  tagIndex=Object.keys(c).map(function(t){return {tag:t,count:c[t]};}).sort(function(a,b){return b.count-a.count;});
}
function renderVaultMenu(){
  const cur=vaults.find(function(v){return v.id===currentVault;});
  $('vault-name').textContent=cur?cur.name:'RPanel';
  const m=$('vault-menu');m.innerHTML='';
  vaults.forEach(function(v){
    const it=document.createElement('div');
    it.className='mitem'+(v.id===currentVault?' active':'');
    const nm=document.createElement('span');
    nm.style.flex='1';nm.style.overflow='hidden';nm.style.textOverflow='ellipsis';
    nm.textContent=v.name;
    const ct=document.createElement('span');ct.className='vcount';ct.textContent=v.count||0;
    it.appendChild(nm);it.appendChild(ct);
    it.onclick=function(){if(v.id!==currentVault)switchVault(v.id);};
    m.appendChild(it);
  });
  const sep=document.createElement('div');sep.className='msep';
  const cr=document.createElement('div');cr.className='mitem accent';cr.textContent='+ New vault';cr.onclick=newVault;
  const rn=document.createElement('div');rn.className='mitem';rn.textContent='Rename vault';rn.onclick=renameVault;
  const dl=document.createElement('div');dl.className='mitem danger';dl.textContent='Delete vault';dl.onclick=deleteVault;
  m.appendChild(sep);m.appendChild(cr);m.appendChild(rn);m.appendChild(dl);
}
async function switchVault(id){
  const d=await post('/api/vaults/switch',{id:id});
  if(d.success){
    $('search').value='';searchQuery='';hideSugg();
    if(trashMode){trashMode=false;$('btn-trash').classList.remove('active');}
    if(selectMode)toggleSelectMode();
    if(VW.open)closeViewer();
    closeMenus();
    await fetchFiles();
  }
}
async function newVault(){
  const name=await promptDialog('New vault','Name for the new vault:','My vault');
  if(!name)return;
  const d=await post('/api/vaults/create',{name:name});
  if(d.success){closeMenus();$('search').value='';searchQuery='';await fetchFiles();toast('Vault created','ok');}
  else toast(d.error||'Could not create vault','err');
}
async function renameVault(){
  const cur=vaults.find(function(v){return v.id===currentVault;});
  if(!cur)return;
  const name=await promptDialog('Rename vault','New name:',cur.name);
  if(!name||name===cur.name)return;
  await post('/api/vaults/rename',{id:currentVault,name:name});
  closeMenus();await fetchFiles();toast('Vault renamed','ok');
}
async function deleteVault(){
  const cur=vaults.find(function(v){return v.id===currentVault;});
  if(!cur)return;
  const ok=await confirmDialog('Delete vault?','Vault "'+cur.name+'" and ALL its files will be permanently destroyed. This cannot be undone.','Delete forever');
  if(!ok)return;
  const d=await post('/api/vaults/delete',{id:currentVault});
  if(d.success){
    closeMenus();$('search').value='';searchQuery='';
    trashMode=false;$('btn-trash').classList.remove('active');
    if(selectMode)toggleSelectMode();
    if(VW.open)closeViewer();
    await fetchFiles();toast('Vault deleted','info');
  }
}
function closeMenus(){document.querySelectorAll('.menu.show').forEach(function(m){m.classList.remove('show');});}

function wireTopbar(){
  document.querySelectorAll('.vdrop>.btn').forEach(function(b){
    b.addEventListener('click',function(e){
      e.stopPropagation();
      const menu=b.parentElement.querySelector('.menu');
      const was=menu.classList.contains('show');
      closeMenus();
      if(!was)menu.classList.add('show');
    });
  });
  document.addEventListener('click',function(e){
    if(!e.target.closest('.vdrop'))closeMenus();
    if(!e.target.closest('.searchwrap'))hideSugg();
    if(!e.target.closest('#r34-sugg'))hideR34Sugg();
  });
  $('sort-sel').onchange=function(e){
    S.sort=e.target.value;save();
    if(S.sort==='random')files.forEach(function(f){f._r=Math.random();});
    renderGallery();
  };
  document.querySelectorAll('#filter-menu input[data-type]').forEach(function(cb){
    cb.checked=!!S.types[cb.dataset.type];
    cb.addEventListener('change',function(){S.types[cb.dataset.type]=cb.checked;save();updateFilterLabel();renderGallery();});
  });
  $('fav-only').checked=!!S.favOnly;
  $('fav-only').addEventListener('change',function(e){S.favOnly=e.target.checked;save();updateFilterLabel();renderGallery();});
  $('search-mode').onclick=function(){S.mode=S.mode==='all'?'any':'all';save();$('search-mode').textContent=S.mode==='all'?'ALL':'ANY';renderGallery();};
  $('search').addEventListener('input',function(){
    clearTimeout(searchTimer);
    searchTimer=setTimeout(function(){searchQuery=$('search').value;renderGallery();showSugg();},170);
  });
  $('search').addEventListener('focus',showSugg);
  $('search').addEventListener('keydown',searchKeydown);
  $('btn-upload').onclick=function(){$('file-input').click();};
  $('file-input').addEventListener('change',function(e){
    if(e.target.files.length)uploadFiles(e.target.files);
    e.target.value='';
  });
  $('btn-import').onclick=importInbox;
  $('btn-trash').onclick=toggleTrash;
  $('btn-select').onclick=toggleSelectMode;
  $('btn-settings').onclick=openSettings;
  $('btn-r34').onclick=openR34;
  $('btn-lock').onclick=function(){location.href='/logout';};
  $('btn-power').onclick=shutdown;
}

function searchKeydown(e){
  const items=Array.prototype.slice.call(document.querySelectorAll('#sugg .sitem'));
  if(e.key==='ArrowDown'||e.key==='ArrowUp'){
    if(!items.length)return;
    e.preventDefault();
    sugIdx=sugIdx<0?0:(sugIdx+(e.key==='ArrowDown'?1:-1)+items.length)%items.length;
    items.forEach(function(x,i){x.classList.toggle('active',i===sugIdx);});
  }else if(e.key==='Enter'){
    e.preventDefault();
    if(sugIdx>=0&&items[sugIdx])acceptSugg(items[sugIdx].dataset.tag);
    else{hideSugg();renderGallery();}
    $('search').blur();
  }else if(e.key==='Escape'){hideSugg();$('search').blur();}
  else if(e.key==='Tab'&&items.length){e.preventDefault();acceptSugg(items[0].dataset.tag);}
}
function showSugg(){
  const box=$('sugg');
  const parts=$('search').value.toLowerCase().split(/\s+/);
  const last=parts[parts.length-1]||'';
  if(!last||last.charAt(0)==='-'){hideSugg();return;}
  const m=tagIndex.filter(function(t){return t.tag.toLowerCase().indexOf(last)===0;}).slice(0,9);
  if(!m.length){hideSugg();return;}
  box.innerHTML='';sugIdx=-1;
  m.forEach(function(t){
    const it=document.createElement('div');it.className='sitem';it.dataset.tag=t.tag;
    const n=document.createElement('span');n.textContent=t.tag;
    const c=document.createElement('span');c.className='scount';c.textContent=t.count;
    it.appendChild(n);it.appendChild(c);
    it.onclick=function(){acceptSugg(t.tag);};
    box.appendChild(it);
  });
  box.classList.add('show');
}
function acceptSugg(tag){
  const parts=$('search').value.split(/\s+/);
  parts[parts.length-1]=tag;
  $('search').value=parts.join(' ')+' ';
  searchQuery=$('search').value;
  hideSugg();renderGallery();showSugg();
}
function hideSugg(){$('sugg').classList.remove('show');sugIdx=-1;}

function updateFilterLabel(){
  const names={image:'Img',gif:'GIF',video:'Vid',audio:'Aud'};
  const on=['image','gif','video','audio'].filter(function(t){return S.types[t];});
  let lbl=on.length===4?'All':(on.length===0?'None':on.map(function(t){return names[t];}).join('+'));
  if(S.favOnly)lbl='\u2605 '+lbl;
  $('filter-label').textContent=lbl;
}

function parseQuery(q){
  const t=q.trim().toLowerCase().split(/\s+/).filter(Boolean);
  return{
    inc:t.filter(function(x){return x.charAt(0)!=='-';}),
    exc:t.filter(function(x){return x.charAt(0)==='-';}).map(function(x){return x.slice(1);})
  };
}
function termMatch(f,t){
  return f.name.toLowerCase().indexOf(t)>=0||(f.tags||[]).some(function(x){return x.toLowerCase().indexOf(t)>=0;});
}
function matchSearch(f,q){
  if(q.exc.some(function(t){return termMatch(f,t);}))return false;
  if(!q.inc.length)return true;
  return S.mode==='all'?q.inc.every(function(t){return termMatch(f,t);}):q.inc.some(function(t){return termMatch(f,t);});
}
function sortFiltered(){
  filtered.sort(function(a,b){
    switch(S.sort){
      case 'name':return coll.compare(a.name,b.name);
      case 'name_desc':return coll.compare(b.name,a.name);
      case 'old':return (a.added||0)-(b.added||0);
      case 'fav':return (b.fav?1:0)-(a.fav?1:0)||((b.added||0)-(a.added||0));
      case 'random':return (a._r||0)-(b._r||0);
      default:return (b.added||0)-(a.added||0);
    }
  });
}
function renderGallery(){
  const q=parseQuery(searchQuery);
  filtered=files.filter(function(f){
    if(!S.types[f.type])return false;
    if(S.favOnly&&!f.fav)return false;
    return matchSearch(f,q);
  });
  sortFiltered();
  const g=$('gallery');g.innerHTML='';
  if(!filtered.length)g.appendChild(emptyNode());
  else{
    const fr=document.createDocumentFragment();
    filtered.forEach(function(f,i){fr.appendChild(card(f,i));});
    g.appendChild(fr);
  }
  observeThumbs();updateCount();updateBulkbar();
}
function card(f,i){
  const c=document.createElement('div');
  c.className='mcard'+(f.fav?' fav':'')+(selection.has(f.name)?' selected':'');
  c.dataset.name=f.name;
  const img=document.createElement('img');img.alt='';img.dataset.type=f.type;
  if(f.type==='audio'){img.src=PH.audio;img.classList.add('loaded');c.classList.add('loaded');}
  else img.dataset.src='/thumbnail/'+enc(f.name);
  const ov=document.createElement('div');ov.className='card-ov';
  const nm=document.createElement('span');nm.className='card-name';nm.textContent=f.name;nm.title=f.name;
  const st=document.createElement('button');st.type='button';st.className='star'+(f.fav?' on':'');
  st.title='Favorite';st.innerHTML=f.fav?STAR_F:STAR;
  st.onclick=function(e){e.stopPropagation();if(!trashMode)toggleFav(f.name);};
  ov.appendChild(nm);ov.appendChild(st);
  c.appendChild(img);c.appendChild(ov);
  if(f.type==='video'||f.type==='audio'){
    const b=document.createElement('div');b.className='tbadge';
    b.textContent=f.type==='video'?'\u25B6 VIDEO':'\u266A AUDIO';
    c.appendChild(b);
  }
  const chk=document.createElement('div');chk.className='check';chk.innerHTML=CHECK;c.appendChild(chk);
  c.onclick=function(e){
    if(selectMode)toggleSelect(f,c,e.shiftKey);
    else if(trashMode)openViewer(i,true);
    else openViewer(i);
  };
  return c;
}
function observeThumbs(){
  if(io)io.disconnect();
  io=new IntersectionObserver(function(es){
    es.forEach(function(en){
      if(!en.isIntersecting)return;
      io.unobserve(en.target);
      const img=en.target;
      img.addEventListener('load',function(){
        img.classList.add('loaded');
        const c=img.closest('.mcard');if(c)c.classList.add('loaded');
      },{once:true});
      img.addEventListener('error',function(){
        img.src=PH[img.dataset.type]||PH.image;
        img.classList.add('loaded');
        const c=img.closest('.mcard');if(c)c.classList.add('loaded');
      },{once:true});
      img.src=img.dataset.src;
    });
  },{root:$('gallery'),rootMargin:'400px 0px'});
  document.querySelectorAll('#gallery .mcard img[data-src]').forEach(function(t){io.observe(t);});
}
function updateCount(){
  $('count-label').textContent=filtered.length+' / '+files.length+(trashMode?' \u00B7 trash':'');
}
function emptyNode(){
  const d=document.createElement('div');d.className='empty';
  if(trashMode){
    const t=document.createElement('div');t.className='etitle';t.textContent='Trash is empty';
    d.appendChild(t);return d;
  }
  const ic=document.createElement('div');ic.className='eicon';
  ic.innerHTML='<svg xmlns="http://www.w3.org/2000/svg" width="56" height="56" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>';
  const t=document.createElement('div');t.className='etitle';t.textContent='This vault is empty';
  const x=document.createElement('div');x.className='etext';
  x.innerHTML='Drag &amp; drop files anywhere on this page,<br>or use the upload button.<br>Tip: you can also drop files into the <b>inbox</b> folder next to the app and import them later.';
  const b=document.createElement('button');b.className='btn accentbtn';b.type='button';b.textContent='Upload files';
  b.style.margin='0 auto';b.onclick=function(){$('file-input').click();};
  d.appendChild(ic);d.appendChild(t);d.appendChild(x);d.appendChild(b);
  return d;
}
function toggleFav(name){
  const f=files.find(function(x){return x.name===name;});
  if(!f)return;
  f.fav=!f.fav;
  const el=cardByName(name);
  if(el){
    el.classList.toggle('fav',f.fav);
    const st=el.querySelector('.star');
    if(st){st.classList.toggle('on',f.fav);st.innerHTML=f.fav?STAR_F:STAR;}
  }
  if(VW.open&&curFile()&&curFile().name===name)updateFavBtn();
  post('/api/meta',{filename:name,fav:f.fav});
}
function cardByName(name){
  let el=null;
  document.querySelectorAll('.mcard').forEach(function(c){if(c.dataset.name===name)el=c;});
  return el;
}

async function toggleTrash(){
  trashMode=!trashMode;
  $('btn-trash').classList.toggle('active',trashMode);
  if(selectMode)toggleSelectMode();
  if(VW.open)closeViewer();
  selection.clear();
  await fetchFiles(trashMode);
}
async function importInbox(){
  const d=await post('/api/import',{});
  if(d.added)toast('Imported '+d.added+' file(s)','ok');
  if(d.duplicates)toast(d.duplicates+' duplicate(s) were skipped','info');
  if(!d.added&&!d.duplicates)toast('Inbox is empty - nothing to import','info');
  fetchFiles();
}
function uploadFiles(list){
  const arr=Array.prototype.slice.call(list).filter(function(f){return EXT_OK.has(ext(f.name));});
  const skipped=list.length-arr.length;
  if(skipped>0)toast(skipped+' unsupported file(s) skipped','info');
  if(!arr.length)return;
  const fd=new FormData();
  arr.forEach(function(f){fd.append('files[]',f);});
  const xhr=new XMLHttpRequest();
  $('uprog').style.display='block';setProg(0,'Uploading '+arr.length+' file(s)...');
  xhr.upload.onprogress=function(e){if(e.lengthComputable)setProg(e.loaded/e.total);};
  xhr.onload=function(){
    $('uprog').style.display='none';
    if(xhr.status===403){location.href='/';return;}
    let d={};try{d=JSON.parse(xhr.responseText);}catch(e){}
    if(d.added)toast('Uploaded '+d.added+' file(s)','ok');
    if(d.duplicates&&d.duplicates.length)toast(d.duplicates.length+' duplicate(s) skipped','info');
    fetchFiles();
  };
  xhr.onerror=function(){$('uprog').style.display='none';toast('Upload failed','err');};
  xhr.open('POST','/api/upload');
  xhr.send(fd);
}
function setProg(p,text){
  $('uprog-fill').style.width=(p*100).toFixed(1)+'%';
  $('uprog-pct').textContent=Math.round(p*100)+'%';
  if(text)$('uprog-text').textContent=text;
}
function wireDragDrop(){
  window.addEventListener('dragenter',function(e){
    if(!e.dataTransfer)return;
    if(Array.prototype.indexOf.call(e.dataTransfer.types,'Files')<0)return;
    e.preventDefault();dropDepth++;$('dropzone').style.display='flex';
  });
  window.addEventListener('dragover',function(e){e.preventDefault();});
  window.addEventListener('dragleave',function(e){
    dropDepth=Math.max(0,dropDepth-1);
    if(!dropDepth)$('dropzone').style.display='none';
  });
  window.addEventListener('drop',function(e){
    e.preventDefault();dropDepth=0;$('dropzone').style.display='none';
    if(e.dataTransfer&&e.dataTransfer.files.length)uploadFiles(e.dataTransfer.files);
  });
}

function toggleSelectMode(){
  selectMode=!selectMode;
  document.body.classList.toggle('select-mode',selectMode);
  $('btn-select').classList.toggle('active',selectMode);
  if(!selectMode){selection.clear();lastSel=null;}
  renderGallery();
}
function toggleSelect(f,cardEl,shift){
  const idx=filtered.indexOf(f);
  if(selection.has(f.name)){
    selection.delete(f.name);cardEl.classList.remove('selected');lastSel=idx;
  }else{
    if(shift&&lastSel!=null){
      const a=Math.min(lastSel,idx),b=Math.max(lastSel,idx);
      for(let i=a;i<=b;i++)selection.add(filtered[i].name);
      document.querySelectorAll('.mcard').forEach(function(c){if(selection.has(c.dataset.name))c.classList.add('selected');});
    }else{
      selection.add(f.name);cardEl.classList.add('selected');
    }
    lastSel=idx;
  }
  updateBulkbar();
}
function updateBulkbar(){
  const show=selectMode&&selection.size>0;
  $('bulkbar').classList.toggle('show',show);
  if(show)$('bulk-count').textContent=selection.size+' selected';
  $('bulk-tag').style.display=trashMode?'none':'inline-flex';
  $('bulk-fav').style.display=trashMode?'none':'inline-flex';
  $('bulk-restore').style.display=trashMode?'inline-flex':'none';
  $('bulk-purgeall').style.display=trashMode?'inline-flex':'none';
  $('bulk-del').textContent=trashMode?'Delete forever':'Delete';
}
async function bulkOp(body){
  const d=await post('/api/bulk',body);
  if(body.action==='delete'||body.action==='purge'||body.action==='restore'||body.action==='empty')selection.clear();
  toast('Done - '+(d.affected||0)+' file(s)','ok');
  await fetchFiles();
  updateBulkbar();
}

function wireViewer(){
  $('v-close').onclick=closeViewer;
  $('v-prev').onclick=prevMedia;
  $('v-next').onclick=nextMedia;
  $('v-play').innerHTML=PLAY;
  $('v-play').onclick=toggleSlideshow;
  $('v-zoomin').onclick=function(){zoomAt(innerWidth/2,innerHeight/2,1.3);};
  $('v-zoomout').onclick=function(){zoomAt(innerWidth/2,innerHeight/2,1/1.3);};
  $('v-reset').onclick=resetZoom;
  $('v-full').onclick=toggleFullscreen;
  $('v-fav').onclick=function(){const f=curFile();if(f&&!VW.trash)toggleFav(f.name);};
  $('v-tags').onclick=toggleTagOverlay;
  $('v-export').onclick=exportCurrent;
  $('v-delete').onclick=deleteCurrent;
  $('v-restore').onclick=restoreCurrent;
  $('v-purge').onclick=purgeCurrent;
  $('tag-save').onclick=saveTags;
  $('tag-add').onclick=addTagFromInput;
  $('tag-input').addEventListener('keydown',function(e){if(e.key==='Enter'){e.preventDefault();addTagFromInput();}});
  $('v-video').addEventListener('ended',function(){if(slideshowOn)nextMedia();});
  const stage=$('v-stage');
  stage.addEventListener('wheel',function(e){
    e.preventDefault();
    zoomAt(e.clientX,e.clientY,e.deltaY<0?1.15:1/1.15);
  },{passive:false});
  let drag=null;
  stage.addEventListener('pointerdown',function(e){
    if(e.target.id==='v-audio')return;
    if(e.target.id==='v-video'&&VW.scale<=1)return;
    drag={x:e.clientX,y:e.clientY,tx:VW.tx,ty:VW.ty};
    stage.classList.add('dragging');
    try{stage.setPointerCapture(e.pointerId);}catch(err){}
  });
  stage.addEventListener('pointermove',function(e){
    if(!drag)return;
    VW.tx=drag.tx+e.clientX-drag.x;VW.ty=drag.ty+e.clientY-drag.y;
    updateTransform();
  });
  const endDrag=function(){drag=null;stage.classList.remove('dragging');};
  stage.addEventListener('pointerup',endDrag);
  stage.addEventListener('pointercancel',endDrag);
  stage.addEventListener('dblclick',function(e){
    if(VW.scale>1.05)resetZoom();else zoomAt(e.clientX,e.clientY,2.5);
  });
  let ts=null;
  stage.addEventListener('touchstart',function(e){
    if(e.touches.length===1)ts={x:e.touches[0].clientX,y:e.touches[0].clientY};
  },{passive:true});
  stage.addEventListener('touchend',function(e){
    if(!ts)return;
    const t=e.changedTouches[0],dx=t.clientX-ts.x,dy=t.clientY-ts.y;
    if(Math.abs(dx)>60&&Math.abs(dx)>Math.abs(dy)){if(dx<0)nextMedia();else prevMedia();}
    ts=null;
  },{passive:true});
}

function openViewer(i,trash){
  VW.open=true;VW.trash=!!trash;
  $('viewer').classList.add('open');
  document.body.style.overflow='hidden';
  $('v-trashctl').style.display=VW.trash?'flex':'none';
  $('v-delete').style.display=VW.trash?'none':'flex';
  $('v-fav').style.display=VW.trash?'none':'flex';
  $('v-tags').style.display=VW.trash?'none':'flex';
  $('v-play').style.display=VW.trash?'none':'flex';
  showMedia(i);
  if(S.ss&&!slideshowOn&&filtered.length>1&&!VW.trash)toggleSlideshow();
}
function curFile(){return filtered[VW.i];}
function showMedia(i){
  if(!filtered.length){closeViewer();return;}
  if(i<0)i=filtered.length-1;
  if(i>=filtered.length)i=0;
  VW.i=i;resetZoom();
  const f=filtered[i];
  const img=$('v-img'),vid=$('v-video'),aud=$('v-audio');
  vid.pause();aud.pause();
  img.removeAttribute('src');vid.removeAttribute('src');aud.removeAttribute('src');
  img.style.display='none';vid.style.display='none';aud.style.display='none';
  const url='/media/'+enc(f.name);
  if(f.type==='image'||f.type==='gif'){img.src=url;img.style.display='block';}
  else if(f.type==='video'){vid.src=url;vid.style.display='block';if(S.autoplay)vid.play().catch(function(){});}
  else{aud.src=url;aud.style.display='block';if(S.autoplay)aud.play().catch(function(){});}
  $('v-counter').textContent=(i+1)+' / '+filtered.length;
  $('v-name').textContent=f.name;$('v-name').title=f.name;
  editTags=(f.tags||[]).slice();
  renderTagEditor();
  hideTagOverlay();
  updateFavBtn();
  if(slideshowOn)scheduleSlide();
}
function prevMedia(){showMedia(VW.i-1);}
function nextMedia(){showMedia(VW.i+1);}
function closeViewer(){
  VW.open=false;
  if(slideshowOn){
    slideshowOn=false;
    $('v-play').classList.remove('on');
    $('v-play').innerHTML=PLAY;
    clearTimeout(slideshowTimer);
    resetProgress();
  }
  $('viewer').classList.remove('open');
  $('viewer').classList.remove('hideui');
  $('v-video').pause();$('v-audio').pause();
  $('v-img').removeAttribute('src');
  $('v-video').removeAttribute('src');$('v-video').load();
  $('v-audio').removeAttribute('src');
  document.body.style.overflow='';
  hideTagOverlay();
}
function updateTransform(){
  const t='translate('+VW.tx+'px,'+VW.ty+'px) scale('+VW.scale+')';
  $('v-img').style.transform=t;
  $('v-video').style.transform=t;
}
function zoomAt(cx,cy,factor){
  const ns=Math.min(12,Math.max(0.25,VW.scale*factor));
  const k=ns/VW.scale;
  const wx=cx-innerWidth/2,wy=cy-innerHeight/2;
  VW.tx=wx-(wx-VW.tx)*k;
  VW.ty=wy-(wy-VW.ty)*k;
  VW.scale=ns;
  updateTransform();
}
function resetZoom(){VW.scale=1;VW.tx=0;VW.ty=0;updateTransform();}
function toggleFullscreen(){
  if(document.fullscreenElement)document.exitFullscreen();
  else if($('viewer').requestFullscreen)$('viewer').requestFullscreen();
}

function toggleSlideshow(){
  if(!VW.open||VW.trash)return;
  slideshowOn=!slideshowOn;
  $('v-play').classList.toggle('on',slideshowOn);
  $('v-play').innerHTML=slideshowOn?PAUSE:PLAY;
  if(slideshowOn)scheduleSlide();
  else{clearTimeout(slideshowTimer);resetProgress();}
}
function scheduleSlide(){
  clearTimeout(slideshowTimer);
  const f=curFile();
  if(!f||!slideshowOn)return;
  let ms=S.interval*1000;
  if(f.type==='video'||f.type==='audio')ms=Math.min(Math.max(ms*3,15000),90000);
  slideshowTimer=setTimeout(function(){if(slideshowOn&&VW.open)nextMedia();},ms);
  runProgress(ms);
}
function runProgress(ms){
  const p=$('sl-progress');
  p.style.transition='none';p.style.width='0';
  void p.offsetWidth;
  p.style.transition='width '+ms+'ms linear';p.style.width='100%';
}
function resetProgress(){const p=$('sl-progress');p.style.transition='none';p.style.width='0';}

function renderTagEditor(){
  const l=$('tag-list');l.innerHTML='';
  if(!editTags.length){
    const s=document.createElement('span');s.className='notags';s.textContent='No tags yet - add some below';
    l.appendChild(s);return;
  }
  editTags.forEach(function(t,idx){
    const c=document.createElement('span');c.className='tchip';c.title='Click to remove';
    const n=document.createElement('span');n.textContent=t;
    const x=document.createElement('span');x.className='tx';x.textContent='\u00D7';
    c.appendChild(n);c.appendChild(x);
    c.onclick=function(){editTags.splice(idx,1);renderTagEditor();};
    l.appendChild(c);
  });
}
function addTagFromInput(){
  const inp=$('tag-input');
  const parts=inp.value.split(/[\s,]+/).map(function(s){return s.trim().toLowerCase();}).filter(Boolean);
  parts.forEach(function(p){if(editTags.indexOf(p)<0)editTags.push(p);});
  inp.value='';
  renderTagEditor();
}
async function saveTags(){
  const f=curFile();if(!f)return;
  f.tags=editTags.slice();
  await post('/api/meta',{filename:f.name,tags:f.tags});
  buildTagIndex();
  toast('Tags saved','ok');
  hideTagOverlay();
}
function toggleTagOverlay(){
  const o=$('tag-overlay');
  o.classList.toggle('show');
  if(o.classList.contains('show'))setTimeout(function(){$('tag-input').focus();},60);
}
function hideTagOverlay(){$('tag-overlay').classList.remove('show');}
function updateFavBtn(){
  const f=curFile();if(!f)return;
  const b=$('v-fav');
  b.classList.toggle('on',!!f.fav);
  b.innerHTML=f.fav?STAR_F:STAR;
}

function exportCurrent(){
  const f=curFile();if(!f)return;
  const a=document.createElement('a');
  a.href='/api/export?filename='+enc(f.name);
  a.download=f.name;
  document.body.appendChild(a);a.click();a.remove();
  toast('Decrypting and downloading...','info');
}
async function deleteCurrent(){
  const f=curFile();if(!f)return;
  const ok=await confirmDialog('Delete file?','Move "'+f.name+'" to the trash? You can restore it later.','Delete');
  if(!ok)return;
  await post('/api/bulk',{action:'delete',files:[f.name]});
  toast('Moved to trash','ok');
  const i=VW.i;
  await fetchFiles();
  if(!filtered.length){closeViewer();return;}
  showMedia(Math.min(i,filtered.length-1));
}
async function restoreCurrent(){
  const f=curFile();if(!f)return;
  await post('/api/bulk',{action:'restore',files:[f.name]});
  toast('Restored to vault','ok');
  const i=VW.i;
  await fetchFiles();
  if(!filtered.length){closeViewer();return;}
  showMedia(Math.min(i,filtered.length-1));
}
async function purgeCurrent(){
  const f=curFile();if(!f)return;
  const ok=await confirmDialog('Delete forever?','"'+f.name+'" will be permanently destroyed.','Delete forever');
  if(!ok)return;
  await post('/api/bulk',{action:'purge',files:[f.name]});
  toast('Gone forever','info');
  const i=VW.i;
  await fetchFiles();
  if(!filtered.length){closeViewer();return;}
  showMedia(Math.min(i,filtered.length-1));
}

document.addEventListener('keydown',function(e){
  const tag=(e.target.tagName||'').toLowerCase();
  if(tag==='input'||tag==='textarea'||tag==='select'||e.target.isContentEditable)return;
  if(e.key==='Escape'){handleEscape();return;}
  if(e.key==='?'||(e.code==='Slash'&&e.shiftKey)){
    $('keys-modal').classList.toggle('open');e.preventDefault();return;
  }
  if(e.key==='/'){e.preventDefault();$('search').focus();return;}
  if(!VW.open){
    if(e.code==='KeyS')toggleSelectMode();
    return;
  }
  switch(e.code){
    case 'ArrowLeft':prevMedia();break;
    case 'ArrowRight':nextMedia();break;
    case 'KeyZ':zoomAt(innerWidth/2,innerHeight/2,1.25);break;
    case 'KeyX':zoomAt(innerWidth/2,innerHeight/2,0.8);break;
    case 'KeyC':resetZoom();break;
    case 'KeyW':VW.ty+=48;updateTransform();break;
    case 'KeyS':VW.ty-=48;updateTransform();break;
    case 'KeyA':VW.tx+=48;updateTransform();break;
    case 'KeyD':VW.tx-=48;updateTransform();break;
    case 'KeyF':{const f=curFile();if(f&&!VW.trash)toggleFav(f.name);break;}
    case 'KeyT':if(!VW.trash)toggleTagOverlay();break;
    case 'KeyE':exportCurrent();break;
    case 'KeyH':$('viewer').classList.toggle('hideui');break;
    case 'Space':{
      e.preventDefault();
      const v=$('v-video'),a=$('v-audio');
      if(v.style.display==='block'&&!v.paused)v.pause();
      else if(v.style.display==='block')v.play().catch(function(){});
      else if(a.style.display==='block'&&!a.paused)a.pause();
      else if(a.style.display==='block')a.play().catch(function(){});
      else toggleSlideshow();
      break;}
    case 'Delete':if(VW.trash)purgeCurrent();else deleteCurrent();break;
  }
});
function handleEscape(){
  if($('dialog').classList.contains('open')){cancelDialog();return;}
  if($('keys-modal').classList.contains('open')){$('keys-modal').classList.remove('open');return;}
  if($('settings-modal').classList.contains('open')){closeSettings();return;}
  if($('r34-modal').classList.contains('open')){closeR34();return;}
  if(VW.open){
    if($('tag-overlay').classList.contains('show'))hideTagOverlay();
    else closeViewer();
    return;
  }
  closeMenus();hideSugg();
}

function confirmDialog(title,text,okLabel){
  return new Promise(function(res){
    dlgResolve=res;
    $('dlg-title').textContent=title;
    $('dlg-text').textContent=text;
    $('dlg-input').style.display='none';
    $('dlg-input').value='';
    $('dlg-ok').textContent=okLabel||'OK';
    $('dlg-ok').className='btn dangerbtn';
    $('dialog').classList.add('open');
    setTimeout(function(){$('dlg-ok').focus();},50);
  });
}
function promptDialog(title,text,placeholder){
  return new Promise(function(res){
    dlgResolve=res;
    $('dlg-title').textContent=title;
    $('dlg-text').textContent=text;
    $('dlg-input').style.display='block';
    $('dlg-input').value='';
    $('dlg-input').placeholder=placeholder||'';
    $('dlg-ok').textContent='OK';
    $('dlg-ok').className='btn accentbtn';
    $('dialog').classList.add('open');
    setTimeout(function(){$('dlg-input').focus();},50);
  });
}
function closeDialog(val){
  $('dialog').classList.remove('open');
  if(dlgResolve){const r=dlgResolve;dlgResolve=null;r(val);}
}
function cancelDialog(){closeDialog(null);}

function wireModals(){
  $('dlg-cancel').onclick=cancelDialog;
  $('dlg-ok').onclick=function(){
    if($('dlg-input').style.display!=='none')closeDialog($('dlg-input').value.trim()||null);
    else closeDialog(true);
  };
  $('dlg-input').addEventListener('keydown',function(e){if(e.key==='Enter')$('dlg-ok').click();});
  $('dialog').addEventListener('click',function(e){if(e.target===$('dialog'))cancelDialog();});
  $('keys-close').onclick=function(){$('keys-modal').classList.remove('open');};
  $('keys-modal').addEventListener('click',function(e){if(e.target===$('keys-modal'))$('keys-modal').classList.remove('open');});

  $('settings-close').onclick=closeSettings;
  $('settings-modal').addEventListener('click',function(e){if(e.target===$('settings-modal'))closeSettings();});
  $('set-grid').addEventListener('input',function(e){S.grid=+e.target.value;save();applyGrid();});
  $('set-theme').onclick=function(){S.theme=S.theme==='dark'?'light':'dark';save();applySettings();};
  $('set-ss').addEventListener('change',function(e){S.ss=e.target.checked;save();});
  $('set-interval').addEventListener('change',function(e){S.interval=Math.max(1,+e.target.value||4);e.target.value=S.interval;save();});
  $('set-autoplay').addEventListener('change',function(e){S.autoplay=e.target.checked;save();});
  $('set-autolock').addEventListener('change',async function(e){
    const v=Math.max(0,+e.target.value||0);e.target.value=v;
    await post('/api/settings',{autolock:v});
    toast(v?('Auto-lock after '+v+' min'):'Auto-lock disabled','ok');
  });
  $('r34cfg-save').onclick=async function(){
    await post('/api/r34_config',{api_key:$('r34-key').value.trim(),user_id:$('r34-uid').value.trim()});
    toast('API config saved','ok');
  };
  $('pw-btn').onclick=async function(){
    const o=$('pw-old').value,n=$('pw-new').value,n2=$('pw-new2').value;
    if(!o||!n){toast('Fill in the passwords','err');return;}
    if(n!==n2){toast('New passwords do not match','err');return;}
    const d=await post('/api/change_password',{old_pass:o,new_pass:n});
    if(d.success){toast('Password updated','ok');$('pw-old').value='';$('pw-new').value='';$('pw-new2').value='';}
    else toast(d.error||'Failed','err');
  };
  $('shutdown-btn').onclick=shutdown;

  $('bulk-all').onclick=function(){
    filtered.forEach(function(f){selection.add(f.name);});
    document.querySelectorAll('.mcard').forEach(function(c){c.classList.add('selected');});
    updateBulkbar();
  };
  $('bulk-exit').onclick=toggleSelectMode;
  $('bulk-tag').onclick=async function(){
    if(!selection.size)return;
    const t=await promptDialog('Add tags','Tags to add to '+selection.size+' selected file(s):','tag1 tag2');
    if(!t)return;
    await bulkOp({action:'tag_add',files:Array.from(selection),tags:t.split(/[\s,]+/).filter(Boolean)});
  };
  $('bulk-fav').onclick=function(){bulkOp({action:'fav',files:Array.from(selection)});};
  $('bulk-restore').onclick=function(){bulkOp({action:'restore',files:Array.from(selection)});};
  $('bulk-purgeall').onclick=async function(){
    const ok=await confirmDialog('Empty trash?','ALL files in the trash will be permanently destroyed.','Empty trash');
    if(!ok)return;
    selection.clear();
    await bulkOp({action:'empty',files:[]});
  };
  $('bulk-del').onclick=async function(){
    const n=selection.size;if(!n)return;
    if(trashMode){
      const ok=await confirmDialog('Destroy forever?',n+' file(s) will be permanently deleted.','Delete forever');
      if(!ok)return;
      await bulkOp({action:'purge',files:Array.from(selection)});
    }else{
      const ok=await confirmDialog('Delete files?','Move '+n+' file(s) to the trash? You can restore them later.','Delete');
      if(!ok)return;
      await bulkOp({action:'delete',files:Array.from(selection)});
    }
  };
}

async function openSettings(){
  $('settings-modal').classList.add('open');
  $('set-grid').value=S.grid;
  $('set-ss').checked=!!S.ss;
  $('set-interval').value=S.interval;
  $('set-autoplay').checked=!!S.autoplay;
  renderStats();
  try{
    const r=await api('/api/settings');const d=await r.json();
    $('set-autolock').value=d.autolock;
  }catch(e){}
  try{
    const r=await api('/api/r34_config');const d=await r.json();
    $('r34-key').value=d.api_key||'';$('r34-uid').value=d.user_id||'';
  }catch(e){}
}
function closeSettings(){$('settings-modal').classList.remove('open');}
function renderStats(){
  const c=vstats.counts||{};
  const rows=[
    ['Files',vstats.files||0],
    ['Images / GIFs',(c.image||0)+' / '+(c.gif||0)],
    ['Videos',c.video||0],
    ['Audio',c.audio||0],
    ['Size on disk',fmtSize(vstats.total||0)],
    ['In trash',vstats.trash||0]
  ];
  $('stats').innerHTML=rows.map(function(r){return '<div class="strow"><span>'+r[0]+'</span><b>'+r[1]+'</b></div>';}).join('');
}
function applySettings(){
  document.body.classList.toggle('light',S.theme==='light');
  applyGrid();updateFilterLabel();
  $('sort-sel').value=S.sort;
  $('search-mode').textContent=S.mode==='all'?'ALL':'ANY';
  document.querySelectorAll('#filter-menu input[data-type]').forEach(function(cb){cb.checked=!!S.types[cb.dataset.type];});
  $('fav-only').checked=!!S.favOnly;
  updateThemeBtn();
}
function applyGrid(){document.documentElement.style.setProperty('--grid',S.grid+'px');}
function updateThemeBtn(){
  $('set-theme').innerHTML=(S.theme==='light'?MOON:SUN)+'<span>'+(S.theme==='light'?'Light':'Dark')+'</span>';
}

function wireR34(){
  $('r34-close').onclick=closeR34;
  $('r34-modal').addEventListener('click',function(e){if(e.target===$('r34-modal'))closeR34();});
  $('r34-go').onclick=function(){hideR34Sugg();r34Search();};
  $('r34-q').addEventListener('keydown',function(e){if(e.key==='Enter'){hideR34Sugg();r34Search();}});
  $('r34-q').addEventListener('input',function(){clearTimeout(r34Timer);r34Timer=setTimeout(r34Sugg,200);});
  $('r34-prev').onclick=function(){if(r34.i>0){r34.i--;showR34Post();}};
  $('r34-next').onclick=r34Next;
  $('r34-savebtn').onclick=r34SaveBtn;
  $('r34-open').onclick=function(){
    const p=r34.posts[r34.i];
    if(p&&p.id)window.open('https://rule34.xxx/index.php?page=post&s=view&id='+p.id,'_blank');
  };
}
function openR34(){
  $('r34-modal').classList.add('open');
  renderRecent();
  if(!r34.posts.length)$('r34-q').focus();
}
function closeR34(){
  $('r34-modal').classList.remove('open');
  $('r34-video').pause();
  hideR34Sugg();
}
async function r34Search(){
  r34.tags=$('r34-q').value.trim();
  if(!r34.tags){toast('Type some tags first','info');return;}
  addRecent(r34.tags);renderRecent();
  $('r34-spin').style.display='block';
  $('r34-empty').style.display='none';
  $('r34-img').style.display='none';
  const vid=$('r34-video');vid.style.display='none';vid.pause();vid.removeAttribute('src');
  try{
    const r=await api('/api/r34_search',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({tags:r34.tags})});
    const d=await r.json();
    r34.posts=d.posts||[];r34.i=0;
    if(!r34.posts.length){
      $('r34-empty').innerHTML=(d.error||'No results')+'<br><span style="font-size:12px">Try different or fewer tags</span>';
      $('r34-empty').style.display='block';
    }else showR34Post();
  }catch(e){toast('Search failed','err');}
  $('r34-spin').style.display='none';
}
function r34Next(){
  if(!r34.posts.length)return;
  if(r34.i>=r34.posts.length-1){r34Search();return;}
  r34.i++;showR34Post();
}
function showR34Post(){
  const p=r34.posts[r34.i];if(!p)return;
  const img=$('r34-img'),vid=$('r34-video');
  img.style.display='none';vid.style.display='none';vid.pause();
  if(p.type==='video'){vid.src=p.url;vid.style.display='block';vid.play().catch(function(){});}
  else{img.src=p.url;img.style.display='block';}
  $('r34-counter').textContent=(r34.i+1)+' / '+r34.posts.length+' \u00B7 #'+p.id;
  $('r34-status').textContent=r34.saved.has(p.id)?'saved \u2713':'';
  const chips=$('r34-chips');chips.innerHTML='';
  const tags=(p.tags||[]).slice(0,25);
  tags.forEach(function(t){
    const c=document.createElement('span');c.className='rchip';c.textContent=t;c.title='Add to search';
    c.onclick=function(){$('r34-q').value=(r34.tags?r34.tags+' ':'')+t;};
    chips.appendChild(c);
  });
  if((p.tags||[]).length>25){
    const m=document.createElement('span');m.className='rchip';m.textContent='+'+(p.tags.length-25)+' more';
    chips.appendChild(m);
  }
}
async function r34SaveBtn(){
  const p=r34.posts[r34.i];if(!p)return;
  if(r34.saved.has(p.id)){toast('Already saved','info');return;}
  const btn=$('r34-savebtn');btn.disabled=true;
  try{
    const d=await post('/api/r34_save',{url:p.url,tags:p.tags||[],id:p.id});
    if(d.success){r34.saved.add(p.id);$('r34-status').textContent='saved \u2713';toast('Saved to vault: '+d.name,'ok');fetchFiles();}
    else if(d.duplicate){r34.saved.add(p.id);$('r34-status').textContent='saved \u2713';toast('Already in your vault','info');}
    else toast(d.error||'Save failed','err');
  }catch(e){toast('Save failed','err');}
  btn.disabled=false;
}
async function r34Sugg(){
  const q=(($('r34-q').value.trim().split(/\s+/).pop())||'').toLowerCase();
  const box=$('r34-sugg');
  if(!q){hideR34Sugg();return;}
  let sugg=[];
  try{
    const r=await api('/api/r34_tags?q='+enc(q));
    sugg=await r.json();
  }catch(e){}
  if(!sugg.length)sugg=tagIndex.filter(function(t){return t.tag.toLowerCase().indexOf(q)===0;}).slice(0,10).map(function(t){return t.tag;});
  if(!sugg.length){hideR34Sugg();return;}
  box.innerHTML='';
  sugg.slice(0,10).forEach(function(t){
    const d=document.createElement('div');d.className='sitem';
    const s=document.createElement('span');s.textContent=t;
    d.appendChild(s);
    d.onclick=function(){
      const parts=$('r34-q').value.split(/\s+/);
      parts[parts.length-1]=t;
      $('r34-q').value=parts.join(' ')+' ';
      hideR34Sugg();$('r34-q').focus();
    };
    box.appendChild(d);
  });
  box.classList.add('show');
}
function hideR34Sugg(){$('r34-sugg').classList.remove('show');}
function addRecent(t){
  let rec=[];try{rec=JSON.parse(localStorage.getItem('r34rec')||'[]');}catch(e){}
  rec=[t].concat(rec.filter(function(x){return x!==t;})).slice(0,10);
  localStorage.setItem('r34rec',JSON.stringify(rec));
}
function renderRecent(){
  let rec=[];try{rec=JSON.parse(localStorage.getItem('r34rec')||'[]');}catch(e){}
  const el=$('r34-recent');el.innerHTML='';
  rec.forEach(function(t){
    const c=document.createElement('span');c.className='rchip';c.textContent=t;c.title='Search again';
    c.onclick=function(){$('r34-q').value=t;r34Search();};
    el.appendChild(c);
  });
}

async function shutdown(){
  const ok=await confirmDialog('Shut down?','The vault server will stop. Your files stay safely encrypted on disk.','Shut down');
  if(!ok)return;
  try{await post('/api/shutdown',{});}catch(e){}
  const b=$('boot');
  b.classList.remove('hide');
  b.innerHTML='<div class="spinner" style="position:static"></div><div class="etext">Shutting down... you can close this tab.</div>';
}
</script>
<script>
'use strict';
/* == RPanel patch: saved-sync, multi-vault save, ZIP export == */
let RP_vaultNames=[];
const RP_targets=new Set();
function RP_syncSaved(){
  r34.saved=new Set();
  RP_vaultNames.forEach(function(n){
    const m=/^r34_(\d+)/.exec(n);
    if(m)r34.saved.add(m[1]);
  });
}
function RP_updateSaveBtn(){
  const p=r34.posts[r34.i];
  const saved=!!(p&&r34.saved.has(String(p.id)));
  const b=$('r34-savebtn');
  if(b){b.textContent=saved?'✓ Already saved':'Save to vault';b.disabled=false;}
}
function RP_label(){
  const el=$('r34-vault-label');if(!el)return;
  const n=RP_targets.size;
  if(!n){
    const cur=vaults.find(function(v){return v.id===currentVault;});
    el.textContent='Current vault'+(cur?' — '+cur.name:'');
  }else el.textContent='Selected vaults: '+n;
  const c=$('r34-vault-cnt');if(c)c.textContent=n||1;
}
function RP_renderVaults(){
  const m=$('r34-vault-menu');if(!m)return;
  m.innerHTML='';
  vaults.forEach(function(v){
    const it=document.createElement('label');it.className='mitem';
    const cb=document.createElement('input');cb.type='checkbox';
    cb.checked=RP_targets.has(v.id);
    cb.onchange=function(){
      if(cb.checked)RP_targets.add(v.id);else RP_targets.delete(v.id);
      RP_label();
    };
    const nm=document.createElement('span');nm.style.flex='1';nm.textContent=v.name;
    const ct=document.createElement('span');ct.className='vcount';ct.textContent=v.count||0;
    it.appendChild(cb);it.appendChild(nm);it.appendChild(ct);
    m.appendChild(it);
  });
  RP_label();
}
async function RP_save(){
  const p=r34.posts[r34.i];if(!p)return;
  const b=$('r34-savebtn');
  b.disabled=true;b.textContent='Saving…';
  const t=[...RP_targets];
  try{
    const d=await post('/api/r34_save',{url:p.url,tags:p.tags,id:p.id,vault:t.length?t:currentVault});
    if(d.saved&&d.saved.length){
      toast('Saved ('+d.saved.length+(d.saved.length>1?' vaults':' vault')+')','ok');
      fetchFiles();
      setTimeout(RP_updateSaveBtn,1500);
    }else if(d.duplicates&&d.duplicates.length){
      toast('Duplicate — already in vault','info');
      RP_updateSaveBtn();
    }else{
      toast(d.error||'Could not save','err');
      RP_updateSaveBtn();
    }
  }catch(e){
    toast('Save failed','err');
    RP_updateSaveBtn();
  }
}
window.addEventListener('DOMContentLoaded',function(){
  const sb=$('r34-savebtn');
  if(sb&&sb.parentElement)sb.parentElement.addEventListener('click',function(e){
    if(!e.target.closest||!e.target.closest('#r34-savebtn'))return;
    e.stopPropagation();e.preventDefault();
    RP_save();
  },true);
  ['r34-prev','r34-next'].forEach(function(id){
    const el=$(id);
    if(el)el.addEventListener('click',function(){setTimeout(RP_updateSaveBtn,0);});
  });
  const br=$('btn-r34');
  if(br)br.addEventListener('click',function(){
    setTimeout(function(){RP_syncSaved();RP_renderVaults();RP_updateSaveBtn();},0);
  });
  const ev=$('btn-export-vault');
  if(ev)ev.onclick=function(){
    toast('Packing vault into ZIP…');
    window.location.href='/api/export_vault'+(($('exp-trash')&&$('exp-trash').checked)?'?trash=1':'');
  };
});
</script>
</body>
</html>'''