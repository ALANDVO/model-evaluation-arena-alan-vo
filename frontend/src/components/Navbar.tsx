import React from 'react';
import { useAuth } from '../context/AuthContext';

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

export const Navbar: React.FC<NavbarProps> = ({ activeTab, setActiveTab }) => {
  const { user, demoMode, loginAsDemo, logout } = useAuth();

  return (
    <header className="navbar">
      <div className="navbar-container">
        <div className="navbar-brand">
          <div className="brand-logo">⚔️</div>
          <div>
            <h1 className="brand-title">Model Evaluation Arena</h1>
            <p className="brand-subtitle">Alan Vo &bull; AI & Machine Learning</p>
          </div>
        </div>

        <nav className="navbar-links">
          <button
            className={`nav-btn ${activeTab === 'arena' ? 'active' : ''}`}
            onClick={() => setActiveTab('arena')}
          >
            Arena Benchmark
          </button>
          <button
            className={`nav-btn ${activeTab === 'datasets' ? 'active' : ''}`}
            onClick={() => setActiveTab('datasets')}
          >
            Datasets & Models
          </button>
          <button
            className={`nav-btn ${activeTab === 'slices' ? 'active' : ''}`}
            onClick={() => setActiveTab('slices')}
          >
            Cohort Slices
          </button>
          <button
            className={`nav-btn ${activeTab === 'reports' ? 'active' : ''}`}
            onClick={() => setActiveTab('reports')}
          >
            Advisory & Audit
          </button>
        </nav>

        <div className="navbar-user">
          {demoMode && (
            <div className="demo-selector">
              <span className="demo-label">Role:</span>
              <select
                className="role-dropdown"
                value={user?.roles?.[0] || 'analyst'}
                onChange={(e) => loginAsDemo(e.target.value)}
              >
                <option value="analyst">Analyst</option>
                <option value="admin">Admin</option>
                <option value="viewer">Viewer</option>
              </select>
            </div>
          )}
          {user ? (
            <div className="user-badge">
              <span className="username">{user.username}</span>
              <button className="logout-btn" onClick={logout}>Sign out</button>
            </div>
          ) : (
            <button className="login-btn" onClick={() => loginAsDemo('analyst')}>Sign in</button>
          )}
        </div>
      </div>
    </header>
  );
};
