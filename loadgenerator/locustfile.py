import random
from locust import HttpUser, TaskSet, task, between
from faker import Faker
import logging
import uuid

fake = Faker()

class UserBehavior(TaskSet):
    product_ids = []
    token = None

    def on_start(self):
        try:
            self.register_and_login()
            self.fetch_product_ids()
        except Exception as e:
            logging.error(f"[FATAL] Erro ao iniciar usuário: {e}")
            self.interrupt(reschedule=True)


    def check_response(self, response, expected_status=200):
        if response.status_code != expected_status:
            error_msg = (
                f"[FAIL] {response.request.method} {response.request.path_url} | "
                f"expected={expected_status}, got={response.status_code} |"
                # f"response={response.text}"
            )
            logging.error(error_msg)
            response.failure(error_msg)
            if response.status_code >= 500:
                self.interrupt(reschedule=True)
            return False
        else:
            response.success()
            return True

    def register_and_login(self):
        email = f"{uuid.uuid4().hex}@test.com"
        password = fake.password()
        
        # Registro
        with self.client.post("/auth/register", json={"email": email, "password": password},
                              name="/auth/register", catch_response=True) as reg_response:
            if not self.check_response(reg_response, expected_status=201):
                self.interrupt(reschedule=False)
                return

        # Login
        with self.client.post("/auth/login", json={"email": email, "password": password},
                              name="/auth/login", catch_response=True) as login_response:
            if self.check_response(login_response, expected_status=200):
                self.token = login_response.json().get("access_token")
                if self.token:
                    self.client.headers.update({"Authorization": f"Bearer {self.token}"})
            else:
                self.interrupt(reschedule=False)

    def fetch_product_ids(self):
        try:
            with self.client.get("/products/", name="/products", catch_response=True) as response:
                if self.check_response(response, expected_status=200):
                    products = response.json()
                    if products:
                        self.product_ids = [p['id'] for p in products]
                    else:
                        response.failure("Nenhum produto encontrado")
        except Exception as e:
            logging.error(f"Exceção ao buscar produtos: {e}")
    
    def safe_task(fn):
        def wrapper(self, *args, **kwargs):
            try:
                fn(self, *args, **kwargs)
            except Exception as e:
                logging.error(f"[EXCEPTION] {fn.__name__}: {e}")
                self.interrupt(reschedule=True)
        return wrapper

    @task(10)
    @safe_task
    def browse_products(self):
        with self.client.get("/products/", name="/products", catch_response=True) as response:
            self.check_response(response, expected_status=200)
        if self.product_ids:
            product_id = random.choice(self.product_ids)
            with self.client.get(f"/products/{product_id}", name="/products/[id]", catch_response=True) as response:
                self.check_response(response, expected_status=200)

    @task(5)
    @safe_task
    def add_to_cart(self):
        if not self.product_ids:
            return
        product_id = random.choice(self.product_ids)
        with self.client.post("/cart/", json={"product_id": product_id, "quantity": random.randint(1, 3)},
                              name="/cart", catch_response=True) as response:
            self.check_response(response, expected_status=201)

    @task(3)
    @safe_task
    def view_cart(self):
        with self.client.get("/cart/", name="/cart", catch_response=True) as response:
            self.check_response(response, expected_status=200)

    @task(2)
    @safe_task
    def checkout_and_pay(self):
        if not self.product_ids:
            return

        product_id = random.choice(self.product_ids)
        with self.client.post("/cart/", json={"product_id": product_id, "quantity": 1},
                              name="/cart (checkout)", catch_response=True) as response:
            self.check_response(response, expected_status=201)
        
        order_id = None
        with self.client.post("/checkout/", name="/checkout", catch_response=True) as response:
            if self.check_response(response, expected_status=201):
                order_data = response.json()
                order_id = order_data.get("order_id")

        if order_id:
            with self.client.post(f"/payment/charge", json={"order_id": order_id},
                                  name="/payment/charge", catch_response=True) as response:
                self.check_response(response, expected_status=200)

    @task(1)
    @safe_task
    def view_orders(self):
        with self.client.get("/orders/", name="/orders", catch_response=True) as response:
            self.check_response(response, expected_status=200)


class WebsiteUser(HttpUser):
    tasks = [UserBehavior]
    wait_time = between(2, 10)
