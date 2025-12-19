import google.generativeai as genai
import os
import json
from dotenv import load_dotenv
from typing import Optional
from api_endpoints import apartment_api

load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

# Define functions cho Gemini - SERVICE FEES & AMENITIES
FUNCTION_DECLARATIONS = [
    {
        "name": "get_service_types",
        "description": """
        Lấy danh sách các loại dịch vụ/phí trong hệ thống quản lý chung cư.
        
        Dùng khi user hỏi về:
        - "có những loại phí nào", "danh sách dịch vụ", "các loại phí"
        - "phí quản lý là gì", "phí gửi xe", "phí internet"
        - "cho tôi xem tất cả các phí"
        
        Ví dụ câu hỏi:
        - "Có những loại phí nào?"
        - "Cho tôi xem danh sách dịch vụ"
        - "Các loại phí Fee là gì?"
        - "Có những dịch vụ Utility nào?"
        """,
        "parameters": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "enum": ["Utility", "Fee", "Service", "Maintenance", "Other"],
                    "description": "Lọc theo danh mục: Utility (điện, nước), Fee (các loại phí), Service (dịch vụ bổ sung), Maintenance (bảo trì), Other (khác)"
                }
            }
        }
    },
    {
        "name": "get_service_prices",
        "description": """
        Lấy bảng giá của các dịch vụ/phí hiện đang áp dụng.
        
        Dùng khi user hỏi về:
        - "giá", "bảng giá", "phí bao nhiêu", "mức phí"
        - "chi phí", "đơn giá", "giá dịch vụ"
        - tên cụ thể: "phí quản lý bao nhiêu", "giá gửi xe"
        
        Ví dụ câu hỏi:
        - "Phí quản lý bao nhiêu?"
        - "Giá gửi xe ô tô là bao nhiêu?"
        - "Cho tôi xem bảng giá tất cả dịch vụ"
        - "Phí internet giá bao nhiêu?"
        """,
        "parameters": {
            "type": "object",
            "properties": {
                "service_type_code": {
                    "type": "string",
                    "description": "Mã dịch vụ: MGMT_FEE (phí quản lý), PARKING_CAR (gửi xe ô tô), PARKING_BIKE (gửi xe máy), INTERNET (internet), ADMIN_FEE (phí hành chính)"
                },
                "active_only": {
                    "type": "boolean",
                    "description": "True: chỉ lấy giá đang áp dụng hiện tại. False: lấy cả giá cũ"
                }
            }
        }
    },
    {
        "name": "calculate_service_fee",
        "description": """
        Tính toán tổng chi phí cho một dịch vụ cụ thể dựa trên số lượng.
        
        Dùng khi user hỏi về:
        - "tính phí", "tổng phí", "tính tiền"
        - "cần đóng bao nhiêu", "chi phí là bao nhiêu"
        - kèm số lượng: "cho căn 80m2", "2 xe ô tô", "3 tháng"
        
        Ví dụ câu hỏi:
        - "Tính phí quản lý cho căn 80m2"
        - "Phí gửi 2 xe ô tô là bao nhiêu?"
        - "Tổng phí internet 3 tháng?"
        - "Cần đóng bao nhiêu cho phí hành chính?"
        """,
        "parameters": {
            "type": "object",
            "properties": {
                "service_code": {
                    "type": "string",
                    "description": "Mã dịch vụ cần tính: MGMT_FEE, PARKING_CAR, PARKING_BIKE, INTERNET, ADMIN_FEE"
                },
                "quantity": {
                    "type": "number",
                    "description": "Số lượng cần tính (diện tích m2, số xe, số tháng...). Nếu không có thì là 1"
                }
            },
            "required": ["service_code"]
        }
    },
    {
        "name": "get_service_categories",
        "description": """
        Lấy danh sách các nhóm phân loại dịch vụ/phí.
        
        Dùng khi user hỏi về:
        - "phân loại", "nhóm dịch vụ", "categories"
        - "chia thành những loại nào", "có mấy nhóm"
        
        Ví dụ câu hỏi:
        - "Có những nhóm phí nào?"
        - "Phân loại dịch vụ như thế nào?"
        - "Dịch vụ được chia thành mấy loại?"
        """,
        "parameters": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "get_amenities",
        "description": """
        Lấy danh sách các tiện ích/dịch vụ có trong chung cư.

        Dùng khi user hỏi về:
        - "có tiện ích gì", "có những dịch vụ nào", "facilities"
        - "gym", "hồ bơi", "phòng họp", "sân tennis"
        - "danh sách tiện ích", "amenities"

        Ví dụ câu hỏi:
        - "Chung cư có những tiện ích gì?"
        - "Có phòng gym không?"
        - "Cho tôi xem danh sách tiện ích"
        - "Tiện ích nào cần xác thực khuôn mặt?"
        """,
        "parameters": {
            "type": "object",
            "properties": {
                "category_name": {
                    "type": "string",
                    "description": "Lọc theo loại tiện ích (Gym, Pool, Meeting Room, Tennis Court...)"
                },
                "status": {
                    "type": "string",
                    "enum": ["ACTIVE", "INACTIVE", "MAINTENANCE"],
                    "description": "Trạng thái tiện ích. Mặc định là ACTIVE"
                },
                "has_monthly_package": {
                    "type": "boolean",
                    "description": "True: chỉ lấy tiện ích có gói tháng. False: không có gói tháng"
                }
            }
        }
    },
    {
        "name": "get_amenity_by_code",
        "description": """
        Lấy thông tin chi tiết về một tiện ích cụ thể.

        Dùng khi user hỏi về tiện ích cụ thể:
        - "thông tin về gym", "chi tiết phòng họp"
        - "hồ bơi ở đâu", "gym có ở tầng mấy"

        Ví dụ câu hỏi:
        - "Cho tôi xem thông tin về phòng gym"
        - "Hồ bơi ở vị trí nào?"
        - "Meeting room cần xác thực khuôn mặt không?"
        """,
        "parameters": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Mã tiện ích cần xem (GYM_01, POOL_01, MEETING_01...)"
                }
            },
            "required": ["code"]
        }
    },
    {
        "name": "get_amenity_packages",
        "description": """
        Lấy danh sách các gói đăng ký theo tháng cho tiện ích.

        Dùng khi user hỏi về:
        - "gói tháng", "monthly package", "đăng ký theo tháng"
        - "giá gói", "bảng giá tiện ích"
        - "đăng ký gym bao nhiêu tiền"

        Ví dụ câu hỏi:
        - "Có gói tháng cho gym không?"
        - "Giá đăng ký gym 3 tháng là bao nhiêu?"
        - "Cho tôi xem các gói đăng ký hồ bơi"
        - "Bảng giá các tiện ích theo tháng"
        """,
        "parameters": {
            "type": "object",
            "properties": {
                "amenity_code": {
                    "type": "string",
                    "description": "Mã tiện ích cần xem gói (GYM_01, POOL_01...)"
                },
                "status": {
                    "type": "string",
                    "enum": ["ACTIVE", "INACTIVE"],
                    "description": "Trạng thái gói. Mặc định là ACTIVE"
                }
            }
        }
    },
    {
        "name": "calculate_amenity_package_price",
        "description": """
        Tính giá gói đăng ký tiện ích theo số tháng.

        Dùng khi user hỏi:
        - "tính tiền", "giá bao nhiêu"
        - "đăng ký X tháng"
        - "chi phí sử dụng"

        Ví dụ câu hỏi:
        - "Tính tiền đăng ký gym 6 tháng"
        - "Gói 3 tháng hồ bơi giá bao nhiêu?"
        - "Chi phí dùng phòng họp 1 tháng?"
        """,
        "parameters": {
            "type": "object",
            "properties": {
                "amenity_code": {
                    "type": "string",
                    "description": "Mã tiện ích (GYM_01, POOL_01, MEETING_01...)"
                },
                "month_count": {
                    "type": "integer",
                    "description": "Số tháng đăng ký (1, 3, 6, 12...)"
                }
            },
            "required": ["amenity_code", "month_count"]
        }
    },
    {
        "name": "get_floors",
        "description": """
        Lấy danh sách các tầng trong toà nhà.

        Dùng khi user hỏi về:
        - "có bao nhiêu tầng", "danh sách tầng"
        - "toà nhà có mấy tầng"

        Ví dụ câu hỏi:
        - "Toà nhà có bao nhiêu tầng?"
        - "Cho tôi xem danh sách các tầng"
        """,
        "parameters": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "get_apartments",
        "description": """
        Lấy danh sách căn hộ với các bộ lọc.

        Dùng khi user hỏi về:
        - "căn hộ", "apartment", "unit"
        - "tìm căn hộ", "xem căn hộ"
        - lọc theo: tầng, trạng thái, loại, số phòng, diện tích

        Ví dụ câu hỏi:
        - "Có căn hộ nào còn trống không?"
        - "Tìm căn hộ 2 phòng ngủ ở tầng 5"
        - "Căn hộ 80-100m2 còn trống"
        - "Xem căn hộ loại 2BR"
        """,
        "parameters": {
            "type": "object",
            "properties": {
                "floor_number": {
                    "type": "integer",
                    "description": "Số tầng (1, 2, 3...)"
                },
                "status": {
                    "type": "string",
                    "enum": ["AVAILABLE", "OCCUPIED", "RESERVED", "MAINTENANCE"],
                    "description": "Trạng thái: AVAILABLE (còn trống), OCCUPIED (đã thuê), RESERVED (đã đặt), MAINTENANCE (bảo trì)"
                },
                "apartment_type": {
                    "type": "string",
                    "description": "Loại căn hộ: Studio, 1BR, 2BR, 3BR, Penthouse..."
                },
                "min_bedrooms": {
                    "type": "integer",
                    "description": "Số phòng ngủ tối thiểu"
                },
                "max_bedrooms": {
                    "type": "integer",
                    "description": "Số phòng ngủ tối đa"
                },
                "min_area": {
                    "type": "number",
                    "description": "Diện tích tối thiểu (m2)"
                },
                "max_area": {
                    "type": "number",
                    "description": "Diện tích tối đa (m2)"
                }
            }
        }
    },
    {
        "name": "get_apartment_by_number",
        "description": """
        Lấy thông tin chi tiết về một căn hộ cụ thể theo số căn.

        Dùng khi user hỏi về căn hộ cụ thể:
        - "căn 101", "căn A-1203"
        - "thông tin căn hộ số X"

        Ví dụ câu hỏi:
        - "Cho tôi xem thông tin căn 101"
        - "Căn A-1203 bao nhiêu m2?"
        - "Căn 205 còn trống không?"
        """,
        "parameters": {
            "type": "object",
            "properties": {
                "apartment_number": {
                    "type": "string",
                    "description": "Số căn hộ (ví dụ: '101', 'A-1203', '2B-05')"
                }
            },
            "required": ["apartment_number"]
        }
    },
    {
        "name": "get_available_apartments",
        "description": """
        Lấy danh sách căn hộ còn trống (AVAILABLE).

        Dùng khi user hỏi:
        - "căn hộ còn trống", "available apartments"
        - "có căn nào trống", "xem căn trống"

        Ví dụ câu hỏi:
        - "Có căn hộ nào còn trống?"
        - "Cho tôi xem các căn còn trống"
        - "Căn 2 phòng ngủ còn trống không?"
        """,
        "parameters": {
            "type": "object",
            "properties": {
                "apartment_type": {
                    "type": "string",
                    "description": "Loại căn hộ: Studio, 1BR, 2BR, 3BR..."
                },
                "min_bedrooms": {
                    "type": "integer",
                    "description": "Số phòng ngủ tối thiểu"
                }
            }
        }
    },
    {
        "name": "get_apartment_statistics",
        "description": """
        Lấy thống kê tổng quan về căn hộ trong toà nhà.

        Dùng khi user hỏi về:
        - "thống kê", "tổng quan", "overview"
        - "có bao nhiêu căn", "số lượng căn hộ"

        Ví dụ câu hỏi:
        - "Cho tôi xem thống kê căn hộ"
        - "Có bao nhiêu căn đang trống?"
        - "Tổng quan về căn hộ trong toà nhà"
        """,
        "parameters": {
            "type": "object",
            "properties": {}
        }
    }
]

