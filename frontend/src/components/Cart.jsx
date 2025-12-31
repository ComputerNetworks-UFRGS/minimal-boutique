// Cart.jsx

import React, {useEffect, useState} from 'react';
import axios from 'axios';

function Cart(){

    const [cart, setCart] = useState([]);

    useEffect(() => {
        axios.get('/cart/')
            .then(res => setCart(res.data))
            .catch(err => console.error("Erro ao buscar carrinho:", err));

    },  []);

    // NOVA FUNÇÃO para remover o item
    const handleRemoveItem = (itemId) => {
        axios.delete(`/cart/${itemId}`)
            .then(response => {
                // Se a remoção for bem-sucedida, atualiza o estado do carrinho
                // filtrando o item removido
                setCart(currentCart => currentCart.filter(item => item.id !== itemId));
                console.log(response.data.message);
            })
            .catch(err => {
                console.error("Erro ao remover item:", err);
                alert("Não foi possível remover o item do carrinho.");
            });
    };

    // Renderização condicional para carrinho vazio
    if (cart.length === 0) {
        return (
            <div>
                <h2>Carrinho</h2>
                <p>Seu carrinho está vazio.</p>
            </div>
        );
    }

    return(
        <div>
            <h2>Carrinho</h2>
            <ul>
                {/* LISTA ATUALIZADA com mais detalhes e o novo botão */}
                {cart.map(item => (
                    <li key={item.id}>
                        {item.product_name} (Quantidade: {item.quantity}) - R$ {item.price.toFixed(2)}
                        {/* BOTÃO DE EXCLUIR adicionado aqui */}
                        <button onClick={() => handleRemoveItem(item.id)} style={{marginLeft: '10px'}}>
                            Excluir
                        </button>
                    </li>
                ))}
            </ul>
        </div>
    );
}

export default Cart;