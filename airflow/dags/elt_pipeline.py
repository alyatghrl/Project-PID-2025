from airflow import DAG
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

# Default Arguments
default_args = {
    'owner': 'data_analyst',
    'retries': 0,
    'retry_delay': timedelta(seconds=30),
}

# Definisi DAG
with DAG(
    'fashion_stock_monitoring',  
    default_args=default_args,
    start_date=datetime(2023, 1, 1),
    schedule_interval='*/2 * * * *',  # Jalan tiap 2 menit
    catchup=False,
    max_active_runs=1
) as dag:

    # EXTRACT
    task_extract = BashOperator(
        task_id='extract_data',
        bash_command="""
            if [ -f /opt/airflow/data/live_buffer.csv ]; then
                mv /opt/airflow/data/live_buffer.csv /opt/airflow/data/batch_processing.csv
                chmod 777 /opt/airflow/data/batch_processing.csv
                echo "Batch data berhasil diambil."
            else
                echo "Tidak ada transaksi baru."
                touch /opt/airflow/data/batch_processing.csv
                chmod 777 /opt/airflow/data/batch_processing.csv
            fi
        """
    )

    # LOAD
    task_load = PostgresOperator(
        task_id='load_to_staging',
        postgres_conn_id='postgres_default',
        sql="""
            TRUNCATE TABLE staging_transactions;
            COPY staging_transactions FROM '/data/batch_processing.csv' DELIMITER ',' CSV;
        """
    )

    # TRANSFORM
    task_transform = PostgresOperator(
        task_id='transform_warehouse_analytics',
        postgres_conn_id='postgres_default',
        sql="""
            -- Simpan History Penjualan
            INSERT INTO transactions (store_id, product_id, qty, price, payment_method, created_at)
            SELECT store_id, product_id, qty, price, payment_method, trx_date
            FROM staging_transactions;

            -- Update Stok Produk di Warehouse
            UPDATE products p
            SET stock = GREATEST(0, p.stock - s.total_qty), 
                updated_at = NOW()
            FROM (
                SELECT product_id, SUM(qty) as total_qty
                FROM staging_transactions
                GROUP BY product_id
            ) s
            WHERE p.product_id = s.product_id;

            -- Prediksi Stok Habis 
            -- Bersihkan prediksi lama
            TRUNCATE TABLE inventory_forecast;

            -- Hitung prediksi baru berdasarkan batch ini
            INSERT INTO inventory_forecast (product_id, name, stock_left, velocity_per_hour, hours_left, status)
            SELECT 
                p.product_id,
                p.name,
                p.stock,
                COALESCE(s.velocity, 0) as velocity_per_hour,
                CASE 
                    WHEN COALESCE(s.velocity, 0) = 0 THEN 999 
                    ELSE ROUND(p.stock::NUMERIC / s.velocity, 1) 
                END as hours_left,
                CASE
                    WHEN p.stock = 0 THEN 'HABIS'
                    WHEN COALESCE(s.velocity, 0) > 0 AND (p.stock::NUMERIC / s.velocity) < 24 THEN 'KRITIS'
                    ELSE 'AMAN'
                END as status
            FROM products p
            LEFT JOIN (
                -- Hitung kecepatan per jam. 
                SELECT product_id, SUM(qty) * 30 as velocity 
                FROM staging_transactions
                GROUP BY product_id
            ) s ON p.product_id = s.product_id
            ;   
            
            -- Profit Analysis
            TRUNCATE TABLE daily_profit_analysis;
            INSERT INTO daily_profit_analysis 
            SELECT p.category, SUM(t.price), SUM(p.unit_cost * t.qty), SUM(t.price - (p.unit_cost * t.qty)),
            CASE WHEN SUM(t.price) = 0 THEN 0 ELSE ROUND((SUM(t.price - (p.unit_cost * t.qty)) / SUM(t.price)) * 100, 2) END
            FROM transactions t JOIN products p ON t.product_id = p.product_id WHERE t.created_at >= CURRENT_DATE GROUP BY p.category;

            -- Payment Behavior
            TRUNCATE TABLE payment_behavior_analysis;
            INSERT INTO payment_behavior_analysis
            SELECT payment_method, ROUND(AVG(price), 0), COUNT(*) FROM transactions WHERE created_at >= CURRENT_DATE GROUP BY payment_method;

            -- Hourly Traffic
            TRUNCATE TABLE hourly_traffic_stats;
            INSERT INTO hourly_traffic_stats
            SELECT EXTRACT(HOUR FROM created_at), COUNT(*), SUM(price) FROM transactions WHERE created_at >= CURRENT_DATE GROUP BY 1 ORDER BY 1;
            
            -- RESTOCK LOGIC
            INSERT INTO restock_log (product_id, restocked_to)
            SELECT product_id, 
                   CASE 
                       WHEN is_event = TRUE THEN 5000 -- Barang Event restock lebih dikit (Hati-hati overstock)
                       ELSE 10000                     -- Barang Harian restock full (Aman)
                   END
            FROM products
            WHERE stock < safety_stock; -- Hanya jika stok di bawah batas aman

            -- Eksekusi Restock Fisik (Update Tabel Produk)
            UPDATE products
            SET stock = CASE 
                            WHEN is_event = TRUE THEN 5000 
                            ELSE 10000 
                        END,
                updated_at = NOW()
            WHERE stock < safety_stock;
        """
    )

    task_extract >> task_load >> task_transform