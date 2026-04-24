import { useState, useRef, useEffect } from 'react'
import './index.css'

function App() {
  const [leftText, setLeftText] = useState('')
  const [rightText, setRightText] = useState('')
  const [smartTags, setSmartTags] = useState([])
  const [meetingUrl, setMeetingUrl] = useState('https://meet.google.com/dov-mcry-hxr')
  const [botStatus, setBotStatus] = useState({ is_running: false, transcribing: false, logs: [] })
  const [activeTab, setActiveTab] = useState('Archive')
  const [activeNav, setActiveNav] = useState('Workspace')
  const [archiveData, setArchiveData] = useState([])
  const [isSaving, setIsSaving] = useState(false)
  
  const debounceRef = useRef(null)
  const leftTextRef = useRef(leftText)
  
  useEffect(() => { leftTextRef.current = leftText }, [leftText])
  
  // Poll bot status
  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const res = await fetch('http://127.0.0.1:8000/api/meeting/status')
        if (res.ok) {
          const data = await res.json()
          setBotStatus(data)
          if (data.last_transcript && data.last_transcript !== leftTextRef.current && !data.transcribing) {
             const updatedText = leftTextRef.current + (leftTextRef.current ? '\n' : '') + "[BOT]: " + data.last_transcript
             setLeftText(updatedText)
             handleTextUpdateEffect(updatedText)
          }
        }
      } catch (err) { /* Silent fail */ }
    }, 3000)
    return () => clearInterval(interval)
  }, [])

  // Fetch Archive when clicking Archive
  useEffect(() => {
    if (activeNav === 'Archive') {
      fetch('http://127.0.0.1:8000/api/archive')
        .then(res => res.json())
        .then(data => setArchiveData(data))
        .catch(err => console.error(err))
    }
  }, [activeNav])

  const handleTextUpdateEffect = (text) => {
    const lines = text.split('\n')
    const tags = lines.filter(line => {
      const l = line.trim().toLowerCase()
      return l.startsWith('task:') || l.startsWith('action:') || l.startsWith('update:') || l.startsWith('bug:') || l.startsWith('goal:')
    })
    setSmartTags(tags)

    if (debounceRef.current) clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(async () => {
      try {
        const response = await fetch('http://127.0.0.1:8000/api/translate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text })
        });
        if (response.ok) {
          const data = await response.json()
          setRightText(data.translated_text)
        }
      } catch (error) {}
    }, 1200)
  }

  const joinMeeting = async () => {
    if (!meetingUrl) return alert("Please enter a meeting URL")
    try {
      const res = await fetch('http://127.0.0.1:8000/api/meeting/join', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: meetingUrl, name: "Roman-Scribe Assistant" })
      })
      if (res.ok) {
        setBotStatus(prev => ({ ...prev, is_running: true }))
      }
    } catch (err) {}
  }

  const stopMeeting = async () => {
    try {
      setBotStatus(prev => ({ ...prev, transcribing: true }))
      const res = await fetch('http://127.0.0.1:8000/api/meeting/stop', { method: 'POST' })
      if (res.ok) {
        const data = await res.json()
        if (data.transcript) {
          const updatedText = leftTextRef.current + "\n[MEETING SUMMARY]: " + data.transcript
          setLeftText(updatedText)
          handleTextUpdateEffect(updatedText)
        }
      }
    } catch (err) {}
  }

  const handleTextChange = (e) => {
    const text = e.target.value
    setLeftText(text)
    handleTextUpdateEffect(text)
  }

  const saveSession = async () => {
    if (!leftText) return
    setIsSaving(true)
    try {
      const res = await fetch('http://127.0.0.1:8000/api/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: `Session ${new Date().toLocaleTimeString()}`,
          content_raw: leftText,
          content_urdu: rightText,
          tags: smartTags
        })
      })
      if (res.ok) {
        alert("Session saved successfully!")
      }
    } catch (e) { alert("Save failed.") }
    finally { setIsSaving(false) }
  }

  const addTask = () => {
    const textToAdd = "\nTask: New item at " + new Date().toLocaleTimeString()
    const updatedText = leftText + textToAdd
    setLeftText(updatedText)
    handleTextUpdateEffect(updatedText)
  }

  const exportPDF = async () => {
    try {
      const resp = await fetch('http://127.0.0.1:8000/api/export', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ english_text: leftText, urdu_text: rightText })
      })
      if (resp.ok) {
        const blob = await resp.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = 'RomanScribe_Notes.pdf'
        a.click()
      }
    } catch (e) { console.error(e) }
  }

  return (
    <div className="app-container">
      {/* Left Sidebar */}
      <aside className="sidebar-left">
        <div className="logo-container">
          <h1 onClick={() => setActiveNav('Workspace')} style={{cursor: 'pointer'}}>Roman-Scribe AI</h1>
        </div>
        
        <nav className="nav-links">
          <div className={`nav-item ${activeNav === 'AI Scribe' || activeNav === 'Workspace' ? 'active' : ''}`} onClick={() => setActiveNav('Workspace')}>
            <span className="icon">📝</span> AI Scribe
          </div>
          <div className={`nav-item ${activeNav === 'Archive' ? 'active' : ''}`} onClick={() => setActiveNav('Archive')}>
            <span className="icon">📊</span> Archive
          </div>
          <div className={`nav-item ${activeNav === 'Logs' ? 'active' : ''}`} onClick={() => setActiveNav('Logs')}>
            <span className="icon">📜</span> Logs
          </div>
          <div className="nav-item" onClick={saveSession}><span className="icon">💾</span> {isSaving ? "Saving..." : "Save Now"}</div>
        </nav>

        <div className="console-mini">
          <h3>Recent activity</h3>
          <div className="logs">
            {(botStatus.logs || []).slice(-4).map((log, i) => (
              <div key={i} style={{marginBottom: '4px', opacity: 1 - (i*0.1)}}>
                &gt; {log.substring(0, 30)}...
              </div>
            ))}
            {(!botStatus.logs || botStatus.logs.length === 0) && <div>&gt; System Ready.</div>}
          </div>
        </div>

        <button className="nav-item" onClick={exportPDF} style={{border: 'none', background:'none', width:'100%', marginTop: '20px', textAlign: 'left', padding: '12px 16px'}}>
           <span className="icon">📁</span> Export PDF
        </button>

        <div className="footer-info">
          <div>● System Online</div>
          <div>Encryption: AES-256</div>
          <div>Local Buffer: 12.4 MB</div>
        </div>
      </aside>

      {/* Top Navigation / Header */}
      <header className="top-nav">
        <div className="tabs">
          <div className={`tab ${activeTab === 'Meetings' ? 'active' : ''}`} onClick={() => setActiveTab('Meetings')}>Meetings</div>
          <div className={`tab ${activeTab === 'Archive' ? 'active' : ''}`} onClick={() => setActiveTab('Archive')}>Archive</div>
          <div className={`tab ${activeTab === 'Settings' ? 'active' : ''}`} onClick={() => setActiveTab('Settings')}>Settings</div>
        </div>

        <div className="header-actions">
          <div className="search-bar">
            <input 
              placeholder="Google Meet / Zoom URL" 
              value={meetingUrl}
              onChange={(e) => setMeetingUrl(e.target.value)}
            />
            {botStatus.is_running && <span style={{fontSize: '0.65rem', color: '#00796b', fontWeight: '700', marginLeft: '8px'}}>ACTIVE ●</span>}
          </div>
          
          {!botStatus.is_running ? (
            <button className="btn-join" onClick={joinMeeting}>Join Meeting</button>
          ) : (
            <button className="btn-join" style={{background: '#d32f2f'}} onClick={stopMeeting}>
              {botStatus.transcribing ? 'Analyzing...' : 'Stop Bot'}
            </button>
          )}
          
          <div className="user-avatar" style={{width: '32px', height: '32px', borderRadius: '50%', background: '#eee', display:'flex', alignItems:'center', justifyContent:'center', fontSize:'1rem'}}>👤</div>
        </div>
      </header>

      {/* Main Content Area */}
      {activeNav === 'Workspace' && (
        <main className="main-content">
          <div className="content-header">
            <div className="title-section">
              <h2>Executive Briefing</h2>
              <p>Weekly Strategic Review • {new Date().toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}</p>
            </div>
            <div className="mode-pills">
              <div className="pill">Roman-Urdu Mode</div>
              <div className="pill">Live Syncing</div>
            </div>
          </div>

          <div className="briefing-panel">
            <section className="pane pane-left">
              <div className="pane-label"><span>🖋️</span> Transcription Feed</div>
              <textarea 
                value={leftText} 
                onChange={handleTextChange} 
                placeholder="11:00 AM: Meeting start ho gayi hai..."
              />
            </section>
            
            <section className="pane pane-right">
              <div className="pane-label" style={{justifyContent: 'flex-end'}}><span>✨</span> نستعلیق آئینہ</div>
              <div className="urdu-mirror">
                {rightText || <span style={{opacity: 0.1}}>اردو متن یہاں آئے گا...</span>}
              </div>
            </section>
          </div>
        </main>
      )}

      {activeNav === 'Archive' && (
        <main className="main-content">
          <div className="content-header">
            <div className="title-section">
              <h2>Archives</h2>
              <p>Previous Meeting Sessions</p>
            </div>
          </div>
          <div className="briefing-panel" style={{flexDirection: 'column', padding: '20px', gap: '15px', overflowY: 'auto'}}>
            {archiveData.length === 0 && <p style={{color: 'var(--text-muted)'}}>No archived sessions found.</p>}
            {archiveData.map(note => (
              <div key={note.id} className="task-card" style={{flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center'}}>
                <div>
                  <h4 style={{fontSize: '1.1rem'}}>{note.title}</h4>
                  <p>{new Date(note.created_at).toLocaleString()}</p>
                </div>
                <button className="btn-join" style={{fontSize: '0.8rem', padding: '8px 16px'}} onClick={() => {
                   setLeftText(note.content_raw)
                   setRightText(note.content_urdu)
                   setActiveNav('Workspace')
                }}>Load Session</button>
              </div>
            ))}
          </div>
        </main>
      )}

      {activeNav === 'Logs' && (
        <main className="main-content">
          <div className="content-header">
            <div className="title-section">
              <h2>System Logs</h2>
              <p>Live Bot Session History</p>
            </div>
          </div>
          <div className="briefing-panel" style={{background: '#1a1e23', color: '#a0aec0', fontFamily: 'monospace', padding: '40px', overflowY: 'auto'}}>
             <div style={{fontSize: '0.9rem', lineHeight: '1.6'}}>
                {botStatus.logs.map((log, i) => (
                  <div key={i} style={{marginBottom: '8px'}}>&gt; {log}</div>
                ))}
                {botStatus.logs.length === 0 && <div>&gt; No session activity recorded.</div>}
             </div>
          </div>
        </main>
      )}

      {/* Right Sidebar */}
      <aside className="sidebar-right">
        <div className="section-header">
          <h3>Smart Tasks</h3>
          <span className="badge-new">{smartTags.length} NEW</span>
        </div>

        <div className="task-list">
          {smartTags.map((tag, idx) => (
            <div className="task-card" key={idx}>
              <div className="task-top">
                <div className="task-checkbox"></div>
                <div>
                  <h4>{tag.split(':')[1]?.trim() || tag}</h4>
                  <p>Assigned to: Team AI</p>
                </div>
              </div>
              <div className="task-meta">
                <span className="tag-time">🕒 Today, 2:30 PM</span>
                {tag.toLowerCase().includes('urgent') && <span className="tag-urgent">! Urgent</span>}
              </div>
            </div>
          ))}
          {smartTags.length === 0 && (
            <>
              <div className="task-card">
                <div className="task-top">
                  <div className="task-checkbox checked"></div>
                  <div>
                    <h4>Follow up on deliverables</h4>
                    <p>Assigned to: Design Team</p>
                  </div>
                </div>
                <div className="task-meta">
                  <span className="tag-time">🕒 Today, 2:30 PM</span>
                </div>
              </div>
              <div className="task-card">
                <div className="task-top">
                  <div className="task-checkbox"></div>
                  <div>
                    <h4>Arrange stakeholder meeting</h4>
                    <p>Priority: High</p>
                  </div>
                </div>
                <div className="task-meta">
                   <span className="tag-urgent">! Urgent</span>
                </div>
              </div>
            </>
          )}
        </div>

        <div className="ai-suggestion">
           <span style={{fontSize: '1.5rem'}}>💡</span>
           <p>AI Suggestion: Create a task for budget reconciliation?</p>
           <button className="btn-text-action" onClick={addTask}>Add Task</button>
        </div>
      </aside>

      {/* Floating Action Button */}
      <button className="btn-generate-floating" onClick={exportPDF}>
         <span style={{fontSize: '1.2rem'}}>📄</span> Generate PDF Report ➔
      </button>
    </div>
  )
}

export default App
