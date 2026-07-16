"""Run once to populate initial data: admin user + sample products + customers."""

from app.core.database import init_db, SessionLocal
from app.core.security import hash_password
from app.models.user import User
from app.models.product import Product
from app.models.customer import Customer  # noqa: F401
from app.models.order import Order, OrderItem  # noqa: F401
from app.models.stock import StockMovement  # noqa: F401
from app.models.production import Production  # noqa: F401


def seed():
    init_db()
    db = SessionLocal()

    if not db.query(User).first():
        db.add_all([
            User(
                username="admin",
                hashed_password=hash_password("admin"),
                full_name="Administrador",
                role="admin",
            ),
            User(
                username="andressa",
                hashed_password=hash_password("123"),
                full_name="Andressa Vendas",
                role="sales",
            ),
            User(
                username="cozinha",
                hashed_password=hash_password("123"),
                full_name="Chef Cozinha",
                role="kitchen",
            ),
        ])

    if not db.query(Product).first():
        db.add_all([
            Product(name="Frango Grelhado", price=22.90, category="marmita", unit="un"),
            Product(name="Carne Moída", price=24.90, category="marmita", unit="un"),
            Product(name="Strogonoff de Frango", price=26.90, category="marmita", unit="un"),
            Product(name="Peixe ao Molho", price=28.90, category="marmita", unit="un"),
            Product(name="Arroz Branco", price=8.90, category="acompanhamento", unit="serving"),
            Product(name="Feijão Preto", price=6.90, category="acompanhamento", unit="serving"),
            Product(name="Batata Doce", price=7.90, category="acompanhamento", unit="serving"),
            Product(name="Salada Verde", price=5.90, category="acompanhamento", unit="serving"),
        ])

    if not db.query(Customer).first():
        db.add_all([
            Customer(name="Maria Silva", phone="(11) 99999-0001", address_street="Rua Augusta, 500", address_neighborhood="Consolação", address_city="São Paulo", address2_street="Rua da Consolação, 300", address2_neighborhood="Consolação", address2_city="São Paulo"),
            Customer(name="João Santos", phone="(11) 99999-0002", address_street="Av. Paulista, 1000", address_neighborhood="Bela Vista", address_city="São Paulo", address2_street="Rua Joaquim Floriano, 200", address2_neighborhood="Itaim Bibi", address2_city="São Paulo"),
            Customer(name="Ana Oliveira", phone="(11) 99999-0003", address_street="Rua Oscar Freire, 200", address_neighborhood="Jardins", address_city="São Paulo", address2_street="Av. Brigadeiro Faria Lima, 1500", address2_neighborhood="Pinheiros", address2_city="São Paulo"),
            Customer(name="Carlos Lima", phone="(11) 99999-0004", address_street="Rua da Consolação, 1500", address_neighborhood="Consolação", address_city="São Paulo"),
            Customer(name="Fernanda Costa", phone="(11) 99999-0005", address_street="Alameda Santos, 800", address_neighborhood="Cerqueira César", address_city="São Paulo"),
        ])

    db.commit()
    db.close()
    print("Seed complete. Users: admin/admin, andressa/123, cozinha/123 | 5 products")


if __name__ == "__main__":
    seed()
