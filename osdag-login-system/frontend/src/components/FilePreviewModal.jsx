import React, { useState, useEffect } from 'react';
import api from '../api/axios';

const PREVIEWABLE = ['pdf', 'jpg', 'jpeg', 'png', 'gif', 'svg', 'txt', 'md', 'json', 'xml', 'csv'];

const getExt = (filename) => filename.split('.').pop().toLowerCase();

const FilePreviewModal = ({ fileId, filename, onClose }) => {
  const [url, setUrl] = useState(null);
  const [textContent, setTextContent] = useState(null);
  const ext = getExt(filename);

  useEffect(() => {
    if (!fileId) return;
    if (['jpg', 'jpeg', 'png', 'gif', 'svg'].includes(ext)) {
      api.get(`/files/${fileId}/download/`, { responseType: 'blob' }).then(res => {
        setUrl(URL.createObjectURL(new Blob([res.data])));
      });
    } else if (['txt', 'md', 'json', 'xml', 'csv'].includes(ext)) {
      api.get(`/files/${fileId}/download/`, { responseType: 'blob' }).then(res => {
        const reader = new FileReader();
        reader.onload = () => setTextContent(reader.result);
        reader.readAsText(res.data);
      });
    } else if (ext === 'pdf') {
      api.get(`/files/${fileId}/download/`, { responseType: 'blob' }).then(res => {
        setUrl(URL.createObjectURL(new Blob([res.data], { type: 'application/pdf' })));
      });
    }
  }, [fileId, ext]);

  useEffect(() => {
    return () => { if (url) URL.revokeObjectURL(url); };
  }, [url]);

  const renderPreview = () => {
    if (['jpg', 'jpeg', 'png', 'gif'].includes(ext) && url) {
      return <img src={url} alt={filename} className="preview-image" />;
    }
    if (ext === 'svg' && url) {
      return <img src={url} alt={filename} className="preview-image" />;
    }
    if (ext === 'pdf' && url) {
      return <iframe src={url} title={filename} className="preview-pdf" />;
    }
    if (textContent !== null) {
      return <pre className="preview-text">{textContent}</pre>;
    }
    return <div className="preview-unavailable">Preview not available for .{ext} files</div>;
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal preview-modal" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h3>{filename}</h3>
          <button className="modal-close" onClick={onClose}>&times;</button>
        </div>
        <div className="preview-body">
          {renderPreview()}
        </div>
      </div>
    </div>
  );
};

export { PREVIEWABLE };
export default FilePreviewModal;
