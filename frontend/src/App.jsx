import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, Navigate } from 'react-router-dom';
import ProductList from './components/ProductList';
import Cart from './components/Cart';
import Checkout from './components/Checkout';
import Login from './components/Login';
import Register from './components/Register';
import UserStatus from './components/UserStatus';
import OrderHistory from './components/OrderHistory';
import Payment from './components/Payment';
import axios from 'axios';

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchUser = async () => {
    try {
      const res = await axios.get('/auth/user');
      setUser(res.data);
    } catch (error) {
      console.error('Nenhum usuário logado', error);
      setUser(null);
    } finally {
        setLoading(false);
    }
  };

  useEffect(() => {
    fetchUser();
  }, []);

  const handleLogout = async () => {
    try {
      await axios.post('/auth/logout');
      setUser(null);
    } catch (error) {
      console.error('Falha no logout', error);
    }
  };

  if (loading) {
    return <div>Carregando...</div>;
  }

  return (
    <Router>
      <UserStatus user={user} onLogout={handleLogout} />
      <nav>
        <Link to="/products">Produtos</Link> | <Link to="/cart">Carrinho</Link> | <Link to="/checkout">Checkout</Link>
      </nav>
      <Routes>
        <Route path="/" element={user ? <Navigate to="/products" /> : <Navigate to="/login" />} />
        <Route path="/products" element={<ProductList />} />
        <Route path="/cart" element={<Cart />} />
        <Route path="/checkout" element={<Checkout />} />
        <Route path="/login" element={<Login onLoginSuccess={fetchUser} />} />
        <Route path="/register" element={<Register />} />
        <Route path="/orders" element={<OrderHistory/>}/>
        <Route path="/payment/:orderId" element={<Payment/>}/>
      </Routes>
    </Router>
  );
}

export default App;