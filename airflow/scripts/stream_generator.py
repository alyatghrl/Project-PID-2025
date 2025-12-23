import time
import random
import csv
import os
import sys
from datetime import datetime

OUTPUT_FILE = "/opt/airflow/data/live_buffer.csv"

NORMAL_ITEMS = [
    {"id": 1, "name": "Kaos Polos", "price": 50000},
    {"id": 2, "name": "Celana Jeans", "price": 150000},
    {"id": 3, "name": "Jaket Hoodie", "price": 200000},
    {"id": 4, "name": "Sepatu Sneakers", "price": 300000},
    {"id": 5, "name": "Topi", "price": 75000}
]

NATARU_ITEMS = [
    {"id": 101, "name": "Sweater Natal", "price": 250000},
    {"id": 102, "name": "Celana Chino", "price": 75000},
    {"id": 103, "name": "Kemeja Kotak", "price": 150000}
]

PAYMENT_METHODS = ["Cash", "Credit Card", "QRIS"]

def generate_stream():
    current_mode = os.environ.get('MODE', 'NORMAL').upper()
    
    if current_mode == 'NATARU':
        active_products = NATARU_ITEMS
        print("\n>>> [SYSTEM ALERT] EVENT NATARU BERJALAN! ")
        print(">>> Hanya menjual item Event Natal & Tahun Baru.")
    else:
        active_products = NORMAL_ITEMS
        print("\n>>> [SYSTEM INFO] MODE 'NORMAL' (Hari Biasa).")
        print(">>> Menjual item fashion reguler.")

    print(f">>> Buffer File: {OUTPUT_FILE}")
    print(">>> Tekan CTRL+C untuk berhenti.\n")
    
    # Header Log
    print(f"{'TIMESTAMP':<20} | {'ITEM':<20} | {'QTY':<5} | {'TOTAL':<12} | {'METODE':<10}")
    print("-" * 80)

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    try:
        while True:
            prod = random.choice(active_products)
            
            # Limit MAX 2 item 
            qty = random.randint(1, 2)
            
            total_price = prod["price"] * qty
            payment = random.choice(PAYMENT_METHODS)
            
            trx_data = [
                int(time.time() * 1000),      
                1,                            
                prod["id"],                   
                qty,                          
                total_price,                  
                payment,                      
                datetime.now().strftime("%Y-%m-%d %H:%M:%S") 
            ]

            with open(OUTPUT_FILE, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(trx_data)

            print(f"{trx_data[6]:<20} | {prod['name']:<20} | {qty:<5} | {total_price:<12} | {payment:<10}")

            time.sleep(random.uniform(0.5, 2.0))

    except KeyboardInterrupt:
        print("\n>>> Generator Berhenti.")

if __name__ == "__main__":
    generate_stream()