from app.config.database import SessionLocal
from app.config.database import engine

from app.models import Base, User, Product, Table

from app.core.security import get_password_hash


def mockup():
    # สร้าง tables ทั้งหมด
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        existing_admin = db.query(User).filter(User.username == "admin").first()
        if not existing_admin:
            admin = User(
                username="admin",
                password=get_password_hash("admin"),
                user_role="admin",
                is_verified=True,
                name="แอดมิน",
                email="project.cafein.coffee@gmail.com",
                tel="0999999999",
            )
            db.add(admin)
            print("Created admin user (admin)")
        else:
            print("Admin user already exists")

        # ===== Products =====
        existing_products = db.query(Product).count()
        if existing_products == 0:
            products = [
                Product(
                    product_name="Americano",
                    price=50,
                    sweetness_options=["0", "25", "50", "75", "100"],
                    milk_type_options=[],
                    type_options=["hot", "iced"],
                ),
                Product(
                    product_name="Espresso",
                    price=50,
                    sweetness_options=["0", "25", "50", "75", "100"],
                    milk_type_options=[],
                    type_options=["hot", "iced"],
                ),
                Product(
                    product_name="Latte",
                    price=70,
                    sweetness_options=["0", "25", "50", "75", "100", "125"],
                    milk_type_options=["whole", "low-fat", "non-fat", "oat", "soy"],
                    type_options=["hot", "iced", "frappe"],
                ),
            ]
            db.add_all(products)
            print(f"Created {len(products)} products")
        else:
            print(f"Products already exist ({existing_products} records)")

        # ===== Tables =====
        existing_tables = db.query(Table).count()
        if existing_tables == 0:
            tables_data = []
            for i in range(1, 15):
                capacity = 6 if i <= 3 else 4
                tables_data.append(
                    Table(
                        table_number=str(i),
                        capacity=capacity,
                        status="empty",
                    )
                )
            db.add_all(tables_data)
            print(f"Created {len(tables_data)} tables")
        else:
            print(f"Tables already exist ({existing_tables} records)")

        db.commit()
        print("\nMockup completed!")

    except Exception as e:
        db.rollback()
        print(f"Mockup failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    mockup()
