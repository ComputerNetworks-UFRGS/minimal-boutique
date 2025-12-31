import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

function Checkout() {
    const navigate = useNavigate();
    const [cart, setCart] = useState([]);
    const [total, setTotal] = useState(0);

    useEffect(() => {
        axios.get('/cart/')
            .then(res => {
                setCart(res.data);
                const totalValue = res.data.reduce((acc, item) => acc + item.price * item.quantity, 0);
                setTotal(totalValue);
            })
            .catch(err => {
                console.error("Erro ao buscar carrinho:", err)
                alert("Não foi possível buscar os itens do carrinho.");
            });
    }, []);

    const handleCheckout = () => {
        axios.post('/checkout/')
            .then(res => {
                const newOrderId = res.data.order_id;
                alert(`Pedido #${newOrderId} criado com sucesso! Você será redirecionado para o pagamento.`);
                navigate(`/payment/${newOrderId}`);
            })
            .catch(err => {
                if (err.response && err.response.data && err.response.data.error) {
                    alert(err.response.data.error);
                } else {
                    alert('Ocorreu um erro ao finalizar a compra. Por favor, tente novamente.');
                }
                console.error(err)
            });
    };

    return (
        <div>
            <h2>Checkout</h2>
            {cart.length > 0 ? (
                <>
                    <ul>
                        {cart.map(item => (
                            <li key={item.id}>
                                {item.product_name} (Quantidade: {item.quantity}) - R$ {(item.price * item.quantity).toFixed(2)}
                            </li>
                        ))}
                    </ul>
                    <h3>Total da Compra: R$ {total.toFixed(2)}</h3>
                    <button onClick={handleCheckout}>Finalizar Compra</button>
                </>
            ) : (
                <p>Seu carrinho está vazio.</p>
            )}
        </div>
    );
}

export default Checkout;