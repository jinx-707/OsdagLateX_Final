import React from 'react';
import { Outlet, useLocation, Link } from 'react-router-dom';
import Sidebar from './Sidebar';

const routeNames = {
  '/dashboard': 'My Files',
  '/shared': 'Shared With Me',
  '/teams': 'Teams',
  '/activity': 'Activity',
  '/settings': 'Settings',
};

const Breadcrumbs = () => {
  const location = useLocation();
  const name = routeNames[location.pathname];
  if (!name) return null;
  return (
    <div className="breadcrumbs">
      <Link to="/dashboard" className="breadcrumb-link">Home</Link>
      <span className="breadcrumb-sep">/</span>
      <span className="breadcrumb-current">{name}</span>
    </div>
  );
};

const Layout = () => {
  return (
    <div className="layout-wrapper">
      <Sidebar />
      <div className="content-area">
        <Breadcrumbs />
        <Outlet />
      </div>
    </div>
  );
};

export default Layout;
