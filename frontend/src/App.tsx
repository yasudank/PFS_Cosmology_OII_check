import React, { useState, useEffect } from 'react';
import ImageRater from './components/ImageRater';
import Login from './components/Login';

function App() {
  const [userName, setUserName] = useState<string | null>(null);

  useEffect(() => {
    // Check if user name is in localStorage on initial load
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
  };

  return (
    <div>
      {userName ? (
        <>
          <nav className="navbar navbar-light bg-light sticky-top">
            <div className="container-fluid">
              <span className="navbar-brand mb-0 h1">Image Rating System</span>
              <div>
                <span className="navbar-text me-3">
                  Welcome, {userName}
                </span>
                <button className="btn btn-outline-secondary" onClick={handleLogout}>
                  Logout
                </button>
              </div>
            </div>
          </nav>
          <ImageRater userName={userName} />
        </>
      ) : (
        <Login onLogin={handleLogin} />
      )}
    </div>
  );
}

export default App;
