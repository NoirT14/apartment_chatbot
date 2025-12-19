import pyodbc
import os
from dotenv import load_dotenv
from typing import List, Dict, Any
from schema.schema_context import get_current_schema

# Load environment variables
load_dotenv()

class Database:
    def __init__(self):
        self.server = os.getenv('DB_SERVER')
        self.database = os.getenv('DB_NAME')
        self.username = os.getenv('DB_USER')
        self.password = os.getenv('DB_PASSWORD')
        self.connection_string = (
            f'DRIVER={{ODBC Driver 18 for SQL Server}};'
            f'SERVER={self.server};'
            f'DATABASE={self.database};'
            f'UID={self.username};'
            f'PWD={self.password};'
            f'TrustServerCertificate=yes;'
        )
    
    def get_connection(self):
        """Tạo kết nối đến database"""
        try:
            conn = pyodbc.connect(self.connection_string)
            return conn
        except Exception as e:
            print(f"❌ Lỗi kết nối database: {e}")
            raise
    
    def _inject_schema(self, query: str) -> str:
        """
        Inject schema name vào query
        
        Thay thế {schema} placeholder bằng schema name từ context
        
        Args:
            query: SQL query với {schema} placeholder
            
        Returns:
            Query đã được inject schema
            
        Raises:
            ValueError: Nếu không có schema (chưa đăng nhập)
        """
        schema = get_current_schema()
        
        if schema is None:
            raise ValueError(
                "Cannot execute query: No schema context. "
                "User must be authenticated to access database."
            )
        
        # Replace {schema} placeholder với schema name
        query = query.replace('{schema}', schema)
        
        return query
    
    def execute_query(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """
        Thực thi SELECT query và trả về kết quả dạng list of dict
        
        Tự động inject schema vào query trước khi execute
        """
        # Inject schema vào query
        query = self._inject_schema(query)
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            # Lấy tên cột
            columns = [column[0] for column in cursor.description]
            
            # Chuyển kết quả thành list of dict
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            
            return results
        except Exception as e:
            print(f"❌ Lỗi thực thi query: {e}")
            raise
        finally:
            cursor.close()
            conn.close()
    
    def execute_non_query(self, query: str, params: tuple = None) -> int:
        """
        Thực thi INSERT/UPDATE/DELETE query
        
        Tự động inject schema vào query trước khi execute
        """
        # Inject schema vào query
        query = self._inject_schema(query)
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            conn.commit()
            return cursor.rowcount
        except Exception as e:
            conn.rollback()
            print(f"❌ Lỗi thực thi query: {e}")
            raise
        finally:
            cursor.close()
            conn.close()

# Singleton instance
db = Database()