# -*- coding: utf-8 -*-
"""
APARTMENT CHATBOT - INTERACTIVE DEMO
Test chatbot với đầy đủ chức năng: Service Fees, Amenities, Apartments, Floors
"""
from gemini_bot import chatbot
import sys
import io

# Fix encoding cho Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding='utf-8')

def print_header():
    """In header"""
    print("\n" + "=" * 80)
    print("           🏢 APARTMENT CHATBOT - DEMO TƯƠNG TÁC")
    print("=" * 80)
    print("\n🎉 Chào mừng đến với chatbot quản lý chung cư!")
    print("\n📋 CHỨC NĂNG:")
    print("  💰 Service Fees   - Hỏi về phí dịch vụ, giá cả")
    print("  🏊 Amenities      - Hỏi về tiện ích (gym, hồ bơi, phòng họp...)")
    print("  🏠 Apartments     - Tìm kiếm căn hộ, xem thông tin căn hộ")
    print("  🏗️  Floors         - Xem thông tin tầng")
    print("\n💡 Ví dụ câu hỏi:")
    print("  • 'Có những loại phí nào?'")
    print("  • 'Chung cư có những tiện ích gì?'")
    print("  • 'Tìm căn hộ 2 phòng ngủ còn trống'")
    print("  • 'Căn 101 bao nhiêu m2?'")
    print("  • 'Cho tôi xem thống kê căn hộ'")
    print("  • 'Toà nhà có bao nhiêu tầng?'")
    print("  • 'Giá đăng ký gym 3 tháng là bao nhiêu?'")
    print("\n⌨️  Gõ 'exit', 'quit', hoặc 'thoát' để kết thúc")
    print("⌨️  Gõ 'reset' hoặc 'mới' để bắt đầu cuộc hội thoại mới")
    print("=" * 80 + "\n")

def print_separator():
    """In đường phân cách"""
    print("-" * 80)

def main():
    """Main chatbot loop"""
    print_header()

    conversation_count = 0

    while True:
        # Nhập câu hỏi
        try:
            question = input("\n❓ Bạn: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\n👋 Tạm biệt!")
            break

        # Kiểm tra exit
        if question.lower() in ['exit', 'quit', 'thoát', 'bye', 'thoat']:
            print("\n👋 Cảm ơn bạn đã sử dụng chatbot! Tạm biệt!")
            break

        # Kiểm tra reset conversation
        if question.lower() in ['reset', 'mới', 'moi', 'new']:
            chatbot.start_new_conversation()
            conversation_count = 0
            continue

        # Kiểm tra empty
        if not question:
            continue

        print_separator()

        # Gọi chatbot
        try:
            result = chatbot.chat(question)

            if result["success"]:
                conversation_count += 1

                # Hiển thị functions được gọi (debug info)
                if result.get("function_calls"):
                    print("\n🔧 [DEBUG] Functions called:")
                    for fc in result["function_calls"]:
                        func_name = fc['function']
                        func_args = fc['args']
                        print(f"  → {func_name}({func_args})")

                # Hiển thị câu trả lời
                print(f"\n🤖 Bot: {result['response']}")

            else:
                print(f"\n❌ [ERROR] Lỗi: {result.get('error', 'Unknown error')}")
                print("Vui lòng thử lại hoặc hỏi câu hỏi khác.")

        except Exception as e:
            print(f"\n⚠️  [EXCEPTION] Đã xảy ra lỗi: {e}")
            print("Vui lòng thử lại.")

        print_separator()

    # Summary
    if conversation_count > 0:
        print(f"\n📊 Đã xử lý {conversation_count} câu hỏi thành công!")

    print("\n" + "=" * 80)
    print("           🙏 CẢM ƠN ĐÃ SỬ DỤNG APARTMENT CHATBOT!")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Chương trình bị ngắt bởi người dùng. Tạm biệt!")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Lỗi không mong muốn: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
