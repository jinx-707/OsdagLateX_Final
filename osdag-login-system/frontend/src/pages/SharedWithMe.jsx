import React, { useState, useEffect } from 'react';
import api from '../api/axios';
import EmptyState from '../components/EmptyState';

const getFileIcon = (filename) => {
  const ext = filename.split('.').pop().toLowerCase();
  const map = {
    pdf: { icon: '\uD83D\uDCC4', color: '#f87171' },
    doc: { icon: '\uD83D\uDCDD', color: '#60a5fa' },
    docx: { icon: '\uD83D\uDCDD', color: '#60a5fa' },
    xls: { icon: '\uD83D\uDCCA', color: '#34d399' },
    xlsx: { icon: '\uD83D\uDCCA', color: '#34d399' },
    dwg: { icon: '\uD83D\uDCD0', color: '#38bdf8' },
    dxf: { icon: '\uD83D\uDCD0', color: '#38bdf8' },
    jpg: { icon: '\uD83D\uDDBC\uFE0F', color: '#fbbf24' },
    jpeg: { icon: '\uD83D\uDDBC\uFE0F', color: '#fbbf24' },
    png: { icon: '\uD83D\uDDBC\uFE0F', color: '#fbbf24' },
    zip: { icon: '\uD83D\uDCE6', color: '#a78bfa' },
    txt: { icon: '\uD83D\uDCC3', color: '#94a3b8' },
  };
  return map[ext] || { icon: '\uD83D\uDCCE', color: '#94a3b8' };
};

const formatSize = (bytes) => {
  if (!bytes || bytes === 0) return '';
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / 1048576).toFixed(1) + ' MB';
};

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

const SharedWithMe = () => {
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState(null);
  const [search, setSearch] = useState('');

  const showToast = (message, type = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4000);
  };

  useEffect(() => {
    const fetchShared = async () => {
      try {
        const res = await api.get('/files/shared/');
        setFiles(res.data);
      } catch {
        showToast('Failed to load shared files', 'error');
      } finally {
        setLoading(false);
      }
    };
    fetchShared();
  }, []);

  const handleDownload = async (fileId, filename) => {
    try {
      const response = await api.get(`/files/${fileId}/download/`, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch {
      showToast('Download failed', 'error');
    }
  };

  const filtered = search.trim()
    ? files.filter(f => f.filename.toLowerCase().includes(search.toLowerCase()))
    : files;

  if (loading) return <div className="loading-state">Loading shared files...</div>;

  return (
    <div className="dashboard-container">
      <div className="top-bar">
        <h2 className="page-title">Shared With Me</h2>
      </div>

      <div className="file-toolbar">
        <input
          type="text"
          className="search-input"
          placeholder="Search shared files..."
          value={search}
          onChange={e => setSearch(e.target.value)}
        />
      </div>

      <div className="file-section">
        <div className="file-grid">
          {filtered.length === 0 ? (
            <EmptyState
              icon="\uD83D\uDD17"
              title={search ? 'No matching files' : 'No shared files'}
              description={search ? 'Try a different search.' : 'Files shared with you will appear here.'}
            />
          ) : (
            filtered.map(f => {
              const iconInfo = getFileIcon(f.filename);
              return (
                <div key={f.id} className="file-card">
                  <div className="file-card-top">
                    <div className="file-icon" style={{ color: iconInfo.color }}>
                      {iconInfo.icon}
                    </div>
                    <div className="file-info">
                      <div className="file-name" title={f.filename}>{f.filename}</div>
                      {f.description && <div className="file-desc">{f.description}</div>}
                      <div className="file-meta">
                        <span className="file-date">{relativeTime(f.uploaded_at)}</span>
                        {f.file_size > 0 && <span className="file-size">{formatSize(f.file_size)}</span>}
                        {f.owner && <span className="owner-badge">{f.owner.username}</span>}
                      </div>
                    </div>
                  </div>
                  <div className="file-actions">
                    <button className="btn-action btn-download" onClick={() => handleDownload(f.id, f.filename)}>
                      \u2B07 Download
                    </button>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>

      {toast && <div className={`toast ${toast.type}`}>{toast.message}</div>}
    </div>
  );
};

export default SharedWithMe;