# Function mapping
FUNCTION_MAP = {
    "get_service_types": apartment_api.get_service_types,
    "get_service_prices": apartment_api.get_service_prices,
    "calculate_service_fee": apartment_api.calculate_service_fee,
    "get_service_categories": apartment_api.get_service_categories,
    "get_amenities": apartment_api.get_amenities,
    "get_amenity_by_code": apartment_api.get_amenity_by_code,
    "get_amenity_packages": apartment_api.get_amenity_packages,
    "calculate_amenity_package_price": apartment_api.calculate_amenity_package_price,
    "get_floors": apartment_api.get_floors,
    "get_apartments": apartment_api.get_apartments,
    "get_apartment_by_number": apartment_api.get_apartment_by_number,
    "get_available_apartments": apartment_api.get_available_apartments,
    "get_apartment_statistics": apartment_api.get_apartment_statistics,
}

class GeminiChatbot:
    def __init__(self, schema_name: Optional[str] = None):
        """
        Khởi tạo chatbot
        
        Args:
            schema_name: Schema name nếu đã đăng nhập, None nếu chưa đăng nhập
        """
        self.chat_session = None  # Lưu chat session để nhớ lịch sử
        self.schema_name = schema_name
        self.is_authenticated = schema_name is not None
        
        
        # System instruction khác nhau tùy vào authentication state
        if self.is_authenticated:
            # Authenticated mode: Có đầy đủ tools để query database
            system_instruction = """
            Bạn là trợ lý ảo thông minh cho hệ thống quản lý chung cư.

            NHIỆM VỤ CHÍNH:
            - Trả lời câu hỏi về phí dịch vụ (service fees)
            - Trả lời câu hỏi về tiện ích chung cư (amenities)
            - Trả lời câu hỏi về căn hộ (apartments) và tầng (floors)
            - Cung cấp thông tin giá cả, bảng giá
            - Tính toán chi phí
            - Tìm kiếm và lọc căn hộ theo yêu cầu
            - Giải thích các loại phí, tiện ích và thông tin căn hộ

            QUY TẮC XỬ LÝ:
            1. LUÔN gọi function để lấy dữ liệu thực từ database
            2. KHÔNG đoán hoặc tự nghĩ ra thông tin về giá, tiện ích
            3. Trả lời bằng tiếng Việt thân thiện, dễ hiểu
            4. Nếu không chắc chắn, hỏi lại user để làm rõ
            5. Hỗ trợ cả tiếng Việt và English
            6. Chấp nhận nhiều cách hỏi khác nhau (slang, typo OK)

            CÁCH HIỂU CÂU HỎI:

            Service Fees:
            - "phí", "dịch vụ", "chi phí", "tiền" → về service fees
            - "bao nhiêu", "giá", "mức" → get_service_prices
            - "tính", "tổng", "cần đóng" → calculate_service_fee
            - "có những loại", "danh sách" → get_service_types

            Amenities:
            - "tiện ích", "gym", "hồ bơi", "phòng họp", "facilities" → get_amenities
            - "gói tháng", "đăng ký", "monthly package" → get_amenity_packages
            - "tính tiền gym", "giá đăng ký" → calculate_amenity_package_price
            - "thông tin chi tiết về X" → get_amenity_by_code

            Apartments & Floors:
            - "căn hộ", "apartment", "tìm căn" → get_apartments
            - "căn còn trống", "available" → get_available_apartments
            - "căn 101", "thông tin căn X" → get_apartment_by_number
            - "thống kê căn hộ", "tổng quan" → get_apartment_statistics
            - "tầng", "floors" → get_floors

            FORMAT TRẢ LỜI:
            - Với giá: format số có dấu phẩy (ví dụ: 100,000 VND)
            - Với tính toán: hiển thị chi tiết (đơn giá × số lượng = tổng)
            - Với danh sách: trình bày rõ ràng, dễ đọc
            - Ngắn gọn, không dài dòng
            - Sử dụng emoji phù hợp để thân thiện hơn 💰📊🏊‍♂️🏋️
            """
            tools = [{"function_declarations": FUNCTION_DECLARATIONS}]
        else:
            # Unauthenticated mode: Chỉ giới thiệu website, KHÔNG có tools
            system_instruction = """
            Bạn là trợ lý ảo giới thiệu về hệ thống quản lý chung cư.

            NHIỆM VỤ CHÍNH:
            1. Giới thiệu về website/dịch vụ quản lý chung cư
            2. Hướng dẫn đăng nhập để truy cập dữ liệu
            3. Trả lời câu hỏi chung về chung cư (KHÔNG có dữ liệu cụ thể từ database)

            CÁC CHỦ ĐỀ CÓ THỂ TRẢ LỜI:
            - Giới thiệu về hệ thống quản lý chung cư
            - Các tính năng của website
            - Hướng dẫn đăng nhập
            - Câu hỏi chung về chung cư (không cần dữ liệu cụ thể)

            QUY TẮC QUAN TRỌNG:
            1. KHÔNG được gọi bất kỳ function nào để query database
            2. Nếu user hỏi về dữ liệu cụ thể (giá phí, căn hộ, tiện ích...):
               → Nhắc họ: "Để xem thông tin chi tiết, vui lòng đăng nhập vào hệ thống."
            3. Giữ thái độ thân thiện, chào mừng
            4. Trả lời bằng tiếng Việt thân thiện, dễ hiểu
            5. Hỗ trợ cả tiếng Việt và English

            VÍ DỤ CÂU TRẢ LỜI:
            - "Chào bạn! Tôi là trợ lý ảo của hệ thống quản lý chung cư. Tôi có thể giúp bạn tìm hiểu về hệ thống và hướng dẫn đăng nhập."
            - "Để xem thông tin chi tiết về phí dịch vụ, căn hộ, tiện ích... vui lòng đăng nhập vào hệ thống."
            - "Hệ thống của chúng tôi cung cấp các tính năng: quản lý phí dịch vụ, tiện ích chung cư, thông tin căn hộ..."
            """
            tools = []  # Không có tools cho unauthenticated mode
        
        self.model = genai.GenerativeModel(
            model_name='gemini-2.5-flash',
            tools=tools,
            system_instruction=system_instruction
        )
    
    def start_new_conversation(self):
        """Bắt đầu cuộc hội thoại mới (xóa lịch sử cũ)"""
        self.chat_session = None
        print("🔄 Đã bắt đầu cuộc hội thoại mới!")

    def chat(self, user_message: str) -> dict:
        """
        Xử lý tin nhắn từ user (với lịch sử hội thoại)

        Args:
            user_message: Câu hỏi từ user

        Returns:
            dict: {
                "success": bool,
                "response": str,
                "function_calls": list,
                "data": dict
            }
        """
        try:
            # Nếu chưa có chat session, tạo mới
            if self.chat_session is None:
                self.chat_session = self.model.start_chat()

            # Sử dụng chat session hiện tại (có lịch sử)
            response = self.chat_session.send_message(user_message)
            
            function_calls_log = []
            all_data = {}
            
            # Xử lý function calling (chỉ khi đã authenticated và có tools)
            # Check nếu response có function_call
            def has_function_call(resp):
                """Helper function để check xem response có function_call không"""
                try:
                    if (resp.candidates and 
                        len(resp.candidates) > 0 and
                        resp.candidates[0].content.parts and 
                        len(resp.candidates[0].content.parts) > 0):
                        part = resp.candidates[0].content.parts[0]
                        return hasattr(part, 'function_call') and part.function_call is not None
                except:
                    pass
                return False
            
            # Xử lý function calling (chỉ khi authenticated và có tools)
            while has_function_call(response):
                # Double check: Nếu không authenticated, block ngay
                if not self.is_authenticated:
                    break
                
                function_call = response.candidates[0].content.parts[0].function_call
                
                # Validate function_call
                if not function_call or not hasattr(function_call, 'name'):
                    break
                
                function_name = function_call.name
                
                # Validate function_name không được rỗng
                if not function_name or function_name.strip() == "":
                    break
                
                # Xử lý args - có thể là None hoặc không có
                if hasattr(function_call, 'args') and function_call.args is not None:
                    function_args = dict(function_call.args)
                else:
                    function_args = {}
                
                # Log function call
                function_calls_log.append({
                    "function": function_name,
                    "args": function_args
                })
                
                # Gọi function thực tế
                if function_name in FUNCTION_MAP:
                    api_result = FUNCTION_MAP[function_name](**function_args)
                    all_data[function_name] = api_result
                else:
                    api_result = {"error": f"Function {function_name} not found"}
                
                # Trả kết quả cho Gemini (sử dụng chat session hiện tại)
                if function_name and function_name.strip():
                    response = self.chat_session.send_message(
                        genai.protos.Content(
                            parts=[genai.protos.Part(
                                function_response=genai.protos.FunctionResponse(
                                    name=function_name,
                                    response={"result": api_result}
                                )
                            )]
                        )
                    )
                else:
                    break
            
            # Lấy câu trả lời cuối cùng
            final_response = response.text
            
            return {
                "success": True,
                "response": final_response,
                "function_calls": function_calls_log,
                "data": all_data
            }
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                "success": False,
                "response": f"Xin lỗi, có lỗi xảy ra: {str(e)}",
                "error": str(e)
            }

# Note: Không tạo instance global nữa vì mỗi session sẽ có instance riêng với schema riêng