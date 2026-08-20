import React from 'react';

const EmptyState = ({ icon, title, description }) => (
  <div className="empty-state">
    <span className="empty-icon">{icon}</span>
    <h4>{title}</h4>
    <p>{description}</p>
  </div>
);

export default EmptyState;
