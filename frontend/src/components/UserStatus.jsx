import React from 'react';
import { Link, useNavigate } from 'react-router-dom';

export default function UserStatus({ user, onLogout }) {
  const navigate = useNavigate();

  const handleLogoutClick = async () => {
    await onLogout();
    navigate('/login');
  };

  return (
    <div style={{ padding: '10px', borderBottom: '1.5px solid black', marginBottom: '10px' }}>
      {user && user.email ? (
        <div>
          <span>Olá, {user.email}</span>
          <Link to="/orders" style={{ marginLeft: '10px' }}>
            <button>Meus Pedidos</button>
          </Link>
          <button onClick={handleLogoutClick} style={{ marginLeft: '10px' }}>Logout</button>
        </div>
      ) : (
        <div>
          <Link to="/login">
            <button>Login</button>
          </Link>
          <Link to="/register" style={{ marginLeft: '10px' }}>
            <button>Register</button>
          </Link>
        </div>
      )}
    </div>
  );
}