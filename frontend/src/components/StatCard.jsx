import Icon from '../icons.jsx'

const TONE_ICON = {
  good: 'trendUp',
  danger: 'trendDown',
  warn: 'calendar',
}

export default function StatCard({ label, value, sub, tone, icon }) {
  return (
    <div className={`stat-card${tone ? ` tone-${tone}` : ''}`}>
      <div className="stat-icon-wrap">
        <Icon name={icon || TONE_ICON[tone] || 'cash'} size={17} />
      </div>
      <div className="stat-label">{label}</div>
      <div className="stat-value">{value}</div>
      {sub && <div className="stat-sub">{sub}</div>}
    </div>
  )
}
