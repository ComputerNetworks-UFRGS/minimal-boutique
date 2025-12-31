import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

export default function Register() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const navigate = useNavigate();

  const handleRegister = async (e) => {
    e.preventDefault();
    try {
        const res = await axios.post('/auth/register', { email, password });
        if (res.status === 201) {
            navigate('/login');
        }
    } catch (error) {
        if (error.response && error.response.data && error.response.data.error) {
            alert(error.response.data.error);
        } else {
            alert('Erro ao registrar');
        }
        console.error(error);
    }
  };

  return (
    <form onSubmit={handleRegister}>
      <h2>Cadastro</h2>
      <input type="email" placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} required />
      <input type="password" placeholder="Senha" value={password} onChange={e => setPassword(e.target.value)} required />
      <button type="submit">Cadastrar</button>
    </form>
  );
}