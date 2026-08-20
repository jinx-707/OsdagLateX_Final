import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import api from '../api/axios';

const formatSize = (bytes) => {
  if (!bytes || bytes === 0) return '';
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / 1048576).toFixed(1) + ' MB';
};

const MagicLinkPage = () => {
  const { token } = useParams();
  const [info, setInfo] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get(`/share/${token}/info/`)
      .then(res => setInfo(res.data))
      .catch(err => {
        if (err.response?.status === 410) setError('This link has expired.');
        else setError('Invalid or expired link.');
      })
      .finally(() => setLoading(false));
  }, [token]);

  const handleDownload = () => {
    window.open(`/api/share/${token}/download/`, '_blank');
  };

  if (loading) return (
    <div className="magic-page">
      <div className="magic-card">Loading...</div>
    </div>
  );

  if (error) return (
    <div className="magic-page">
      <div className="magic-card magic-error">
        <span className="magic-error-icon">\u26A0\uFE0F</span>
        <h2>Link Unavailable</h2>
        <p>{error}</p>
      </div>
    </div>
  );

  return (
    <div className="magic-page">
      <div className="magic-card">
        <div className="magic-logo">Osdag Vault</div>
        <div className="magic-file-icon">\uD83D\uDCC1</div>
        <h2>{info.filename}</h2>
        {info.description && <p className="magic-desc">{info.description}</p>}
        <div className="magic-meta">
          {info.file_size > 0 && <span>{formatSize(info.file_size)}</span>}
          <span>Uploaded {new Date(info.uploaded_at).toLocaleDateString()}</span>
        </div>
        {info.expires_at && (
          <p className="magic-expiry">
            Link expires: {new Date(info.expires_at).toLocaleString()}
          </p>
        )}
        <button className="btn-primary magic-download" onClick={handleDownload}>
          \u2B07 Download File
        </button>
      </div>
    </div>
  );
};

export default MagicLinkPage;
