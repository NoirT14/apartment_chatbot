from database import db
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta, date
from decimal import Decimal
from schema.schema_context import has_schema

class ApartmentAPI:
    """API endpoints để truy vấn dữ liệu apartment management system"""
    
    @staticmethod
    def _check_authentication() -> Optional[Dict[str, Any]]:
        """
        Check xem có schema (đã đăng nhập) chưa
        
        Returns:
            None nếu đã authenticated, dict error nếu chưa
        """
        if not has_schema():
            return {
                "success": False,
                "error": "Authentication required. Please login to access this data.",
                "data": [],
                "count": 0
            }
        return None
    
    @staticmethod
    def _convert_to_serializable(data: Any) -> Any:
        """
        Convert SQL data types to JSON-serializable types
        
        Args:
            data: Dữ liệu cần convert (có thể là dict, list, hoặc primitive)
        
        Returns:
            Dữ liệu đã được convert
        """
        if isinstance(data, dict):
            return {key: ApartmentAPI._convert_to_serializable(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [ApartmentAPI._convert_to_serializable(item) for item in data]
        elif isinstance(data, Decimal):
            return float(data)
        elif isinstance(data, (datetime, date)):
            return data.isoformat()
        elif isinstance(data, bytes):
            return data.decode('utf-8', errors='ignore')
        else:
            return data
    
    # ==================== SERVICE FEES FUNCTIONS ====================
    
    @staticmethod
    def get_service_types(category: Optional[str] = None) -> Dict[str, Any]:
        """
        Lấy danh sách loại dịch vụ
        
        Args:
            category: Lọc theo category (Utility, Fee, Service, Maintenance, Other)
        
        Returns:
            Dict với data và count
        """
        # Check authentication
        auth_error = ApartmentAPI._check_authentication()
        if auth_error:
            return auth_error
        
        query = """
        SELECT 
            st.service_type_id,
            st.code,
            st.name,
            st.unit,
            st.is_mandatory,
            st.is_recurring,
            st.is_active,
            c.name as category_name
        FROM {schema}.service_types st
        LEFT JOIN {schema}.service_type_categories c ON st.category_id = c.category_id
        WHERE st.is_active = 1 AND st.is_delete = 0
        """
        params = []
        
        if category:
            query += " AND c.name = ?"
            params.append(category)
        
        query += " ORDER BY st.name"
        
        try:
            results = db.execute_query(query, tuple(params) if params else None)
            
            # Convert tất cả data types
            results = ApartmentAPI._convert_to_serializable(results)
            
            return {
                "success": True,
                "data": results,
                "count": len(results)
            }
        except Exception as e:
            print(f"❌ Error in get_service_types: {e}")
            return {
                "success": False,
                "error": str(e),
                "data": [],
                "count": 0
            }
    
    @staticmethod
    def get_service_prices(
        service_type_code: Optional[str] = None,
        active_only: bool = True
    ) -> Dict[str, Any]:
        """
        Lấy giá dịch vụ hiện tại
        
        Args:
            service_type_code: Mã loại dịch vụ (MGMT_FEE, PARKING_CAR, INTERNET...)
            active_only: Chỉ lấy giá đang áp dụng
        
        Returns:
            Dict với data và count
        """
        # Check authentication
        auth_error = ApartmentAPI._check_authentication()
        if auth_error:
            return auth_error
        
        query = """
        SELECT 
            st.code as service_code,
            st.name as service_name,
            st.unit,
            sp.unit_price,
            sp.effective_date,
            sp.end_date,
            sp.status
        FROM {schema}.service_prices sp
        INNER JOIN {schema}.service_types st ON sp.service_type_id = st.service_type_id
        WHERE 1=1
        """
        params = []
        
        if service_type_code:
            query += " AND st.code = ?"
            params.append(service_type_code)
        
        if active_only:
            query += " AND sp.status = 'APPROVED'"
            query += " AND sp.effective_date <= GETDATE()"
            query += " AND (sp.end_date IS NULL OR sp.end_date >= GETDATE())"
        
        query += " ORDER BY st.name, sp.effective_date DESC"
        
        try:
            results = db.execute_query(query, tuple(params) if params else None)
            
            # Convert tất cả data types
            results = ApartmentAPI._convert_to_serializable(results)
            
            # Format giá tiền
            for row in results:
                if 'unit_price' in row and row['unit_price']:
                    row['unit_price_formatted'] = f"{row['unit_price']:,.0f} VND"
            
            return {
                "success": True,
                "data": results,
                "count": len(results)
            }
        except Exception as e:
            print(f"❌ Error in get_service_prices: {e}")
            return {
                "success": False,
                "error": str(e),
                "data": [],
                "count": 0
            }
    
    @staticmethod
    def calculate_service_fee(
        service_code: str,
        quantity: float = 1.0
    ) -> Dict[str, Any]:
        """
        Tính phí dịch vụ
        
        Args:
            service_code: Mã dịch vụ (MGMT_FEE, PARKING_CAR...)
            quantity: Số lượng (diện tích, số tháng...)
        
        Returns:
            Dict với thông tin tính toán
        """
        # Check authentication
        auth_error = ApartmentAPI._check_authentication()
        if auth_error:
            return auth_error
        
        # Lấy giá hiện tại
        query = """
        SELECT TOP 1
            st.code,
            st.name,
            st.unit,
            sp.unit_price
        FROM {schema}.service_prices sp
        INNER JOIN {schema}.service_types st ON sp.service_type_id = st.service_type_id
        WHERE st.code = ?
            AND sp.status = 'APPROVED'
            AND sp.effective_date <= GETDATE()
            AND (sp.end_date IS NULL OR sp.end_date >= GETDATE())
        ORDER BY sp.effective_date DESC
        """
        
        try:
            results = db.execute_query(query, (service_code,))
            
            if results:
                # Convert data types
                results = ApartmentAPI._convert_to_serializable(results)
                service = results[0]
                
                unit_price = float(service['unit_price'])
                total = unit_price * quantity
                
                return {
                    "success": True,
                    "data": {
                        "service_code": service['code'],
                        "service_name": service['name'],
                        "unit": service['unit'],
                        "unit_price": unit_price,
                        "unit_price_formatted": f"{unit_price:,.0f} VND",
                        "quantity": quantity,
                        "total": total,
                        "total_formatted": f"{total:,.0f} VND"
                    }
                }
            else:
                return {
                    "success": False,
                    "error": f"Không tìm thấy dịch vụ với mã: {service_code}"
                }
        except Exception as e:
            print(f"❌ Error in calculate_service_fee: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    def get_service_categories() -> Dict[str, Any]:
        """
        Lấy danh sách categories
        
        Returns:
            Dict với data và count
        """
        # Check authentication
        auth_error = ApartmentAPI._check_authentication()
        if auth_error:
            return auth_error
        
        query = """
        SELECT 
            category_id,
            name,
            description
        FROM {schema}.service_type_categories
        ORDER BY name
        """
        
        try:
            results = db.execute_query(query)
            
            # Convert data types
            results = ApartmentAPI._convert_to_serializable(results)
            
            return {
                "success": True,
                "data": results,
                "count": len(results)
            }
        except Exception as e:
            print(f"❌ Error in get_service_categories: {e}")
            return {
                "success": False,
                "error": str(e),
                "data": [],
                "count": 0
            }

    # ==================== AMENITIES FUNCTIONS ====================

    @staticmethod
    def get_amenities(
        category_name: Optional[str] = None,
        status: Optional[str] = "ACTIVE",
        has_monthly_package: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Lấy danh sách tiện ích trong chung cư

        Args:
            category_name: Lọc theo loại tiện ích (Gym, Pool, Meeting Room...)
            status: Trạng thái (ACTIVE, INACTIVE, MAINTENANCE)
            has_monthly_package: Lọc tiện ích có gói tháng

        Returns:
            Dict với data và count
        """
        # Check authentication
        auth_error = ApartmentAPI._check_authentication()
        if auth_error:
            return auth_error
        
        query = """
        SELECT
            amenity_id,
            code,
            name,
            category_name,
            location,
            has_monthly_package,
            fee_type,
            status,
            requires_face_verification,
            asset_id
        FROM {schema}.amenities
        WHERE is_delete = 0
        """
        params = []

        if category_name:
            query += " AND category_name = ?"
            params.append(category_name)

        if status:
            query += " AND status = ?"
            params.append(status)

        if has_monthly_package is not None:
            query += " AND has_monthly_package = ?"
            params.append(1 if has_monthly_package else 0)

        query += " ORDER BY category_name, name"

        try:
            results = db.execute_query(query, tuple(params) if params else None)
            results = ApartmentAPI._convert_to_serializable(results)

            # Thêm thông tin giá gói rẻ nhất cho mỗi tiện ích (nếu có)
            for amenity in results:
                if amenity.get('has_monthly_package'):
                    packages_result = ApartmentAPI.get_amenity_packages(
                        amenity_code=amenity['code'],
                        status='ACTIVE'
                    )
                    if packages_result['success'] and packages_result['count'] > 0:
                        # Lấy gói rẻ nhất
                        cheapest = min(packages_result['data'], key=lambda x: x.get('price', float('inf')))
                        amenity['cheapest_package'] = {
                            'name': cheapest.get('package_name', ''),
                            'price': cheapest.get('price', 0),
                            'price_formatted': cheapest.get('price_formatted', '0 VND'),
                            'month_count': cheapest.get('month_count', 0)
                        }
                        amenity['total_packages'] = packages_result['count']
                    else:
                        amenity['cheapest_package'] = None
                        amenity['total_packages'] = 0
                else:
                    amenity['cheapest_package'] = None
                    amenity['total_packages'] = 0

            return {
                "success": True,
                "data": results,
                "count": len(results)
            }
        except Exception as e:
            print(f"❌ Error in get_amenities: {e}")
            return {
                "success": False,
                "error": str(e),
                "data": [],
                "count": 0
            }

    @staticmethod
    def get_amenity_by_code(code: str) -> Dict[str, Any]:
        """
        Lấy thông tin chi tiết tiện ích theo mã (bao gồm cả thông tin giá nếu có)

        Args:
            code: Mã tiện ích

        Returns:
            Dict với thông tin tiện ích và giá gói (nếu có)
        """
        # Check authentication
        auth_error = ApartmentAPI._check_authentication()
        if auth_error:
            return auth_error
        
        query = """
        SELECT
            amenity_id,
            code,
            name,
            category_name,
            location,
            has_monthly_package,
            fee_type,
            status,
            requires_face_verification,
            asset_id
        FROM {schema}.amenities
        WHERE code = ? AND is_delete = 0
        """

        try:
            results = db.execute_query(query, (code,))
            results = ApartmentAPI._convert_to_serializable(results)

            if results:
                amenity_data = results[0]

                # Nếu có gói tháng, lấy thông tin giá
                if amenity_data.get('has_monthly_package'):
                    packages_result = ApartmentAPI.get_amenity_packages(amenity_code=code, status='ACTIVE')
                    if packages_result['success'] and packages_result['count'] > 0:
                        amenity_data['packages'] = packages_result['data']
                        amenity_data['package_count'] = packages_result['count']
                    else:
                        amenity_data['packages'] = []
                        amenity_data['package_count'] = 0
                else:
                    amenity_data['packages'] = []
                    amenity_data['package_count'] = 0

                return {
                    "success": True,
                    "data": amenity_data
                }
            else:
                return {
                    "success": False,
                    "error": f"Không tìm thấy tiện ích với mã: {code}"
                }
        except Exception as e:
            print(f"❌ Error in get_amenity_by_code: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    @staticmethod
    def get_amenity_packages(
        amenity_code: Optional[str] = None,
        status: Optional[str] = "ACTIVE"
    ) -> Dict[str, Any]:
        """
        Lấy danh sách gói dịch vụ tiện ích (monthly packages)

        Args:
            amenity_code: Mã tiện ích cần xem gói
            status: Trạng thái gói (ACTIVE, INACTIVE)

        Returns:
            Dict với data và count
        """
        # Check authentication
        auth_error = ApartmentAPI._check_authentication()
        if auth_error:
            return auth_error
        
        query = """
        SELECT
            ap.package_id,
            ap.amenity_id,
            a.code as amenity_code,
            a.name as amenity_name,
            ap.name as package_name,
            ap.month_count,
            ap.price,
            ap.description,
            ap.status,
            ap.duration_days,
            ap.period_unit
        FROM {schema}.amenity_packages ap
        INNER JOIN {schema}.amenities a ON ap.amenity_id = a.amenity_id
        WHERE 1=1
        """
        params = []

        if amenity_code:
            query += " AND a.code = ?"
            params.append(amenity_code)

        if status:
            query += " AND ap.status = ?"
            params.append(status)

        query += " ORDER BY a.name, ap.month_count"

        try:
            results = db.execute_query(query, tuple(params) if params else None)
            results = ApartmentAPI._convert_to_serializable(results)

            # Format giá tiền
            for row in results:
                if 'price' in row and row['price']:
                    row['price_formatted'] = f"{row['price']:,.0f} VND"

            return {
                "success": True,
                "data": results,
                "count": len(results)
            }
        except Exception as e:
            print(f"❌ Error in get_amenity_packages: {e}")
            return {
                "success": False,
                "error": str(e),
                "data": [],
                "count": 0
            }

    @staticmethod
    def calculate_amenity_package_price(
        amenity_code: str,
        month_count: int = 1
    ) -> Dict[str, Any]:
        """
        Tính giá gói tiện ích theo số tháng

        Args:
            amenity_code: Mã tiện ích
            month_count: Số tháng đăng ký

        Returns:
            Dict với thông tin tính toán
        """
        # Check authentication
        auth_error = ApartmentAPI._check_authentication()
        if auth_error:
            return auth_error
        
        query = """
        SELECT TOP 1
            a.code,
            a.name as amenity_name,
            ap.name as package_name,
            ap.month_count,
            ap.price,
            ap.duration_days,
            ap.period_unit
        FROM {schema}.amenity_packages ap
        INNER JOIN {schema}.amenities a ON ap.amenity_id = a.amenity_id
        WHERE a.code = ?
            AND ap.month_count = ?
            AND ap.status = 'ACTIVE'
        ORDER BY ap.price ASC
        """

        try:
            results = db.execute_query(query, (amenity_code, month_count))
            results = ApartmentAPI._convert_to_serializable(results)

            if results:
                package = results[0]
                price = float(package['price'])

                return {
                    "success": True,
                    "data": {
                        "amenity_code": package['code'],
                        "amenity_name": package['amenity_name'],
                        "package_name": package['package_name'],
                        "month_count": package['month_count'],
                        "duration_days": package['duration_days'],
                        "period_unit": package['period_unit'],
                        "price": price,
                        "price_formatted": f"{price:,.0f} VND"
                    }
                }
            else:
                return {
                    "success": False,
                    "error": f"Không tìm thấy gói {month_count} tháng cho tiện ích {amenity_code}"
                }
        except Exception as e:
            print(f"❌ Error in calculate_amenity_package_price: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    # ==================== APARTMENTS & FLOORS FUNCTIONS ====================

    @staticmethod
    def get_floors() -> Dict[str, Any]:
        """
        Lấy danh sách các tầng trong toà nhà

        Returns:
            Dict với data và count
        """
        # Check authentication
        auth_error = ApartmentAPI._check_authentication()
        if auth_error:
            return auth_error
        
        query = """
        SELECT
            floor_id,
            floor_number,
            name
        FROM {schema}.floors
        ORDER BY floor_number
        """

        try:
            results = db.execute_query(query)
            results = ApartmentAPI._convert_to_serializable(results)

            return {
                "success": True,
                "data": results,
                "count": len(results)
            }
        except Exception as e:
            print(f"❌ Error in get_floors: {e}")
            return {
                "success": False,
                "error": str(e),
                "data": [],
                "count": 0
            }

    @staticmethod
    def get_apartments(
        floor_number: Optional[int] = None,
        status: Optional[str] = None,
        apartment_type: Optional[str] = None,
        min_bedrooms: Optional[int] = None,
        max_bedrooms: Optional[int] = None,
        min_area: Optional[float] = None,
        max_area: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Lấy danh sách căn hộ với các bộ lọc

        Args:
            floor_number: Số tầng
            status: Trạng thái (AVAILABLE, OCCUPIED, RESERVED, MAINTENANCE)
            apartment_type: Loại căn hộ (Studio, 1BR, 2BR, 3BR, Penthouse...)
            min_bedrooms: Số phòng ngủ tối thiểu
            max_bedrooms: Số phòng ngủ tối đa
            min_area: Diện tích tối thiểu (m2)
            max_area: Diện tích tối đa (m2)

        Returns:
            Dict với data và count
        """
        # Check authentication
        auth_error = ApartmentAPI._check_authentication()
        if auth_error:
            return auth_error
        
        query = """
        SELECT
            a.apartment_id,
            a.floor_id,
            f.floor_number,
            f.name as floor_name,
            a.number as apartment_number,
            a.area_m2,
            a.bedrooms,
            a.status,
            a.type,
            a.created_at,
            a.updated_at
        FROM {schema}.apartments a
        INNER JOIN {schema}.floors f ON a.floor_id = f.floor_id
        WHERE 1=1
        """
        params = []

        if floor_number is not None:
            query += " AND f.floor_number = ?"
            params.append(floor_number)

        if status:
            query += " AND a.status = ?"
            params.append(status)

        if apartment_type:
            query += " AND a.type = ?"
            params.append(apartment_type)

        if min_bedrooms is not None:
            query += " AND a.bedrooms >= ?"
            params.append(min_bedrooms)

        if max_bedrooms is not None:
            query += " AND a.bedrooms <= ?"
            params.append(max_bedrooms)

        if min_area is not None:
            query += " AND a.area_m2 >= ?"
            params.append(min_area)

        if max_area is not None:
            query += " AND a.area_m2 <= ?"
            params.append(max_area)

        query += " ORDER BY f.floor_number, a.number"

        try:
            results = db.execute_query(query, tuple(params) if params else None)
            results = ApartmentAPI._convert_to_serializable(results)

            return {
                "success": True,
                "data": results,
                "count": len(results)
            }
        except Exception as e:
            print(f"❌ Error in get_apartments: {e}")
            return {
                "success": False,
                "error": str(e),
                "data": [],
                "count": 0
            }

    @staticmethod
    def get_apartment_by_number(apartment_number: str) -> Dict[str, Any]:
        """
        Lấy thông tin chi tiết căn hộ theo số căn

        Args:
            apartment_number: Số căn hộ (ví dụ: "101", "A-1203")

        Returns:
            Dict với thông tin căn hộ
        """
        # Check authentication
        auth_error = ApartmentAPI._check_authentication()
        if auth_error:
            return auth_error
        
        query = """
        SELECT
            a.apartment_id,
            a.floor_id,
            f.floor_number,
            f.name as floor_name,
            a.number as apartment_number,
            a.area_m2,
            a.bedrooms,
            a.status,
            a.type,
            a.image,
            a.created_at,
            a.updated_at
        FROM {schema}.apartments a
        INNER JOIN {schema}.floors f ON a.floor_id = f.floor_id
        WHERE a.number = ?
        """

        try:
            results = db.execute_query(query, (apartment_number,))
            results = ApartmentAPI._convert_to_serializable(results)

            if results:
                return {
                    "success": True,
                    "data": results[0]
                }
            else:
                return {
                    "success": False,
                    "error": f"Không tìm thấy căn hộ số: {apartment_number}"
                }
        except Exception as e:
            print(f"❌ Error in get_apartment_by_number: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    @staticmethod
    def get_available_apartments(
        apartment_type: Optional[str] = None,
        min_bedrooms: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Lấy danh sách căn hộ còn trống (AVAILABLE)

        Args:
            apartment_type: Loại căn hộ
            min_bedrooms: Số phòng ngủ tối thiểu

        Returns:
            Dict với data và count
        """
        return ApartmentAPI.get_apartments(
            status="AVAILABLE",
            apartment_type=apartment_type,
            min_bedrooms=min_bedrooms
        )

    @staticmethod
    def get_apartment_statistics() -> Dict[str, Any]:
        """
        Thống kê tổng quan về căn hộ

        Returns:
            Dict với thông tin thống kê
        """
        # Check authentication
        auth_error = ApartmentAPI._check_authentication()
        if auth_error:
            return auth_error
        
        query = """
        SELECT
            COUNT(*) as total_apartments,
            SUM(CASE WHEN status = 'AVAILABLE' THEN 1 ELSE 0 END) as available,
            SUM(CASE WHEN status = 'OCCUPIED' THEN 1 ELSE 0 END) as occupied,
            SUM(CASE WHEN status = 'RESERVED' THEN 1 ELSE 0 END) as reserved,
            SUM(CASE WHEN status = 'MAINTENANCE' THEN 1 ELSE 0 END) as maintenance,
            AVG(CAST(area_m2 AS FLOAT)) as avg_area,
            MIN(area_m2) as min_area,
            MAX(area_m2) as max_area
        FROM {schema}.apartments
        """

        try:
            results = db.execute_query(query)
            results = ApartmentAPI._convert_to_serializable(results)

            if results:
                stats = results[0]
                return {
                    "success": True,
                    "data": {
                        "total_apartments": stats.get('total_apartments', 0),
                        "available": stats.get('available', 0),
                        "occupied": stats.get('occupied', 0),
                        "reserved": stats.get('reserved', 0),
                        "maintenance": stats.get('maintenance', 0),
                        "avg_area_m2": round(stats.get('avg_area', 0), 2),
                        "min_area_m2": stats.get('min_area', 0),
                        "max_area_m2": stats.get('max_area', 0)
                    }
                }
            else:
                return {
                    "success": False,
                    "error": "Không có dữ liệu thống kê"
                }
        except Exception as e:
            print(f"❌ Error in get_apartment_statistics: {e}")
            return {
                "success": False,
                "error": str(e)
            }

# Create singleton instance
apartment_api = ApartmentAPI()