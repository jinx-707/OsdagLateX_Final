import React, { useState, useEffect } from 'react';
import api from '../api/axios';
import EmptyState from '../components/EmptyState';

const relativeTime = (dateStr) => {
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return mins + 'm ago';
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return hrs + 'h ago';
  const days = Math.floor(hrs / 24);
  if (days < 7) return days + 'd ago';
  return new Date(dateStr).toLocaleDateString();
};

const dayLabel = (dateStr) => {
  const d = new Date(dateStr);
  const today = new Date();
  const yesterday = new Date(today);
  yesterday.setDate(yesterday.getDate() - 1);

  if (d.toDateString() === today.toDateString()) return 'Today';
  if (d.toDateString() === yesterday.toDateString()) return 'Yesterday';
  return d.toLocaleDateString(undefined, { weekday: 'long', month: 'short', day: 'numeric' });
};

const groupByDay = (logs) => {
  const groups = {};
  logs.forEach(log => {
    const key = new Date(log.timestamp).toDateString();
    if (!groups[key]) groups[key] = { label: dayLabel(log.timestamp), items: [] };
    groups[key].items.push(log);
  });
  return Object.values(groups);
};

const Activity = () => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchActivity = async () => {
      try {
        const res = await api.get('/files/activity/');
        setLogs(res.data);
      } catch {
        // silent
      } finally {
        setLoading(false);
      }
    };
    fetchActivity();
  }, []);

  const getActionIcon = (action) => {
    const map = {
      view: '\uD83D\uDC41\uFE0F',
      download: '\u2B07\uFE0F',
      share: '\uD83D\uDD17',
    };
    return map[action] || '\uD83D\uDCCC';
  };

  if (loading) return <div className="loading-state">Loading activity...</div>;

  const grouped = groupByDay(logs);

  return (
    <div className="activity-container">
      <h2 className="page-title">Activity</h2>
      {grouped.length === 0 ? (
        <EmptyState
          icon="\uD83D\uDCCA"
          title="No activity yet"
          description="Activity on your files will appear here."
        />
      ) : (
        <div className="activity-groups">
          {grouped.map((group, gi) => (
            <div key={gi} className="activity-day-group">
              <div className="day-label">{group.label}</div>
              <div className="activity-list">
                {group.items.map(log => (
                  <div key={log.id} className="activity-item">
                    <span className="activity-icon">{getActionIcon(log.action)}</span>
                    <div className="activity-detail">
                      <strong>{log.user.username}</strong>{' '}
                      {log.action === 'share' ? 'shared' : log.action + 'ed'}{' '}
                      <strong>{log.file.filename}</strong>
                      <span className="activity-time">{relativeTime(log.timestamp)}</span>
                      {log.details && Object.keys(log.details).length > 0 && (
                        <div className="activity-meta">
                          {log.details.ip && `IP: ${log.details.ip}`}
                          {log.details.permission && ` (${log.details.permission})`}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default Activity;
