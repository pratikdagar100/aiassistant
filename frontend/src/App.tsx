import { Route, Routes } from 'react-router-dom'
import { Sidebar } from './components/Sidebar'
import { Dashboard } from './pages/Dashboard'
import { Chat } from './pages/Chat'
import { Models } from './pages/Models'
import { Entities } from './pages/Entities'
import { Memory } from './pages/Memory'
import { Computer } from './pages/Computer'
import { Permissions } from './pages/Permissions'
import { Audit } from './pages/Audit'
import { Tasks } from './pages/Tasks'
import { Learning } from './pages/Learning'
import { Training } from './pages/Training'
import { Settings } from './pages/Settings'
import { Knowledge } from './pages/Knowledge'

function App() {
  return (
    <div className="flex h-screen bg-zinc-950 text-zinc-100">
      <Sidebar />
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/chat" element={<Chat />} />
        <Route path="/models" element={<Models />} />
        <Route path="/entities" element={<Entities />} />
        <Route path="/memory" element={<Memory />} />
        <Route path="/computer" element={<Computer />} />
        <Route path="/permissions" element={<Permissions />} />
        <Route path="/audit" element={<Audit />} />
        <Route path="/tasks" element={<Tasks />} />
        <Route path="/learning" element={<Learning />} />
        <Route path="/training" element={<Training />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="/knowledge" element={<Knowledge />} />
      </Routes>
    </div>
  )
}

export default App
