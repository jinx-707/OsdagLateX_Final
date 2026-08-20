import React, { useState, useEffect } from 'react';
import api from '../api/axios';

const formatSize = (bytes) => {
  if (!bytes || bytes === 0) return '0 B';
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
  if (bytes < 1073741824) return (bytes / 1048576).toFixed(1) + ' MB';
  return (bytes / 1073741824).toFixed(2) + ' GB';
};

const MAX_STORAGE = 10737418240; // 10 GB default

const StorageWidget = () => {
  const [usage, setUsage] = useState(null);

  useEffect(() => {
    api.get('/files/storage_usage/').then(res => setUsage(res.data)).catch(() => {});
  }, []);

  if (!usage) return null;

  const pct = Math.min((usage.total_bytes / MAX_STORAGE) * 100, 100);
  const barColor = pct > 90 ? '#f87171' : pct > 70 ? '#fbbf24' : '#4ade80';

  return (
    <div className="storage-widget">
      <div className="storage-header">
        <span className="storage-label">Storage</span>
        <span className="storage-detail">{formatSize(usage.total_bytes)} / 10 GB</span>
      </div>
      <div className="storage-bar">
        <div className="storage-fill" style={{ width: pct + '%', background: barColor }} />
      </div>
      <div className="storage-footer">{usage.file_count} file{usage.file_count !== 1 ? 's' : ''}</div>
    </div>
  );
};

export default StorageWidget;
