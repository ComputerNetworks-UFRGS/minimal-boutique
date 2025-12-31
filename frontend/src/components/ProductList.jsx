import React, { useState, useEffect } from 'react';
import axios from 'axios';

function ProductList() {
    const [products, setProducts] = useState([]);
    const [quantities, setQuantities] = useState({});

    useEffect(() => {
        axios.get('/products/')
            .then(res => {
                setProducts(res.data);
                const initialQuantities = {};
                res.data.forEach(product => {
                    initialQuantities[product.id] = 1;
                });
                setQuantities(initialQuantities);
            })
            .catch(err => console.error(err));
    }, []);

    const handleQuantityChange = (productId, quantity) => {
        setQuantities(prevQuantities => ({
            ...prevQuantities,
            [productId]: quantity
        }));
    };

    const addToCart = (product) => {
        const quantity = quantities[product.id] || 1;
        axios.post('/cart/', { product_id: product.id, quantity: parseInt(quantity, 10) })
            .then(() => alert('Adicionado ao carrinho!'))
            .catch(err => console.error(err));
    };

    return (
        <div>
            <h2>Produtos</h2>
            <ul>
                {products.map(prod => (
                    <li key={prod.id}>
                        {prod.name} - R$ {prod.price.toFixed(2)}
                        <input
                            type="number"
                            value={quantities[prod.id] || 1}
                            onChange={(e) => handleQuantityChange(prod.id, e.target.value)}
                            min="1"
                            style={{ marginLeft: '10px', width: '50px' }}
                        />
                        <button onClick={() => addToCart(prod)}>Adicionar</button>
                    </li>
                ))}
            </ul>
        </div>
    );
}

export default ProductList;