from database import db

def test_database_connection():
    """Test kết nối database"""
    try:
        print("🔄 Đang kết nối đến database...")
        
        # Test query đơn giản
        query = """
        SELECT TABLE_NAME 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_TYPE = 'BASE TABLE'
        ORDER BY TABLE_NAME
        """
        
        results = db.execute_query(query)
        
        print("✅ Kết nối thành công!")
        print(f"\n📊 Database có {len(results)} bảng:")
        for row in results:
            print(f"   - {row['TABLE_NAME']}")
        
        return True
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        return False

if __name__ == "__main__":
    test_database_connection()