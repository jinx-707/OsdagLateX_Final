import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../api/axios';

const Settings = () => {
  const { user } = useAuth();
  const [profile, setProfile] = useState({
    username: '',
    email: '',
    institution: '',
    role: 'student',
  });
  const [originalProfile, setOriginalProfile] = useState({});
  const [passwordData, setPasswordData] = useState({
    old_password: '',
    new_password: '',
    confirm_password: '',
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [changingPassword, setChangingPassword] = useState(false);
  const [profileErrors, setProfileErrors] = useState({});
  const [passwordErrors, setPasswordErrors] = useState({});
  const [successMsg, setSuccessMsg] = useState('');
  const [errorMsg, setErrorMsg] = useState('');

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const res = await api.get('/accounts/me/');
        setProfile(res.data);
        setOriginalProfile(res.data);
      } catch (err) {
        console.error('Failed to load profile:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchProfile();
  }, []);

  const handleProfileChange = (e) => {
    const { name, value } = e.target;
    setProfile(prev => ({ ...prev, [name]: value }));
    if (profileErrors[name]) {
      setProfileErrors(prev => ({ ...prev, [name]: undefined }));
    }
  };

  const isProfileChanged = () => {
    return JSON.stringify(profile) !== JSON.stringify(originalProfile);
  };

  const handleProfileSubmit = async (e) => {
    e.preventDefault();
    setProfileErrors({});
    setSuccessMsg('');
    setErrorMsg('');
    if (!isProfileChanged()) {
      setErrorMsg('No changes to save.');
      return;
    }
    setSaving(true);
    try {
      const res = await api.patch('/accounts/me/', profile);
      setOriginalProfile(res.data);
      setProfile(res.data);
      setSuccessMsg('Profile updated successfully!');
    } catch (err) {
      if (err.response?.data) {
        setProfileErrors(err.response.data);
        setErrorMsg('Please fix the errors below.');
      } else {
        setErrorMsg('Failed to update profile.');
      }
    } finally {
      setSaving(false);
    }
  };

  const handlePasswordChange = (e) => {
    const { name, value } = e.target;
    setPasswordData(prev => ({ ...prev, [name]: value }));
    if (passwordErrors[name]) {
      setPasswordErrors(prev => ({ ...prev, [name]: undefined }));
    }
  };

  const handlePasswordSubmit = async (e) => {
    e.preventDefault();
    setPasswordErrors({});
    setSuccessMsg('');
    setErrorMsg('');

    if (passwordData.new_password !== passwordData.confirm_password) {
      setPasswordErrors({ confirm_password: 'Passwords do not match' });
      return;
    }
    if (passwordData.new_password.length < 8) {
      setPasswordErrors({ new_password: 'Password must be at least 8 characters' });
      return;
    }

    setChangingPassword(true);
    try {
      await api.post('/accounts/change-password/', {
        old_password: passwordData.old_password,
        new_password: passwordData.new_password,
      });
      setSuccessMsg('Password changed successfully!');
      setPasswordData({ old_password: '', new_password: '', confirm_password: '' });
    } catch (err) {
      if (err.response?.data) {
        setPasswordErrors(err.response.data);
      } else {
        setErrorMsg('Failed to change password.');
      }
    } finally {
      setChangingPassword(false);
    }
  };

  if (loading) return <div style={{ color: '#94a3b8' }}>Loading profile...</div>;

  const inputStyle = {
    width: '100%',
    padding: '10px 14px',
    background: 'rgba(255,255,255,0.04)',
    border: '1px solid rgba(255,255,255,0.08)',
    borderRadius: '10px',
    color: '#f8fafc',
    fontSize: '14px',
    fontFamily: "'Inter', sans-serif",
  };

  const labelStyle = {
    display: 'block',
    color: '#94a3b8',
    fontSize: '13px',
    fontWeight: '500',
    marginBottom: '4px',
  };

  const sectionStyle = {
    background: 'rgba(255,255,255,0.03)',
    border: '1px solid rgba(255,255,255,0.06)',
    borderRadius: '20px',
    padding: '24px 28px',
    marginBottom: '32px',
  };

  const fieldErrorStyle = {
    color: '#f87171',
    fontSize: '13px',
    display: 'block',
    marginTop: '4px',
  };

  return (
    <div className="settings-container">
      <h2 style={{ color: '#f8fafc', marginBottom: '24px' }}>Settings</h2>

      {successMsg && (
        <div style={{
          background: 'rgba(74,222,128,0.12)',
          border: '1px solid rgba(74,222,128,0.2)',
          color: '#86efac',
          padding: '10px 16px',
          borderRadius: '12px',
          marginBottom: '20px',
          fontSize: '14px',
        }}>
          {successMsg}
        </div>
      )}
      {errorMsg && (
        <div style={{
          background: 'rgba(248,113,113,0.12)',
          border: '1px solid rgba(248,113,113,0.2)',
          color: '#fca5a5',
          padding: '10px 16px',
          borderRadius: '12px',
          marginBottom: '20px',
          fontSize: '14px',
        }}>
          {errorMsg}
        </div>
      )}

      {/* Profile Section */}
      <section style={sectionStyle}>
        <h3 style={{ color: '#e2e8f0', marginBottom: '20px', fontSize: '20px' }}>Profile</h3>
        <form onSubmit={handleProfileSubmit}>
          <div style={{ marginBottom: '16px' }}>
            <label style={labelStyle}>Username</label>
            <input
              name="username"
              value={profile.username || ''}
              onChange={handleProfileChange}
              style={inputStyle}
            />
            {profileErrors.username && <span style={fieldErrorStyle}>{profileErrors.username}</span>}
          </div>

          <div style={{ marginBottom: '16px' }}>
            <label style={labelStyle}>Email</label>
            <input
              name="email"
              type="email"
              value={profile.email || ''}
              onChange={handleProfileChange}
              style={inputStyle}
            />
            {profileErrors.email && <span style={fieldErrorStyle}>{profileErrors.email}</span>}
          </div>

          <div style={{ marginBottom: '16px' }}>
            <label style={labelStyle}>Institution</label>
            <input
              name="institution"
              value={profile.institution || ''}
              onChange={handleProfileChange}
              style={inputStyle}
            />
          </div>

          <div style={{ marginBottom: '20px' }}>
            <label style={labelStyle}>Role</label>
            <select
              name="role"
              value={profile.role || 'student'}
              onChange={handleProfileChange}
              style={inputStyle}
            >
              <option value="student">Student</option>
              <option value="engineer">Engineer</option>
              <option value="admin">Admin</option>
            </select>
          </div>

          <button
            type="submit"
            disabled={!isProfileChanged() || saving}
            style={{
              background: !isProfileChanged() || saving ? 'rgba(255,255,255,0.1)' : 'linear-gradient(135deg, #f59e0b, #d97706)',
              border: 'none',
              padding: '10px 24px',
              borderRadius: '12px',
              fontWeight: '600',
              color: !isProfileChanged() || saving ? '#64748b' : '#0b1120',
              cursor: !isProfileChanged() || saving ? 'not-allowed' : 'pointer',
              transition: 'all 0.2s',
              fontSize: '14px',
            }}
          >
            {saving ? 'Saving...' : 'Save Changes'}
          </button>
        </form>
      </section>

      {/* Change Password Section */}
      <section style={sectionStyle}>
        <h3 style={{ color: '#e2e8f0', marginBottom: '20px', fontSize: '20px' }}>Change Password</h3>
        <form onSubmit={handlePasswordSubmit}>
          <div style={{ marginBottom: '16px' }}>
            <label style={labelStyle}>Current Password</label>
            <input
              type="password"
              name="old_password"
              value={passwordData.old_password}
              onChange={handlePasswordChange}
              style={inputStyle}
            />
            {passwordErrors.old_password && <span style={fieldErrorStyle}>{passwordErrors.old_password}</span>}
          </div>

          <div style={{ marginBottom: '16px' }}>
            <label style={labelStyle}>New Password</label>
            <input
              type="password"
              name="new_password"
              value={passwordData.new_password}
              onChange={handlePasswordChange}
              style={inputStyle}
            />
            {passwordErrors.new_password && <span style={fieldErrorStyle}>{passwordErrors.new_password}</span>}
          </div>

          <div style={{ marginBottom: '20px' }}>
            <label style={labelStyle}>Confirm New Password</label>
            <input
              type="password"
              name="confirm_password"
              value={passwordData.confirm_password}
              onChange={handlePasswordChange}
              style={inputStyle}
            />
            {passwordErrors.confirm_password && <span style={fieldErrorStyle}>{passwordErrors.confirm_password}</span>}
          </div>

          <button
            type="submit"
            disabled={changingPassword}
            style={{
              background: changingPassword ? 'rgba(255,255,255,0.1)' : 'linear-gradient(135deg, #f59e0b, #d97706)',
              border: 'none',
              padding: '10px 24px',
              borderRadius: '12px',
              fontWeight: '600',
              color: changingPassword ? '#64748b' : '#0b1120',
              cursor: changingPassword ? 'not-allowed' : 'pointer',
              transition: 'all 0.2s',
              fontSize: '14px',
            }}
          >
            {changingPassword ? 'Changing...' : 'Change Password'}
          </button>
        </form>
      </section>

      {/* Account Info */}
      <section style={sectionStyle}>
        <h3 style={{ color: '#e2e8f0', marginBottom: '16px', fontSize: '20px' }}>Account Info</h3>
        <p style={{ color: '#94a3b8', marginBottom: '16px' }}>
          Joined: {user?.created_at ? new Date(user.created_at).toLocaleDateString('en-US', { month: 'long', year: 'numeric' }) : 'Unknown'}
        </p>
        <div style={{
          marginTop: '16px',
          padding: '16px',
          border: '1px dashed rgba(239,68,68,0.2)',
          borderRadius: '12px',
        }}>
          <button
            disabled
            style={{
              background: 'rgba(239,68,68,0.1)',
              border: '1px solid rgba(239,68,68,0.2)',
              color: '#fca5a5',
              padding: '6px 16px',
              borderRadius: '30px',
              cursor: 'not-allowed',
              opacity: 0.6,
              fontSize: '13px',
            }}
          >
            Delete Account (not available)
          </button>
          <p style={{ color: '#64748b', fontSize: '13px', marginTop: '8px' }}>
            This action is irreversible and not implemented in this version.
          </p>
        </div>
      </section>
    </div>
  );
};

export default Settings;
