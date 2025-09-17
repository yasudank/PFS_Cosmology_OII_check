import React, { useState, useEffect } from 'react';
import { Routes, Route, Link } from 'react-router-dom';
import ImageRater from './components/ImageRater';
import Login from './components/Login';
import SummaryView from './components/SummaryView';

function App() {
  const [userName, setUserName] = useState<string | null>(null);

  useEffect(() => {
    const storedUserName = localStorage.getItem('userName');
    if (storedUserName) {
      setUserName(storedUserName);
    }
  }, []);

  const handleLogin = (name: string) => {
    localStorage.setItem('userName', name);
    setUserName(name);
  };

  const handleLogout = () => {
    localStorage.removeItem('userName');
    setUserName(null);
    // Optionally, redirect to login or home page after logout
    window.location.href = '/';
  };

  // If not logged in, show the Login component for all routes
  if (!userName) {
    return <Login onLogin={handleLogin} />;
  }

  return (
    <div>
      <nav className="navbar navbar-expand-lg navbar-light bg-light sticky-top shadow-sm" style={{ zIndex: 1030 }}>
        <div className="container-fluid">
          <Link className="navbar-brand" to="/">Image Rating System</Link>
          <button className="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav" aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
            <span className="navbar-toggler-icon"></span>
          </button>
          <div className="collapse navbar-collapse" id="navbarNav">
            <ul className="navbar-nav me-auto">
              <li className="nav-item">
                <Link className="nav-link" to="/summary">View Summary</Link>
              </li>
            </ul>
            <div className="d-flex align-items-center">
              <span className="navbar-text me-3">
                Welcome, {userName}
              </span>
              <button className="btn btn-outline-secondary" onClick={handleLogout}>
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>
      
      <main className="container-fluid mt-4">
        <Routes>
          <Route path="/" element={<ImageRater userName={userName} />} />
          <Route path="/rate/:filename" element={<ImageRater userName={userName} />} />
          <Route path="/summary" element={<SummaryView />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;

