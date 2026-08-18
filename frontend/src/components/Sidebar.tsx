import { NavLink } from 'react-router-dom'

interface NavItem {
  label: string
  path: string
}

const NAV_ITEMS: NavItem[] = [
  { label: 'Dashboard', path: '/' },
  { label: 'Live Chat', path: '/chat' },
  { label: 'Entities', path: '/entities' },
  { label: 'Memory', path: '/memory' },
  { label: 'Knowledge', path: '/knowledge' },
  { label: 'Computer Control', path: '/computer' },
  { label: 'Tasks', path: '/tasks' },
  { label: 'Learning', path: '/learning' },
  { label: 'Training', path: '/training' },
  { label: 'Models', path: '/models' },
  { label: 'Permissions', path: '/permissions' },
  { label: 'Audit', path: '/audit' },
  { label: 'Settings', path: '/settings' },
]

export function Sidebar() {
  return (
    <nav className="flex h-full w-56 flex-col gap-1 border-r border-zinc-800 bg-zinc-950 p-4">
      <div className="mb-4 px-2 text-lg font-semibold text-zinc-100">PratikAI</div>
      {NAV_ITEMS.map((item) => (
        <NavLink
          key={item.path}
          to={item.path}
          end
          className={({ isActive }) =>
            `rounded-md px-3 py-2 text-sm font-medium transition-colors ${
              isActive ? 'bg-violet-600/20 text-violet-300' : 'text-zinc-300 hover:bg-zinc-800 hover:text-zinc-100'
            }`
          }
        >
          {item.label}
        </NavLink>
      ))}
    </nav>
  )
}
