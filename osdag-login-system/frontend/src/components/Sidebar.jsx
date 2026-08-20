import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import './Sidebar.css';

const Sidebar = () => {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navItems = [
    { path: '/dashboard', label: 'My Files', icon: '\uD83D\uDCC1' },
    { path: '/shared', label: 'Shared With Me', icon: '\uD83D\uDD17' },
    { path: '/teams', label: 'Teams', icon: '\uD83D\uDC65' },
    { path: '/activity', label: 'Activity', icon: '\uD83D\uDCCA' },
    { path: '/settings', label: 'Settings', icon: '\u2699\uFE0F' },
  ];

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <span className="logo">Osdag Vault</span>
      </div>
      <nav className="sidebar-nav">
        {navItems.map((item) => (
          <Link
            key={item.path}
            to={item.path}
            className={`nav-item ${location.pathname === item.path ? 'active' : ''}`}
          >
            <span className="nav-icon">{item.icon}</span>
            <span className="nav-label">{item.label}</span>
          </Link>
        ))}
      </nav>
      <div className="sidebar-footer">
        <div className="user-info" onClick={() => navigate('/settings')}>
          <div className="user-avatar">
            {user?.username ? user.username[0].toUpperCase() : '?'}
          </div>
          <span className="username">{user?.username}</span>
        </div>
        <button className="logout-btn-sidebar" onClick={handleLogout}>
          Log Out
        </button>
      </div>
    </div>
  );
};

export default Sidebar;
