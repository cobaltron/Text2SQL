import psycopg2

def rebuild_database():
    try:
        conn = psycopg2.connect(
            dbname="mydb",
            user="postgres",
            password="test",
            host="localhost",
            port="5432"
        )
        conn.autocommit = True
        cur = conn.cursor()
        
        print("Dropping existing tables...")
        # Drop all tables cleanly mapping dependencies
        tables = ["order_items", "orders", "inventory", "products", "customers", 
                  "product_categories", "suppliers", "employees", "warehouses", 
                  "locations", "regions"]
                  
        for t in tables:
            cur.execute(f"DROP TABLE IF EXISTS {t} CASCADE;")
            
        print("Rebuilding Enterprise Schema...")
        
        # 1. Regions
        cur.execute("""
            CREATE TABLE regions (
                id SERIAL PRIMARY KEY,
                region_name VARCHAR(255) NOT NULL,
                manager_name VARCHAR(255)
            );
        """)
        
        # 2. Locations
        cur.execute("""
            CREATE TABLE locations (
                id SERIAL PRIMARY KEY,
                street_address VARCHAR(255),
                postal_code VARCHAR(20),
                city VARCHAR(100) NOT NULL,
                state_province VARCHAR(100),
                country_id VARCHAR(2) NOT NULL,
                region_id INTEGER REFERENCES regions(id)
            );
        """)
        
        # 3. Warehouses
        cur.execute("""
            CREATE TABLE warehouses (
                id SERIAL PRIMARY KEY,
                warehouse_name VARCHAR(255) NOT NULL,
                location_id INTEGER REFERENCES locations(id),
                capacity INTEGER
            );
        """)
        
        # 4. Employees
        cur.execute("""
            CREATE TABLE employees (
                id SERIAL PRIMARY KEY,
                first_name VARCHAR(100) NOT NULL,
                last_name VARCHAR(100) NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                hire_date DATE NOT NULL,
                salary NUMERIC(10, 2),
                warehouse_id INTEGER REFERENCES warehouses(id)
            );
        """)
        
        # 5. Suppliers
        cur.execute("""
            CREATE TABLE suppliers (
                id SERIAL PRIMARY KEY,
                company_name VARCHAR(255) NOT NULL,
                contact_name VARCHAR(255),
                contact_email VARCHAR(255),
                location_id INTEGER REFERENCES locations(id)
            );
        """)
        
        # 6. Categories
        cur.execute("""
            CREATE TABLE product_categories (
                id SERIAL PRIMARY KEY,
                category_name VARCHAR(255) NOT NULL,
                parent_category_id INTEGER REFERENCES product_categories(id)
            );
        """)
        
        # 7. Products
        cur.execute("""
            CREATE TABLE products (
                id SERIAL PRIMARY KEY,
                product_name VARCHAR(255) NOT NULL,
                description TEXT,
                standard_cost NUMERIC(10, 2),
                list_price NUMERIC(10, 2) NOT NULL,
                category_id INTEGER REFERENCES product_categories(id),
                supplier_id INTEGER REFERENCES suppliers(id)
            );
        """)
        
        # 8. Inventory
        cur.execute("""
            CREATE TABLE inventory (
                product_id INTEGER REFERENCES products(id),
                warehouse_id INTEGER REFERENCES warehouses(id),
                quantity_on_hand INTEGER NOT NULL,
                last_restocked_date TIMESTAMP,
                PRIMARY KEY (product_id, warehouse_id)
            );
        """)
        
        # 9. Customers
        cur.execute("""
            CREATE TABLE customers (
                id SERIAL PRIMARY KEY,
                first_name VARCHAR(100),
                last_name VARCHAR(100) NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                phone VARCHAR(50),
                location_id INTEGER REFERENCES locations(id),
                registration_date TIMESTAMP NOT NULL
            );
        """)
        
        # 10. Orders
        cur.execute("""
            CREATE TABLE orders (
                id SERIAL PRIMARY KEY,
                customer_id INTEGER REFERENCES customers(id),
                employee_id INTEGER REFERENCES employees(id),
                order_date TIMESTAMP NOT NULL,
                shipped_date TIMESTAMP,
                status VARCHAR(50) NOT NULL,
                freight_cost NUMERIC(10, 2)
            );
        """)
        
        # 11. Order Items
        cur.execute("""
            CREATE TABLE order_items (
                order_id INTEGER REFERENCES orders(id),
                product_id INTEGER REFERENCES products(id),
                quantity INTEGER NOT NULL,
                unit_price NUMERIC(10, 2) NOT NULL,
                discount_amount NUMERIC(10, 2) DEFAULT 0,
                PRIMARY KEY (order_id, product_id)
            );
        """)

        print("Successfully rebuilt Global E-Commerce Logistics Database natively inside Postgres!")
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"Error rebuilding DB: {e}")

if __name__ == "__main__":
    rebuild_database()
