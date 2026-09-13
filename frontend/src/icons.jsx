// Small inline SVG icon set (stroke-based, like Feather/Lucide) so the app
// doesn't depend on an external icon package or network fetch.
const PATHS = {
  dashboard: 'M3 3h8v8H3zM13 3h8v5h-8zM13 10h8v11h-8zM3 13h8v8H3z',
  loan: 'M4 21h16M5 21V10l7-5 7 5v11M9 21v-7h6v7M4 10h16',
  cash: 'M3 6h18v12H3zM3 10h18M12 10a3 3 0 1 0 0 6 3 3 0 0 0 0-6z',
  wallet: 'M3 7.5A2.5 2.5 0 0 1 5.5 5H18a1 1 0 0 1 1 1v2M3 7.5V18a2 2 0 0 0 2 2h15a1 1 0 0 0 1-1v-8a1 1 0 0 0-1-1H8a2 2 0 0 1 0-4h11',
  piggy: 'M4 12a6 6 0 0 1 6-6c2.2 0 3.7 1 4.8 2.6L17.5 8l1.5 1-1 2v3l-2 2H9.5l-2-2v-1a5 5 0 0 1-3-3zM9 19v2M14 19v2M6.5 11h.01',
  shield: 'M12 3l7 3.2v5.3c0 4.9-3 7.9-7 9-4-1.1-7-4.1-7-9V6.2z',
  card: 'M3 6h18a1 1 0 0 1 1 1v10a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1zM2 10h20M6 15h4',
  calendar: 'M7 3v3M17 3v3M4 8h16M5 6h14a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1z',
  trendUp: 'M3 17l6-6 4 4 8-8M15 7h6v6',
  trendDown: 'M3 7l6 6 4-4 8 8M21 11v6h-6',
  check: 'M4 12l5 5L20 6',
  close: 'M6 6l12 12M18 6L6 18',
}

export default function Icon({ name, size = 18, strokeWidth = 1.8, className }) {
  const d = PATHS[name] || PATHS.dashboard
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={strokeWidth}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      <path d={d} />
    </svg>
  )
}
