import React, { useState } from 'react';
import App from './App';
import Scorecard from './Scorecard';
import './Router.css';

type Page = 'dashboard' | 'scorecard';

export default function Router() {
  const [currentPage, setCurrentPage] = useState<Page>('dashboard');

  return (
    <div className="router-container">
      {/* Top Navigation */}
      <nav className="top-nav">
        <div className="nav-brand">
          <span className="nav-logo">🖥️</span>
          <span className="nav-title">Lab Monitoring System</span>
        </div>
        <div className="nav-links">
          <button
            className={`nav-button ${currentPage === 'dashboard' ? 'active' : ''}`}
            onClick={() => setCurrentPage('dashboard')}
          >
            📊 Dashboard
          </button>
          <button
            className={`nav-button ${currentPage === 'scorecard' ? 'active' : ''}`}
            onClick={() => setCurrentPage('scorecard')}
          >
            📋 Scorecard
          </button>
        </div>
      </nav>

      {/* Page Content */}
      <div className="page-content">
        {currentPage === 'dashboard' && <App />}
        {currentPage === 'scorecard' && <Scorecard />}
      </div>
    </div>
  );
}
