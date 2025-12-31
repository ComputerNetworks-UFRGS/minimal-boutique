import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';

export default function Payment() {
  const { orderId } = useParams();
  const navigate = useNavigate();
  const [card, setCard] = useState('');
  const [error, setError] = useState('');

  const handlePayment = async (e) => {
    e.preventDefault();
    if (card.length < 5) {
        setError('Número de cartão inválido.');
        return;
    }
    setError('');
    try {
      await axios.post('/payment/charge', { order_id: orderId });
      alert('Pagamento aprovado com sucesso!');
      navigate('/orders');
    } catch (err) {
      console.error(err);
      setError('Ocorreu um erro ao processar o pagamento.');
    }
  };

  return (
    <div>
      <h2>Pagamento para o Pedido #{orderId}</h2>
      <form onSubmit={handlePayment}>
        <input
          type="text"
          placeholder="Número do Cartão de Crédito"
          value={card}
          onChange={e => setCard(e.target.value)}
          required
          style={{ minWidth: '300px', padding: '5px' }}
        />
        <button type="submit" style={{ marginLeft: '10px' }}>Pagar Agora</button>
      </form>
      {error && <p style={{ color: 'red' }}>{error}</p>}
    </div>
  );
}