import psycopg2

def inspect_direct():
    try:
        conn = psycopg2.connect("postgresql://postgres:ashiq%40123@localhost:5433/agenthealth")
        cur = conn.cursor()
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'patients'")
        columns = [row[0] for row in cur.fetchall()]
        print(f"Direct columns in patients: {columns}")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_direct()
