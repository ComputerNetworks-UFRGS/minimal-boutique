import React, {useState, useEffect} from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

function OrderHistory(){
    const [orders, setOrders] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(false);
    const navigate = useNavigate();

    useEffect(()=>{
        axios.get('/orders/', {withCredentials: true})
            .then(res => {
                setOrders(res.data);
                setLoading(false);
            })
            .catch(err => {

                if(err.response){
                    console.error("Erro ao buscar histórico de pedidos");
                    console.error("Status:", err.response.status);
                    console.error("Dados:", err.response.data);
                    console.error("Headers:", err.response.headers);
                } else if( err.request){
                    console.error("Nenhuma resposta recebida. Request: ", err.request);
                } else {
                    console.error("Erro na configuração da requisição", err.message);
                }
                // console.error("Erro ao buscar histórico de pedidos:", err);
                setLoading(false);
                setError(true);
            });
    }, []);

    const handlePayment = (orderId) => {
        navigate(`/payment/${orderId}`);
    };

    const handleDeleteOrder = (orderId) => {
        axios.delete(`/orders/${orderId}`, {withCredentials: true})
            .then(() => {
                setOrders(orders.filter(order => order.id !== orderId));
            })
            .catch(err => {
                console.error("Erro ao cancelar o pedido:", err);
                alert("Não foi possível cancelar o pedido.");
            });
    };

    if(loading){
        return <div>Carregando histórico de pedidos...</div>
    }

    if(error) return <div>Erro ao carregar o histórico de pedidos</div>

    if(orders.length === 0){
        return (
            <div>
                <h2>Meus Pedidos</h2>
                <p>Você ainda não fez nenhum pedido</p>
            </div>
        );
    }
    
    return(
        <div>
            <h2>Meus Pedidos</h2>
            {orders.map(order=> (
                <div key = {order.id} style={{border:'1px solid #ccc', margin: '10px', padding: '10px', borderRadius:'5px'}}>
                    <h4>Pedido #{order.id}</h4>
                    <p><strong>Status:</strong> {order.status}</p>
                    <ul>
                        {order.items.map((item,index)=> (
                            <li key = {index}>
                                {item.product_name} (Quantidade: {item.quantity}) - R$ {(item.price * item.quantity).toFixed(2)}

                            </li>
                        ))}
                    </ul>
                    <p><strong>Total do Pedido: R$ {order.total.toFixed(2)}</strong></p>
                    {order.status === 'pending' && (
                        <>
                            <button onClick={() => handlePayment(order.id)}>Pagar</button>
                            <button onClick={() => handleDeleteOrder(order.id)} style={{marginLeft: '10px'}}>Cancelar Pedido</button>
                        </>
                    )}
                </div>
            ))}
        </div>
    );
}

export default OrderHistory;