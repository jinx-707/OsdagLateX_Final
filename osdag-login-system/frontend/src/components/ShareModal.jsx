import React, { useState, useEffect } from 'react';
import api from '../api/axios';

const ShareModal = ({ fileId, onClose, onShared, showToast }) => {
  const [email, setEmail] = useState('');
  const [permission, setPermission] = useState('view');
  const [expiresAt, setExpiresAt] = useState('');
  const [currentShares, setCurrentShares] = useState([]);
  const [loading, setLoading] = useState(false);
  const [magicLink, setMagicLink] = useState(null);
  const [linkLoading, setLinkLoading] = useState(false);

  useEffect(() => {
    if (!fileId) return;
    api.get(`/files/${fileId}/`).then(res => {
      setCurrentShares(res.data.access_grants || []);
    }).catch(() => {});
  }, [fileId]);

  const handleShare = async () => {
    if (!email.trim()) return;
    setLoading(true);
    try {
      await api.post(`/files/${fileId}/share/`, {
        email: email.trim(),
        permission,
        expires_at: expiresAt || null,
      });
      showToast?.(`Shared with ${email.trim()}`);
      onShared?.();
      onClose();
    } catch (err) {
      showToast?.(err.response?.data?.error || 'Share failed', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleRevoke = async (userId) => {
    if (!window.confirm('Revoke access for this user?')) return;
    try {
      await api.post(`/files/${fileId}/revoke/`, { user_id: userId });
      setCurrentShares(prev => prev.filter(s => s.shared_with?.id !== userId));
      showToast?.('Access revoked');
      onShared?.();
    } catch (err) {
      showToast?.('Revoke failed', 'error');
    }
  };

  const handleCreateMagicLink = async () => {
    setLinkLoading(true);
    try {
      const res = await api.post(`/files/${fileId}/create-link/`, {
        expires_in_hours: 24,
      });
      const url = `${window.location.origin}/share/${res.data.token}`;
      setMagicLink(url);
    } catch {
      showToast?.('Could not create link', 'error');
    } finally {
      setLinkLoading(false);
    }
  };

  const copyLink = () => {
    navigator.clipboard.writeText(magicLink);
    showToast?.('Link copied!');
  };

  if (!fileId) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal share-modal" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h3>Share File</h3>
          <button className="modal-close" onClick={onClose}>&times;</button>
        </div>

        <div className="share-section">
          <div className="share-form-row">
            <input
              type="email"
              placeholder="Enter email address"
              value={email}
              onChange={e => setEmail(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleShare()}
            />
            <select value={permission} onChange={e => setPermission(e.target.value)}>
              <option value="view">View</option>
              <option value="edit">Edit</option>
            </select>
          </div>
          <div className="share-form-row">
            <label className="expiry-label">
              <span>Expires:</span>
              <input
                type="datetime-local"
                value={expiresAt}
                onChange={e => setExpiresAt(e.target.value)}
              />
            </label>
            <button
              className="btn-primary"
              onClick={handleShare}
              disabled={loading || !email.trim()}
            >
              {loading ? 'Sharing...' : 'Share'}
            </button>
          </div>
        </div>

        {currentShares.length > 0 && (
          <div className="current-shares">
            <h4>Current Shares</h4>
            {currentShares.map(grant => (
              <div key={grant.id} className="share-item">
                <div className="share-item-info">
                  <span className="share-email">{grant.shared_with?.email}</span>
                  <span className={`share-perm perm-${grant.permission}`}>
                    {grant.permission}
                  </span>
                  {grant.expires_at && (
                    <span className="share-expiry">
                      exp. {new Date(grant.expires_at).toLocaleDateString()}
                    </span>
                  )}
                  {grant.is_expired && <span className="share-expired">expired</span>}
                </div>
                <button
                  className="btn-revoke"
                  onClick={() => handleRevoke(grant.shared_with?.id)}
                >
                  Revoke
                </button>
              </div>
            ))}
          </div>
        )}

        <div className="magic-link-section">
          <button
            className="btn-secondary"
            onClick={handleCreateMagicLink}
            disabled={linkLoading}
          >
            {linkLoading ? 'Creating...' : 'Create Public Link'}
          </button>
          {magicLink && (
            <div className="magic-link-result">
              <input readOnly value={magicLink} onClick={e => e.target.select()} />
              <button className="btn-copy" onClick={copyLink}>Copy</button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ShareModal;
