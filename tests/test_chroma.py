import createEmbeddings
import traceback

if __name__ == "__main__":
    try:
        query = "Find number of order for each customer"
        print("Testing generate_sql standalone...")
        res = createEmbeddings.generate_sql(query)
        print("Result:", res)
    except Exception as e:
        print("Exception:", str(e))
        traceback.print_exc()
