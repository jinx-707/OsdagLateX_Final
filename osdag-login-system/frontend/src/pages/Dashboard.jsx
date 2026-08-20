import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../api/axios';
import { Document, Page, pdfjs } from 'react-pdf';

pdfjs.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.min.js`;

const Dashboard = () => {
  const { user } = useAuth();
  const [myFiles, setMyFiles] = useState([]);
  const [sharedFiles, setSharedFiles] = useState([]);
  const [file, setFile] = useState(null);
  const [description, setDescription] = useState('');
  const [uploading, setUploading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState('date');
  const [toast, setToast] = useState(null);
  const [shareModal, setShareModal] = useState({ open: false, fileId: null });
  const [previewModal, setPreviewModal] = useState({ open: false, file: null });
  const [generatedLink, setGeneratedLink] = useState('');
  const [shareEmail, setShareEmail] = useState('');
  const [numPages, setNumPages] = useState(null);
  const fileInputRef = useRef(null);

  const fetchFiles = async () => {
    try {
      const [myRes, sharedRes] = await Promise.all([
        api.get('/files/mine/'),
        api.get('/files/shared/'),
      ]);
      setMyFiles(myRes.data || []);
      setSharedFiles(sharedRes.data || []);
    } catch {
      showToast('Failed to load files', 'error');
    }
  };

  useEffect(() => { fetchFiles(); }, []);

  const showToast = (message, type = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 4000);
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) { showToast('Please select a file', 'error'); return; }
    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);
    if (description) formData.append('description', description);
    try {
      await api.post('/files/', formData, { headers: { 'Content-Type': 'multipart/form-data' } });
      showToast('File uploaded successfully!');
      setFile(null);
      setDescription('');
      if (fileInputRef.current) fileInputRef.current.value = '';
      fetchFiles();
    } catch (err) {
      showToast(err.response?.data?.detail || 'Upload failed', 'error');
    } finally {
      setUploading(false);
    }
  };

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
      showToast(`Downloading ${filename}`);
    } catch {
      showToast('Download failed', 'error');
    }
  };

  const handleDelete = async (fileId, filename) => {
    if (!window.confirm(`Delete "${filename}"? This action cannot be undone.`)) return;
    try {
      await api.delete(`/files/${fileId}/`);
      showToast(`Deleted ${filename}`);
      fetchFiles();
    } catch {
      showToast('Delete failed', 'error');
    }
  };

  const handleShareClick = (fileId) => {
    setShareModal({ open: true, fileId });
    setGeneratedLink('');
    setShareEmail('');
  };

  const handleCreatePublicLink = async () => {
    try {
      const response = await api.post(`/files/${shareModal.fileId}/create-link/`, { expires_in_hours: 24 });
      const linkUrl = `${window.location.origin}/share/${response.data.token}`;
      setGeneratedLink(linkUrl);
      showToast('Public link created!');
    } catch {
      showToast('Failed to create link', 'error');
    }
  };

  const handleShareWithEmail = async () => {
    if (!shareEmail.trim()) { showToast('Please enter an email', 'error'); return; }
    try {
      await api.post(`/files/${shareModal.fileId}/share/`, { email: shareEmail.trim(), permission: 'view' });
      showToast(`Shared with ${shareEmail}`);
      setShareEmail('');
      fetchFiles();
    } catch (err) {
      showToast(err.response?.data?.error || 'Share failed', 'error');
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    showToast('Link copied to clipboard!');
  };

  const closeShareModal = () => {
    setShareModal({ open: false, fileId: null });
    setGeneratedLink('');
    setShareEmail('');
  };

  const handlePreview = (file) => setPreviewModal({ open: true, file });
  const closePreview = () => { setPreviewModal({ open: false, file: null }); setNumPages(null); };

  const getFileIcon = (filename) => {
    const ext = filename?.split('.').pop()?.toLowerCase() || '';
    const icons = {
      pdf: '\uD83D\uDCC4', doc: '\uD83D\uDCDD', docx: '\uD83D\uDCDD',
      jpg: '\uD83D\uDDBC\uFE0F', jpeg: '\uD83D\uDDBC\uFE0F', png: '\uD83D\uDDBC\uFE0F', gif: '\uD83D\uDDBC\uFE0F', svg: '\uD83D\uDDBC\uFE0F',
      zip: '\uD83D\uDCE6', rar: '\uD83D\uDCE6',
      xls: '\uD83D\uDCCA', xlsx: '\uD83D\uDCCA',
      ppt: '\uD83D\uDCD1', pptx: '\uD83D\uDCD1',
      dwg: '\uD83D\uDCD0', dxf: '\uD83D\uDCD0',
      py: '\uD83D\uDC0D', js: '\u26A1', ts: '\uD83D\uDE80',
      txt: '\uD83D\uDCC3', md: '\uD83D\uDCDD',
    };
    return icons[ext] || '\uD83D\uDCCE';
  };

  const formatSize = (bytes) => {
    if (!bytes) return '0 B';
    const units = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${units[i]}`;
  };

  const timeAgo = (date) => {
    const diff = Date.now() - new Date(date).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return 'Just now';
    if (mins < 60) return `${mins}m ago`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs}h ago`;
    const days = Math.floor(hrs / 24);
    return `${days}d ago`;
  };

  const filterFiles = (files) => {
    let filtered = files;
    if (searchTerm) {
      filtered = filtered.filter(f =>
        f.filename?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        f.description?.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }
    const sortMap = {
      date: (a, b) => new Date(b.uploaded_at) - new Date(a.uploaded_at),
      name: (a, b) => (a.filename || '').localeCompare(b.filename || ''),
      size: (a, b) => (b.file_size || 0) - (a.file_size || 0),
    };
    return filtered.sort(sortMap[sortBy] || sortMap.date);
  };

  const filteredMyFiles = filterFiles(myFiles);
  const filteredSharedFiles = filterFiles(sharedFiles);
  const totalSize = myFiles.reduce((sum, f) => sum + (f.file_size || 0), 0);

  return (
    <div className="dashboard-page">
      {toast && <div className={`toast ${toast.type}`}>{toast.message}</div>}

      {/* Top Bar */}
      <div className="top-bar">
        <div className="user-info">
          <div className="avatar">{user?.username?.[0]?.toUpperCase() || 'U'}</div>
          <div>
            <div className="user-name">{user?.username}</div>
            <div className="user-meta">{user?.role} \u00B7 {user?.institution || 'No institution'}</div>
          </div>
        </div>
        <div className="storage-info">
          <span>\uD83D\uDCE6 {formatSize(totalSize)} / 10 GB</span>
          <div className="storage-bar">
            <div className="storage-fill" style={{ width: `${Math.min((totalSize / 10e9) * 100, 100)}%` }} />
          </div>
          <span className="file-count">{myFiles.length} file{myFiles.length !== 1 ? 's' : ''}</span>
        </div>
      </div>

      {/* Upload Zone */}
      <div className="upload-zone" onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => { e.preventDefault(); const dropped = e.dataTransfer.files[0]; if (dropped) setFile(dropped); }}>
        <form onSubmit={handleUpload} className="upload-form">
          <div className="drop-area" onClick={() => fileInputRef.current?.click()}>
            <span className="drop-icon">\u2B07\uFE0F</span>
            <p>{file ? file.name : 'Drop a file here or click to browse'}</p>
            <input ref={fileInputRef} type="file" onChange={(e) => setFile(e.target.files[0])} style={{ display: 'none' }} />
          </div>
          <div className="upload-controls">
            <input type="text" placeholder="Description (optional)" value={description}
              onChange={(e) => setDescription(e.target.value)} className="desc-input" />
            <button type="submit" disabled={uploading} className="upload-btn">
              {uploading ? '\u23F3 Uploading...' : '\u2B06 Upload'}
            </button>
          </div>
        </form>
      </div>

      {/* Toolbar */}
      <div className="toolbar">
        <div className="search-box">
          <span className="search-icon">\uD83D\uDD0D</span>
          <input type="text" placeholder="Search files..." value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)} />
        </div>
        <select value={sortBy} onChange={(e) => setSortBy(e.target.value)} className="sort-select">
          <option value="date">Latest first</option>
          <option value="name">Name A-Z</option>
          <option value="size">Size</option>
        </select>
      </div>

      {/* My Files */}
      <div className="file-section">
        <div className="section-header">
          <h2>\uD83D\uDCC1 My Files <span className="badge">{filteredMyFiles.length}</span></h2>
        </div>
        {filteredMyFiles.length === 0 ? (
          <div className="empty-state">
            <span className="empty-icon">\uD83D\uDCC2</span>
            <h4>{searchTerm ? 'No matching files' : 'No files yet'}</h4>
            <p>{searchTerm ? 'Try a different search.' : 'Upload your first file to get started.'}</p>
          </div>
        ) : (
          <div className="file-grid">
            {filteredMyFiles.map(f => (
              <FileCard key={f.id} file={f} isOwner={true} onDownload={handleDownload}
                onDelete={handleDelete} onShare={handleShareClick} onPreview={handlePreview}
                getFileIcon={getFileIcon} formatSize={formatSize} timeAgo={timeAgo} />
            ))}
          </div>
        )}
      </div>

      {/* Shared With Me */}
      <div className="file-section">
        <div className="section-header">
          <h2>\uD83D\uDD17 Shared With Me <span className="badge">{filteredSharedFiles.length}</span></h2>
        </div>
        {filteredSharedFiles.length === 0 ? (
          <div className="empty-state">
            <span className="empty-icon">\uD83D\uDD17</span>
            <h4>{searchTerm ? 'No matching files' : 'No shared files'}</h4>
            <p>{searchTerm ? 'Try a different search.' : 'Files shared with you will appear here.'}</p>
          </div>
        ) : (
          <div className="file-grid">
            {filteredSharedFiles.map(f => (
              <FileCard key={f.id} file={f} isOwner={false} onDownload={handleDownload}
                onDelete={handleDelete} onShare={handleShareClick} onPreview={handlePreview}
                getFileIcon={getFileIcon} formatSize={formatSize} timeAgo={timeAgo} />
            ))}
          </div>
        )}
      </div>

      {/* Share Modal */}
      {shareModal.open && (
        <div className="modal-overlay" onClick={closeShareModal}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>\uD83D\uDD17 Share File</h3>
              <button className="modal-close" onClick={closeShareModal}>\u2715</button>
            </div>
            <div className="modal-body">
              <div className="share-section">
                <h4>Share with user</h4>
                <div className="share-row">
                  <input type="email" placeholder="Enter email address" value={shareEmail}
                    onChange={(e) => setShareEmail(e.target.value)} className="share-input" />
                  <button onClick={handleShareWithEmail} className="btn-primary">Share</button>
                </div>
              </div>
              <div className="divider">or</div>
              <div className="share-section">
                <h4>Create public link</h4>
                <button onClick={handleCreatePublicLink} className="btn-secondary">
                  \uD83D\uDD17 Generate Public Link
                </button>
                {generatedLink && (
                  <div className="link-result">
                    <input type="text" value={generatedLink} readOnly className="link-input" />
                    <button onClick={() => copyToClipboard(generatedLink)} className="btn-copy">
                      \uD83D\uDCCB Copy
                    </button>
                  </div>
                )}
                <p className="link-hint">Link expires in 24 hours</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Preview Modal */}
      {previewModal.open && previewModal.file && (
        <div className="modal-overlay" onClick={closePreview}>
          <div className="modal large" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>\uD83D\uDCC4 {previewModal.file.filename}</h3>
              <button className="modal-close" onClick={closePreview}>\u2715</button>
            </div>
            <div className="modal-body">
              {previewModal.file.filename?.toLowerCase().endsWith('.pdf') ? (
                <div className="pdf-preview">
                  <Document
                    file={api.getUri() + `/files/${previewModal.file.id}/download/`}
                    onLoadSuccess={({ numPages }) => setNumPages(numPages)}
                    onLoadError={() => showToast('Failed to load PDF', 'error')}
                  >
                    {Array.from({ length: numPages || 1 }, (_, i) => (
                      <Page key={i + 1} pageNumber={i + 1} width={Math.min(window.innerWidth - 120, 750)} />
                    ))}
                  </Document>
                  {numPages && <div className="pdf-page-count">{numPages} page{numPages !== 1 ? 's' : ''}</div>}
                </div>
              ) : ['jpg','jpeg','png','gif','svg'].includes(previewModal.file.filename?.split('.').pop()?.toLowerCase()) ? (
                <div className="image-preview">
                  <img
                    src={api.getUri() + `/files/${previewModal.file.id}/download/`}
                    alt={previewModal.file.filename}
                  />
                </div>
              ) : (
                <div className="preview-placeholder">
                  <span className="preview-icon">{getFileIcon(previewModal.file.filename)}</span>
                  <p>Preview not available for this file type</p>
                  <button onClick={() => handleDownload(previewModal.file.id, previewModal.file.filename)}>
                    \u2B07 Download to view
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

const FileCard = React.memo(({ file, isOwner, onDownload, onDelete, onShare, onPreview, getFileIcon, formatSize, timeAgo }) => {
  const [showMenu, setShowMenu] = useState(false);
  const fileSize = file.file_size || 0;

  const handleCardClick = useCallback(() => onPreview(file), [onPreview, file]);
  const handleDownload = useCallback(() => onDownload(file.id, file.filename), [onDownload, file.id, file.filename]);
  const handleShare = useCallback(() => onShare(file.id), [onShare, file.id]);
  const handleToggleMenu = useCallback(() => setShowMenu(prev => !prev), []);
  const handleDelete = useCallback(() => { setShowMenu(false); onDelete(file.id, file.filename); }, [onDelete, file.id, file.filename]);
  const handleCopyHash = useCallback((e) => { e.stopPropagation(); navigator.clipboard.writeText(file.sha256); }, [file.sha256]);
  const handleActionsClick = useCallback((e) => e.stopPropagation(), []);

  return (
    <div className="file-card" onClick={handleCardClick}>
      <div className="file-icon-large">{getFileIcon(file.filename)}</div>
      <div className="file-info">
        <div className="file-name" title={file.filename}>{file.filename}</div>
        {file.description && <div className="file-desc">{file.description}</div>}
        <div className="file-meta">
          <span>{formatSize(fileSize)}</span>
          <span>\u00B7</span>
          <span>{timeAgo(file.uploaded_at)}</span>
          {file.sha256 && (
            <span className="hash-badge" onClick={handleCopyHash} title="Click to copy SHA-256 hash">
              \uD83D\uDD12 {file.sha256.slice(0, 8)}\u2026
            </span>
          )}
          {!isOwner && file.owner && (
            <span className="owner-badge">by {file.owner.username}</span>
          )}
        </div>
      </div>
      <div className="file-actions" onClick={handleActionsClick}>
        <button className="btn-download" onClick={handleDownload}>
          \u2B07 Download
        </button>
        <button className="btn-share" onClick={handleShare}>
          \uD83D\uDD17 Share
        </button>
        {isOwner && (
          <div className="menu-wrapper">
            <button className="btn-more" onClick={handleToggleMenu}>\u22EF</button>
            {showMenu && (
              <div className="menu-dropdown">
                <button className="menu-item danger" onClick={handleDelete}>
                  \uD83D\uDDD1\uFE0F Delete
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
});

export default Dashboard;
