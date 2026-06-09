import os
os.makedirs("static", exist_ok=True)

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"/>
<title>BrewConnect ☕</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/react/18.2.0/umd/react.development.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/react-dom/18.2.0/umd/react-dom.development.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/babel-standalone/7.23.2/babel.min.js"></script>
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
html,body,#root{height:100%;overflow:hidden}
body{font-family:system-ui,-apple-system,sans-serif;background:#020617;color:#f1f5f9}
::-webkit-scrollbar{width:4px}::-webkit-scrollbar-track{background:transparent}
::-webkit-scrollbar-thumb{background:#334155;border-radius:99px}
input,textarea,select{font-family:inherit}
@keyframes pulseGlow { 0%,100%{ box-shadow:0 0 0 0 rgba(249,115,22,0.5),0 8px 32px rgba(249,115,22,0.3) } 50%{ box-shadow:0 0 0 18px rgba(249,115,22,0),0 8px 48px rgba(249,115,22,0.5) } }
@keyframes slideUp { from{ transform:translateY(100%); opacity:0 } to{ transform:translateY(0); opacity:1 } }
@keyframes fadeIn { from{ opacity:0; transform:translateY(12px) } to{ opacity:1; transform:translateY(0) } }
@keyframes pinBounce { 0%,100%{ transform:translateY(0) } 50%{ transform:translateY(-6px) } }
.pulse-btn:hover{ transform:scale(1.04); }
.say-hi:hover{ transform:scale(1.04); filter:brightness(1.1); }
.nav-item:hover{ color:#f97316; }
.card-hover:hover{ border-color:rgba(249,115,22,0.35)!important; transform:translateY(-2px); }
.spin{animation:spin .8s linear infinite;display:inline-block}
@keyframes spin{to{transform:rotate(360deg)}}
</style>
</head>
<body>
<div id="root"></div>
<script type="text/babel">
const { useState, useEffect, useCallback, useRef } = React;

/* ── API helper ──────────────────────────────────────────── */
async function api(path, method = 'GET', body = null) {
  const tk = localStorage.getItem('bc_token');
  const r  = await fetch(path, {
    method,
    headers: {'Content-Type':'application/json', ...(tk ? {Authorization:`Bearer ${tk}`} : {})},
    ...(body ? {body: JSON.stringify(body)} : {})
  });
  if (!r.ok) { const e = await r.json().catch(()=>({})); throw new Error(e.detail||`HTTP ${r.status}`); }
  return r.json();
}

/* ── COLOUR TOKENS ─────────────────────────────────────────────── */
const C = {
  base:"#020617",base2:"#0f172a",base3:"#1e293b",
  border:"rgba(255,255,255,0.07)",border2:"rgba(255,255,255,0.12)",
  orange:"#f97316",orangeD:"#ea6c0a",
  grad:"linear-gradient(135deg,#f97316,#ec4899)",
  gradCool:"linear-gradient(135deg,#0f172a,#1e293b)",
  text:"#f1f5f9",textSub:"#94a3b8",
};

/* ── SHARED STYLES ─────────────────────────────────────────────── */
const glass = { background:"rgba(15,23,42,0.82)", backdropFilter:"blur(24px)", WebkitBackdropFilter:"blur(24px)", border:`1px solid ${C.border2}` };
const card  = { background:C.base2, border:`1px solid ${C.border}`, borderRadius:20 };
const inputSt = { background:"rgba(30,41,59,0.9)", border:`1.5px solid rgba(255,255,255,0.1)`, borderRadius:14, padding:"14px 16px", color:C.text, fontSize:15, width:"100%", outline:"none", boxSizing:"border-box" };
const btnPrimary = { background:C.grad, border:"none", borderRadius:14, padding:"15px 24px", color:"#fff", fontWeight:700, fontSize:16, cursor:"pointer", width:"100%", letterSpacing:"0.3px" };
const pill = { display:"inline-flex", alignItems:"center", gap:5, background:"rgba(249,115,22,0.15)", border:`1px solid rgba(249,115,22,0.35)`, borderRadius:999, padding:"4px 12px", fontSize:12, color:C.orange, fontWeight:600 };

/* ── COMPONENTS ────────────────────────────────────────────────── */
function Avatar({ initials, size=46, active=true, compat=null }) {
  const ring = active ? { background:C.grad, padding:2.5, borderRadius:"50%", display:"inline-flex" } : {};
  const inner = { width:size, height:size, borderRadius:"50%", background:C.base3, display:"flex", alignItems:"center", justifyContent:"center", fontWeight:700, fontSize:size*0.36, color:C.text, flexShrink:0 };
  return (
    <div style={{ position:"relative", display:"inline-flex" }}>
      <div style={ring}><div style={inner}>{initials}</div></div>
      {compat !== null && <div style={{ position:"absolute", bottom:-2, right:-2, background:C.grad, borderRadius:99, fontSize:10, fontWeight:800, color:"#fff", padding:"2px 6px", border:`2px solid ${C.base}` }}>{compat}%</div>}
    </div>
  );
}

function PulseBtn({ onClick }) {
  return (
    <button className="pulse-btn" onClick={onClick} style={{ background:C.grad, border:"none", borderRadius:999, width:200, height:200, display:"flex", flexDirection:"column", alignItems:"center", justifyContent:"center", cursor:"pointer", animation:"pulseGlow 2.2s ease-in-out infinite", transition:"transform 0.2s", color:"#fff", fontWeight:800, fontSize:18, letterSpacing:"0.4px", gap:6 }}>
      <span style={{ fontSize:38 }}>☕</span>
      <span>I'm Active</span>
      <span style={{ fontWeight:400, fontSize:13, opacity:0.85 }}>to Talk</span>
    </button>
  );
}
const Loader = () => <div style={{textAlign:'center',padding:'2rem',color:C.textSub}}>
  <span className="spin" style={{fontSize:20}}>⟳</span>
</div>;

/* ═══════════════════════════════════════════════════════════════ */
/* A. LOGIN VIEW                                                    */
/* ═══════════════════════════════════════════════════════════════ */
function LoginView({ onLogin }) {
  const [mode, setMode] = useState("signin");
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const [form, setForm] = useState({ username:"", password:"", display_name:"", email:"", confirm:"" });

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async () => {
    setErr("");
    setBusy(true);
    try {
      if (mode === "signin") {
        const data = await api('/api/auth/login', 'POST', { username: form.username, password: form.password });
        localStorage.setItem('bc_token', data.access_token);
        onLogin(data.user);
      } else {
        if (form.password !== form.confirm) throw new Error("Passwords do not match");
        const data = await api('/api/auth/register', 'POST', {
          username: form.username, email: form.email, password: form.password, display_name: form.display_name, bio: "", interests: []
        });
        localStorage.setItem('bc_token', data.access_token);
        onLogin(data.user);
      }
    } catch(e) { setErr(e.message); } finally { setBusy(false); }
  };

  return (
    <div style={{ minHeight:"100vh", background:C.base, display:"flex", flexDirection:"column", alignItems:"center", justifyContent:"center", padding:20 }}>
      <div style={{ width:"100%", maxWidth:420, background:"linear-gradient(135deg,#f97316 0%,#ec4899 50%,#8b5cf6 100%)", borderRadius:24, padding:"32px 28px 28px", marginBottom:20, textAlign:"center", position:"relative", overflow:"hidden" }}>
        <div style={{ position:"absolute", top:-40, right:-40, width:160, height:160, borderRadius:"50%", background:"rgba(255,255,255,0.07)" }}/>
        <div style={{ position:"absolute", bottom:-30, left:-30, width:120, height:120, borderRadius:"50%", background:"rgba(255,255,255,0.07)" }}/>
        <div style={{ fontSize:36, marginBottom:8 }}>☕</div>
        <div style={{ fontWeight:800, fontSize:22, color:"#fff", lineHeight:1.3, marginBottom:8, position:"relative" }}>Connect in the Real<br/>World, Right Now</div>
        <div style={{ color:"rgba(255,255,255,0.8)", fontSize:14, position:"relative" }}>Discover people nearby who are open to spontaneous conversation</div>
      </div>
      {err && <div style={{width:'100%',maxWidth:420,color:'#f87171',fontSize:13,textAlign:'center',marginBottom:12,padding:10,background:'rgba(248,113,113,.1)',borderRadius:8,flexShrink:0}}>{err}</div>}
      <div style={{ ...card, width:"100%", maxWidth:420, padding:28, borderRadius:24 }}>
        <div style={{ display:"flex", background:C.base3, borderRadius:12, padding:4, marginBottom:24, gap:4 }}>
          {["signin","signup"].map(m => (
            <button key={m} onClick={() => setMode(m)} style={{ flex:1, padding:"10px", border:"none", borderRadius:10, fontWeight:600, fontSize:14, cursor:"pointer", background: mode===m ? C.grad : "transparent", color: mode===m ? "#fff" : C.textSub, transition:"all 0.25s" }}>
              {m === "signin" ? "Sign In" : "Create Account"}
            </button>
          ))}
        </div>
        <div style={{ display:"flex", flexDirection:"column", gap:12 }}>
          {mode === "signup" && <input style={inputSt} name="display_name" placeholder="Display Name" value={form.display_name} onChange={handleChange} />}
          {mode === "signup" && <input style={inputSt} name="email" placeholder="Email address" type="email" value={form.email} onChange={handleChange} />}
          <input style={inputSt} name="username" placeholder="Username" value={form.username} onChange={handleChange} />
          <input style={inputSt} name="password" placeholder="Password" type="password" value={form.password} onChange={handleChange} />
          {mode === "signup" && <input style={inputSt} name="confirm" placeholder="Confirm Password" type="password" value={form.confirm} onChange={handleChange} />}
          <button onClick={handleSubmit} disabled={busy} style={{ ...btnPrimary, marginTop:4, boxShadow:"0 8px 24px rgba(249,115,22,0.35)", opacity: busy ? 0.6 : 1 }}>
            {busy ? "Loading..." : (mode === "signin" ? "Sign In →" : "Create Account →")}
          </button>
        </div>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════ */
/* B. HOME VIEW                                                     */
/* ═══════════════════════════════════════════════════════════════ */
const FEED = [
  { icon:"👀", text:"New people just joined near you", sub:"Check out the Discover tab", hot:true },
  { icon:"🔥", text:"3 people just went active nearby", sub:"Nearby · 42m away", hot:true },
];

function HomeView({ onActivate, user, isLive }) {
  return (
    <div style={{ flex:1, overflowY:"auto", padding:"20px 16px 8px" }}>
      <div style={{ ...glass, borderRadius:20, padding:"16px 18px", marginBottom:18, display:"flex", alignItems:"center", gap:12 }}>
        <Avatar initials={(user?.display_name||"YO")[0].toUpperCase()} size={44} active={isLive} />
        <div style={{ flex:1 }}>
          <div style={{ color:C.text, fontWeight:600, fontSize:15 }}>Hey, {user?.display_name?.split(' ')[0]} 👋</div>
          <div style={{ color:C.textSub, fontSize:13 }}>You're currently <span style={{ color: isLive ? C.orange : "#64748b" }}>{isLive ? 'Live' : 'offline'}</span></div>
        </div>
        {isLive && <div style={{ ...pill }}>🔥 Active</div>}
      </div>
      <div style={{ display:"flex", justifyContent:"center", padding:"20px 0 28px" }}>
        <PulseBtn onClick={onActivate} />
      </div>
      <div style={{ color:C.text, fontWeight:700, fontSize:16, marginBottom:12, letterSpacing:"-0.3px" }}>Activity</div>
      <div style={{ display:"flex", flexDirection:"column", gap:10 }}>
        {FEED.map((f,i) => (
          <div key={i} className="card-hover" style={{ ...card, padding:"14px 16px", display:"flex", alignItems:"center", gap:14, transition:"all 0.25s", cursor:"pointer" }}>
            <div style={{ width:44, height:44, borderRadius:14, background: f.hot ? "rgba(249,115,22,0.15)" : C.base3, display:"flex", alignItems:"center", justifyContent:"center", fontSize:20, flexShrink:0 }}>{f.icon}</div>
            <div style={{ flex:1 }}>
              <div style={{ color:C.text, fontSize:14, fontWeight:500, lineHeight:1.4 }}>{f.text}</div>
              <div style={{ color:C.textSub, fontSize:12, marginTop:2 }}>{f.sub}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════ */
/* C. ACTIVATION DRAWER                                             */
/* ═══════════════════════════════════════════════════════════════ */
const VENUES = ["Blue Tokai, CP","Third Wave Coffee","Starbucks Connaught Pl","Blue Bottle Coffee","Dyu Art Café","Brew Room, Hauz Khas"];
const TAGS = ["Looking for a co-founder 🚀","Discussing Dune Part 3 🎬","Open to networking 🤝","Just chilling ☕","Talking about AI & ML 🤖","Deep work — say hi! 💻"];

function Drawer({ onClose, onGo }) {
  const [venue, setVenue] = useState(VENUES[0]);
  const [topic, setTopic] = useState("");
  const [busy, setBusy] = useState(false);

  const handleGo = async () => {
    setBusy(true);
    await onGo(venue, topic);
    setBusy(false);
  };

  return (
    <div style={{ position:"fixed", inset:0, zIndex:200, display:"flex", flexDirection:"column", justifyContent:"flex-end" }}>
      <div onClick={onClose} style={{ position:"absolute", inset:0, background:"rgba(0,0,0,0.65)", backdropFilter:"blur(8px)" }}/>
      <div style={{ ...glass, borderRadius:"28px 28px 0 0", padding:"10px 20px 32px", animation:"slideUp 0.38s cubic-bezier(0.34,1.56,0.64,1)", position:"relative", maxHeight:"88vh", overflowY:"auto" }}>
        <div style={{ width:40, height:4, borderRadius:99, background:C.base3, margin:"0 auto 20px" }}/>
        <div style={{ fontWeight:800, fontSize:20, color:C.text, marginBottom:4 }}>Go Active ✨</div>
        <div style={{ color:C.textSub, fontSize:13, marginBottom:22 }}>Tell nearby people where you are and what's on your mind</div>
        <div style={{ marginBottom:18 }}>
          <div style={{ color:C.text, fontWeight:600, fontSize:14, marginBottom:8 }}>📍 Where are you?</div>
          <div style={{ position:"relative" }}>
            <select value={venue} onChange={e=>setVenue(e.target.value)} style={{ ...inputSt, appearance:"none", paddingRight:40 }}>
              {VENUES.map(v=><option key={v} value={v}>{v}</option>)}
            </select>
            <span style={{ position:"absolute", right:14, top:"50%", transform:"translateY(-50%)", color:C.textSub, pointerEvents:"none" }}>▾</span>
          </div>
        </div>
        <div style={{ marginBottom:18 }}>
          <div style={{ color:C.text, fontWeight:600, fontSize:14, marginBottom:8 }}>💬 What's on your mind?</div>
          <textarea value={topic} onChange={e=>setTopic(e.target.value)} placeholder="Tell people what you'd love to talk about..." rows={3} style={{ ...inputSt, resize:"none", lineHeight:1.6 }}/>
        </div>
        <div style={{ color:C.textSub, fontSize:12, fontWeight:600, marginBottom:8, textTransform:"uppercase", letterSpacing:"0.8px" }}>Quick Tags</div>
        <div style={{ display:"flex", flexWrap:"wrap", gap:8, marginBottom:24 }}>
          {TAGS.map(t=>(
            <button key={t} onClick={()=>setTopic(t)} style={{ background: topic===t ? "rgba(249,115,22,0.25)" : C.base3, border:`1px solid ${topic===t ? C.orange : C.border}`, borderRadius:999, padding:"7px 13px", color: topic===t ? C.orange : C.textSub, fontSize:13, cursor:"pointer", transition:"all 0.2s" }}>{t}</button>
          ))}
        </div>
        <button onClick={handleGo} disabled={busy} style={{ ...btnPrimary, boxShadow:"0 8px 32px rgba(249,115,22,0.45)", fontSize:17, padding:"17px", opacity: busy ? 0.6 : 1 }}>
          🔥 {busy ? "Going Live..." : "Go Live Now"}
        </button>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════ */
/* D. DISCOVER VIEW                                                 */
/* ═══════════════════════════════════════════════════════════════ */
function DiscoverView({ lat, lon, onChatWith }) {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetch_ = useCallback(async () => {
    setLoading(true);
    try {
      const d = await api(`/api/discover?lat=${lat||28.6315}&lon=${lon||77.2167}&radius_km=2.0`);
      setUsers(d.results || []);
    } catch(e) { console.warn(e); }
    finally { setLoading(false); }
  }, [lat, lon]);

  useEffect(() => { fetch_(); }, [fetch_]);

  const pins = users.slice(0,5).map((u,i)=>{
    const colors = ['#f97316','#fb923c','#fdba74','#3b82f6','#60a5fa'];
    const positions = [{x:22,y:30},{x:55,y:45},{x:70,y:20},{x:35,y:65},{x:80,y:70}];
    const p = positions[i] || {x:50,y:50};
    return {...u, ...p, color:colors[i]};
  });

  return (
    <div style={{ flex:1, overflowY:"auto" }}>
      <div style={{ position:"relative", height:240, background:"linear-gradient(160deg,#0a1628 0%,#0f1f3d 50%,#111827 100%)", overflow:"hidden", flexShrink:0 }}>
        {/* Radar Ring */}
        <div style={{ position:"absolute", top:"50%", left:"50%", transform:"translate(-50%,-50%)", width:180, height:180, borderRadius:"50%", border:"1px solid rgba(249,115,22,0.15)", boxShadow:"0 0 0 40px rgba(249,115,22,0.04), 0 0 0 80px rgba(249,115,22,0.02)" }}/>
        {/* You pin */}
        <div style={{ position:"absolute", top:"50%", left:"50%", transform:"translate(-50%,-50%)", zIndex:10 }}>
          <div style={{ width:16, height:16, borderRadius:"50%", background:C.grad, boxShadow:`0 0 16px rgba(249,115,22,0.8)`, border:"2px solid #fff" }}/>
        </div>
        {/* User pins */}
        {pins.map((p,i)=>(
          <div key={i} style={{ position:"absolute", left:`${p.x}%`, top:`${p.y}%`, transform:"translate(-50%,-100%)", animation:`pinBounce ${1.8+i*0.3}s ease-in-out infinite`, animationDelay:`${i*0.4}s` }}>
            <div style={{ width:32, height:32, borderRadius:"50%", background:`linear-gradient(135deg,${p.color},#ec4899)`, display:"flex", alignItems:"center", justifyContent:"center", fontSize:13, fontWeight:700, color:"#fff", boxShadow:`0 4px 12px rgba(249,115,22,0.5)`, border:"2px solid rgba(255,255,255,0.3)" }}>
              {(p.display_name||"?")[0].toUpperCase()}
            </div>
          </div>
        ))}
      </div>

      <div style={{ padding:"16px 14px 80px" }}>
        <div style={{ color:C.text, fontWeight:700, fontSize:16, marginBottom:12, letterSpacing:"-0.3px" }}>Active Nearby</div>
        {loading && <Loader />}
        {!loading && users.length === 0 && (
          <div style={{textAlign:'center',padding:'2rem',color:C.textSub,fontSize:14}}>No one nearby right now.</div>
        )}
        <div style={{ display:"flex", flexDirection:"column", gap:12 }}>
          {users.map(u=>(
            <div key={u.user_id} className="card-hover" style={{ ...card, padding:"16px", transition:"all 0.25s" }}>
              <div style={{ display:"flex", gap:14, marginBottom:12 }}>
                <Avatar initials={(u.display_name||"?")[0].toUpperCase()} size={52} active={true} compat={Math.round(u.compatibility*100)} />
                <div style={{ flex:1, minWidth:0 }}>
                  <div style={{ display:"flex", justifyContent:"space-between", alignItems:"flex-start" }}>
                    <div style={{ color:C.text, fontWeight:700, fontSize:16 }}>{u.display_name}</div>
                    <div style={{ color:C.textSub, fontSize:12 }}>📍 {u.distance_km < .1 ? '< 100m' : `${u.distance_km.toFixed(2)} km`}</div>
                  </div>
                  <div style={{ color:C.textSub, fontSize:13, marginTop:2 }}>☕ {u.venue_name || "Coffee shop"}</div>
                </div>
              </div>
              {u.mood_tag && (
              <div style={{ background:"rgba(249,115,22,0.08)", border:`1px solid rgba(249,115,22,0.2)`, borderRadius:12, padding:"10px 14px", marginBottom:12, display:"flex", gap:8, alignItems:"flex-start" }}>
                <span style={{ fontSize:16, marginTop:1 }}>💬</span>
                <div style={{ color:C.text, fontSize:13, lineHeight:1.5, fontStyle:"italic" }}>"{u.mood_tag}"</div>
              </div>
              )}
              <button className="say-hi" onClick={()=>onChatWith({id: u.user_id, display_name: u.display_name})} style={{ background: C.grad, border: "none", borderRadius:12, padding:"11px", color:"#fff", fontWeight:700, fontSize:14, cursor:"pointer", width:"100%", transition:"all 0.25s" }}>
                Say Hi 👋
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════ */
/* E. MESSAGES VIEW (Real)                                         */
/* ═══════════════════════════════════════════════════════════════ */
function MessagesView({ onChatWith }) {
  const [convos, setConvos] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetch_ = useCallback(async () => {
    setLoading(true);
    try {
      const d = await api(`/api/messages/conversations`);
      setConvos(d);
    } catch(e) { console.warn(e); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { 
    fetch_(); 
    // Listen for new messages globally to update the conversation list
    const handleNew = () => fetch_();
    window.addEventListener('bc_new_message', handleNew);
    return () => window.removeEventListener('bc_new_message', handleNew);
  }, [fetch_]);

  return (
    <div style={{ flex:1, overflowY:"auto", padding:"20px 14px 80px" }}>
      <div style={{ color:C.text, fontWeight:700, fontSize:20, marginBottom:16, letterSpacing:"-0.5px" }}>Messages</div>
      
      {loading && <Loader />}
      {!loading && convos.length === 0 && (
        <div style={{textAlign:'center',padding:'2rem',color:C.textSub,fontSize:14}}>No messages yet. Go say Hi to someone!</div>
      )}

      {convos.length > 0 && (
      <div style={{ ...card, borderRadius:18, overflow:"hidden" }}>
        {convos.map((m,i)=>(
          <div key={m.user.id} onClick={() => onChatWith(m.user)} className="card-hover" style={{ display:"flex", alignItems:"center", gap:14, padding:"16px", borderBottom: i<convos.length-1 ? `1px solid ${C.border}` : "none", cursor:"pointer", transition:"all 0.2s" }}>
            <Avatar initials={(m.user.display_name||"?")[0].toUpperCase()} size={48} active={false} />
            <div style={{ flex:1, minWidth:0 }}>
              <div style={{ display:"flex", justifyContent:"space-between" }}>
                <span style={{ color:C.text, fontWeight:600, fontSize:15 }}>{m.user.display_name}</span>
                <span style={{ color:C.textSub, fontSize:12 }}>{new Date(m.last_message.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
              </div>
              <div style={{ color: m.unread_count > 0 ? C.text : C.textSub, fontSize:13, marginTop:2, overflow:"hidden", textOverflow:"ellipsis", whiteSpace:"nowrap", fontWeight: m.unread_count > 0 ? 500 : 400 }}>{m.last_message.content}</div>
            </div>
            {m.unread_count > 0 && <div style={{ background:C.grad, borderRadius:99, minWidth:20, height:20, display:"flex", alignItems:"center", justifyContent:"center", fontSize:11, color:"#fff", fontWeight:700, padding:"0 6px", flexShrink:0 }}>{m.unread_count}</div>}
          </div>
        ))}
      </div>
      )}
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════ */
/* F. CHAT VIEW (New Real-Time UI)                                 */
/* ═══════════════════════════════════════════════════════════════ */
function ChatView({ otherUser, onBack, socketRef, currentUserId }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const endRef = useRef(null);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const msgs = await api(`/api/messages/${otherUser.id}`);
        setMessages(msgs);
        setTimeout(() => endRef.current?.scrollIntoView({behavior: "smooth"}), 100);
      } catch (e) { console.warn(e); }
    };
    fetchHistory();
    
    const handleMsg = (e) => {
      const msg = JSON.parse(e.detail);
      if (msg.sender_id === otherUser.id || msg.recipient_id === otherUser.id) {
        setMessages(p => {
          // avoid duplicates
          if (p.some(x => x.id === msg.id)) return p;
          return [...p, msg];
        });
        setTimeout(() => endRef.current?.scrollIntoView({behavior: "smooth"}), 100);
      }
    };
    window.addEventListener('bc_new_message', handleMsg);
    return () => window.removeEventListener('bc_new_message', handleMsg);
  }, [otherUser.id]);

  const send = () => {
    if (!input.trim() || !socketRef.current) return;
    const data = { recipient_id: otherUser.id, content: input.trim() };
    socketRef.current.send(JSON.stringify(data));
    setInput("");
  };

  return (
    <div style={{ flex:1, display:"flex", flexDirection:"column", background:C.base, position:"absolute", inset:0, zIndex:100, animation:"slideUp 0.25s ease-out" }}>
      {/* Header */}
      <div style={{ ...glass, padding:"12px 16px", display:"flex", alignItems:"center", gap:14, borderBottom:`1px solid ${C.border}` }}>
        <button onClick={onBack} style={{ background:"none", border:"none", color:C.textSub, fontSize:22, cursor:"pointer", padding:"0 8px" }}>←</button>
        <Avatar initials={(otherUser.display_name||"?")[0].toUpperCase()} size={36} active={false} />
        <div style={{ flex:1 }}>
          <div style={{ color:C.text, fontWeight:700, fontSize:15 }}>{otherUser.display_name}</div>
        </div>
      </div>
      
      {/* Messages */}
      <div style={{ flex:1, overflowY:"auto", padding:"16px", display:"flex", flexDirection:"column", gap:12 }}>
        {messages.map((m, idx) => {
          const isMe = m.sender_id === currentUserId;
          // check if prev msg was same sender to group bubbles
          const prev = idx > 0 ? messages[idx-1] : null;
          const sameAsPrev = prev && prev.sender_id === m.sender_id;
          
          return (
            <div key={m.id} style={{ alignSelf: isMe ? "flex-end" : "flex-start", maxWidth:"75%", marginTop: sameAsPrev ? -6 : 0 }}>
              <div style={{ background: isMe ? C.grad : C.base3, color:"#fff", padding:"10px 14px", borderRadius: isMe ? "18px 18px 0 18px" : "18px 18px 18px 0", fontSize:14, lineHeight:1.4 }}>
                {m.content}
              </div>
              {!sameAsPrev && <div style={{ color:C.textSub, fontSize:10, marginTop:4, textAlign: isMe ? "right" : "left" }}>
                {new Date(m.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
              </div>}
            </div>
          );
        })}
        <div ref={endRef} />
      </div>

      {/* Input */}
      <div style={{ ...glass, padding:"12px 16px calc(12px + env(safe-area-inset-bottom))", display:"flex", gap:10, alignItems:"center", borderTop:`1px solid ${C.border}` }}>
        <input 
          value={input} 
          onChange={e=>setInput(e.target.value)} 
          onKeyDown={e => e.key === 'Enter' && send()}
          placeholder="Type a message..." 
          style={{ ...inputSt, borderRadius:99, flex:1, padding:"12px 16px" }}
        />
        <button onClick={send} style={{ background:C.orange, border:"none", width:44, height:44, borderRadius:"50%", color:"#fff", fontSize:18, cursor:"pointer", display:"flex", alignItems:"center", justifyContent:"center" }}>
          ↗
        </button>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════ */
/* G. PROFILE VIEW                                                  */
/* ═══════════════════════════════════════════════════════════════ */
function ProfileView({ user, onUpdate }) {
  const logout = () => { localStorage.removeItem('bc_token'); window.location.reload(); };
  return (
    <div style={{ flex:1, overflowY:"auto", paddingBottom: 80 }}>
      <div style={{ background:"linear-gradient(160deg,#1e1035,#1a0a2e,#0f172a)", padding:"32px 20px 0", marginBottom:-20, textAlign:"center", paddingBottom: 40 }}>
        <Avatar initials={(user?.display_name||"YO")[0].toUpperCase()} size={80} active={true} />
        <div style={{ color:C.text, fontWeight:800, fontSize:20, marginTop:12 }}>{user?.display_name}</div>
        <div style={{ color:C.textSub, fontSize:14, marginTop:3 }}>@{user?.username}</div>
      </div>
      <div style={{ padding:"30px 16px 16px" }}>
        <button onClick={logout} style={{ ...btnPrimary, background:C.base3, boxShadow:"none", color:C.textSub, border:`1px solid ${C.border}` }}>Sign Out</button>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════ */
/* ROOT APP                                                         */
/* ═══════════════════════════════════════════════════════════════ */
function BrewConnect() {
  const [user, setUser]       = useState(null);
  const [booting, setBooting] = useState(true);
  const [tab, setTab]         = useState("home");
  const [drawer, setDrawer]   = useState(false);
  const [isLive, setIsLive]   = useState(false);
  const [lat, setLat]         = useState(null);
  const [lon, setLon]         = useState(null);
  
  // Chat state
  const [chattingWith, setChattingWith] = useState(null);
  const socketRef = useRef(null);

  useEffect(() => {
    const tk = localStorage.getItem('bc_token');
    if (!tk) { setBooting(false); return; }
    
    // Connect WebSocket
    const connectWs = () => {
      const wsUrl = (window.location.protocol === 'https:' ? 'wss:' : 'ws:') + '//' + window.location.host + '/api/ws/messages?token=' + tk;
      const ws = new WebSocket(wsUrl);
      ws.onmessage = (e) => {
        const event = new CustomEvent('bc_new_message', { detail: e.data });
        window.dispatchEvent(event);
      };
      ws.onclose = () => {
        setTimeout(connectWs, 3000); // reconnect
      };
      socketRef.current = ws;
    };
    
    api('/api/auth/me')
      .then(u => { setUser(u); connectWs(); return api('/api/session/status'); })
      .then(s => { if (s.is_active){ setIsLive(true); setLat(s.latitude); setLon(s.longitude); } })
      .catch(() => { localStorage.removeItem('bc_token'); })
      .finally(() => setBooting(false));
      
    return () => { if (socketRef.current) socketRef.current.close(); };
  }, []);

  useEffect(() => {
    if (!navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition(
      p => { setLat(p.coords.latitude); setLon(p.coords.longitude); },
      () => { setLat(28.6315); setLon(77.2167); }
    );
  }, []);

  const handleGo = async (venue, topic) => {
    try {
      await api('/api/session/toggle','POST',{
        latitude: lat||28.6315, longitude: lon||77.2167,
        is_active: true, venue_name: venue, mood_tag: topic
      });
      setIsLive(true);
      setDrawer(false);
      setTab("discover");
    } catch(e) { alert(e.message); }
  };

  const handleOffline = async () => {
    try {
      await api('/api/session/toggle','POST',{ latitude: lat||28.6315, longitude: lon||77.2167, is_active: false });
    } catch {}
    setIsLive(false);
  };

  const NAV = [
    { id:"home",     icon:"⌂",  label:"Home"     },
    { id:"discover", icon:"🧭", label:"Discover"  },
    { id:"messages", icon:"💬", label:"Messages"  },
    { id:"profile",  icon:"◉",  label:"Profile"   },
  ];

  if (booting) return (
    <div style={{height:'100vh',background:C.base,display:'flex',alignItems:'center',justifyContent:'center',flexDirection:'column',gap:12}}>
      <div style={{fontSize:48}}>☕</div>
      <div style={{color:C.textSub,fontSize:14}}>Loading BrewConnect...</div>
    </div>
  );

  if (!user) return <LoginView onLogin={(u) => { setUser(u); window.location.reload(); }} />;

  return (
    <div style={{ height:"100vh", background:C.base, display:"flex", flexDirection:"column", fontFamily:"system-ui,-apple-system,sans-serif", maxWidth:430, margin:"0 auto", position:"relative", overflow:"hidden" }}>

      <div style={{ ...glass, padding:"12px 16px", display:"flex", alignItems:"center", justifyContent:"space-between", flexShrink:0, zIndex:50 }}>
        <div style={{ display:"flex", alignItems:"center", gap:10 }}>
          <Avatar initials={(user?.display_name||"YO")[0].toUpperCase()} size={36} active={isLive} />
          <div>
            <div style={{ color:C.text, fontWeight:700, fontSize:14, letterSpacing:"-0.2px" }}>BrewConnect ☕</div>
            <div style={{ color: isLive ? C.orange : C.textSub, fontSize:11, fontWeight:500 }}>{isLive ? "🔴 You're Live" : "● Offline"}</div>
          </div>
        </div>
        <div style={{ display:"flex", gap:10, alignItems:"center" }}>
          {isLive && <div style={{...pill, cursor:"pointer"}} onClick={handleOffline}>🔴 Live</div>}
          {!isLive && <div style={{...pill, opacity:0.5}}>✦ Offline</div>}
        </div>
      </div>

      <div style={{ flex:1, overflowY:"auto", display:"flex", flexDirection:"column", animation:"fadeIn 0.3s ease" }}>
        {tab === "home"     && <HomeView onActivate={() => setDrawer(true)} user={user} isLive={isLive} />}
        {tab === "discover" && <DiscoverView lat={lat} lon={lon} onChatWith={(u) => setChattingWith(u)} />}
        {tab === "messages" && <MessagesView onChatWith={(u) => setChattingWith(u)} />}
        {tab === "profile"  && <ProfileView user={user} onUpdate={setUser} />}
      </div>

      {/* Bottom Nav */}
      <div style={{ ...glass, padding:"10px 8px calc(10px + env(safe-area-inset-bottom))", display:"flex", flexShrink:0, zIndex:50 }}>
        {NAV.map(n => (
          <button key={n.id} className="nav-item" onClick={() => setTab(n.id)} style={{ flex:1, display:"flex", flexDirection:"column", alignItems:"center", gap:3, background:"none", border:"none", cursor:"pointer", padding:"6px 4px", borderRadius:12, transition:"all 0.2s", color: tab === n.id ? C.orange : C.textSub }}>
            <span style={{ fontSize:20 }}>{n.icon}</span>
            <span style={{ fontSize:10, fontWeight: tab===n.id ? 700 : 500, letterSpacing:"0.3px" }}>{n.label}</span>
            {tab === n.id && <div style={{ width:18, height:3, background:C.grad, borderRadius:99 }}/>}
          </button>
        ))}
      </div>

      {drawer && <Drawer onClose={() => setDrawer(false)} onGo={handleGo} />}
      
      {/* Full-Screen Chat Overlay */}
      {chattingWith && (
        <ChatView 
          otherUser={chattingWith} 
          onBack={() => { setChattingWith(null); if(tab === "messages") { const event = new CustomEvent('bc_new_message', {}); window.dispatchEvent(event); } }} 
          socketRef={socketRef} 
          currentUserId={user.id} 
        />
      )}
    </div>
  );
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<BrewConnect />);
</script>
</body>
</html>
"""

with open("static/index.html", "w", encoding="utf-8") as f:
    f.write(HTML)

print("static/index.html written successfully")
