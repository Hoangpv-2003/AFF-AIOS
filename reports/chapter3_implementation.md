# Chương 3: Triển khai hệ thống (System Implementation)

Chương này trình bày chi tiết về quá trình triển khai kỹ thuật của dự án **AFF-AIOS** (Artificial Intelligence Operating System), bao gồm môi trường phát triển, kiến trúc hệ thống, các module cốt lõi và hạ tầng kỹ thuật.

## 3.1. Môi trường triển khai và Công cụ phát triển

Hệ thống được xây dựng trên nền tảng ngôn ngữ Python hiện đại, tận dụng các thư viện tối ưu cho xử lý bất đồng bộ và trí tuệ nhân tạo.

*   **Ngôn ngữ lập trình**: Python 3.11+.
*   **Framework chính**:
    *   **FastAPI**: Sử dụng để xây dựng lớp API RESTful với hiệu năng cao và hỗ trợ Type Hinting mạnh mẽ qua Pydantic.
    *   **Uvicorn**: Server ASGI phục vụ ứng dụng FastAPI.
*   **Quản lý dữ liệu**:
    *   **MongoDB**: Cơ sở dữ liệu NoSQL dùng để lưu trữ thông tin về Agent, Task, Skill và các bản ghi Trace.
    *   **Redis**: Hệ thống lưu trữ trong bộ nhớ (In-memory) phục vụ hàng đợi tác vụ (Queue) và caching.
    *   **Qdrant / ChromaDB**: Cơ sở dữ liệu Vector (Vector Database) dùng cho cơ chế RAG (Retrieval-Augmented Generation) và bộ nhớ dài hạn của Agent.
*   **Công nghệ Container**:
    *   **Docker & Docker Compose**: Đóng gói toàn bộ hệ thống (API, DB, Redis) giúp triển khai nhất quán trên các môi trường khác nhau.
*   **Mô hình ngôn ngữ (LLM)**:
    *   Hỗ trợ kết nối với các mô hình qua **Ollama** (chạy local) hoặc các API Cloud (OpenAI, Anthropic).

## 3.2. Cấu trúc và Kiến trúc hệ thống

Dự án AFF-AIOS tuân thủ nghiêm ngặt nguyên tắc **Clean Architecture** và **Domain-Driven Design (DDD)** nhằm đảm bảo tính mở rộng và dễ bảo trì.

### 3.2.1. Phân tầng mã nguồn (Project Structure)
Mã nguồn được tổ chức trong thư mục `app/` theo các lớp chức năng:
*   `app/api/`: Định nghĩa các Router, Endpoints (v1) và Dependency Injection.
*   `app/core/`: Chứa các cấu hình hệ thống (`config.py`), hằng số và cơ chế bảo mật.
*   `app/agents/`: Triển khai các lớp Agent (BaseAgent, Manager, Coder, Reviewer).
*   `app/brain/`: Tầng tư duy và lập kế hoạch (Planner, Memory, Prompt templates).
*   `app/skills/`: Quản lý các kỹ năng (Skills) tĩnh và động.
*   `app/infrastructure/`: Triển khai giao tiếp với các dịch vụ bên ngoài (DB, Sandboxes, Observability).
*   `app/schemas/`: Định nghĩa các Model dữ liệu (Pydantic) dùng cho Request/Response và Validation.

## 3.3. Triển khai các Module cốt lõi

### 3.3.1. Hệ thống Tác nhân (Multi-Agent System)
Hệ thống được triển khai theo mô hình điều phối (Orchestration) với 3 vai trò chính:
1.  **Manager Agent**: Tiếp nhận yêu cầu từ người dùng, quản lý vòng đời của Task và điều phối các Agent khác.
2.  **Coder Agent**: Chuyên trách viết mã nguồn Python để giải quyết một Sub-task cụ thể.
3.  **Reviewer Agent**: Thẩm định mã nguồn, thực thi trong môi trường Sandbox và đưa ra đánh giá.

### 3.3.2. Cơ chế Lập kế hoạch (Dynamic Planning)
Sử dụng **Planner** trong module `brain` để phân tích yêu cầu ngôn ngữ tự nhiên thành một danh sách các công việc nhỏ (Sub-tasks) có thứ tự ưu tiên và phụ thuộc lẫn nhau.

### 3.3.3. Tự động sinh Kỹ năng (Auto-Skill Generation)
Khi hệ thống nhận thấy thiếu công cụ để giải quyết vấn đề, **Coder Agent** sẽ sinh mã. Sau khi được **Reviewer** phê duyệt, mã này sẽ được đăng ký vào `Skill Registry` và lưu trữ dưới dạng một Skill mới, có thể tái sử dụng ngay lập tức mà không cần sinh lại mã.

## 3.4. Hạ tầng kỹ thuật và Bảo mật

### 3.4.1. Môi trường thực thi an toàn (Sandbox)
Để xử lý mã độc hại hoặc lỗi tiềm tàng khi thực thi mã do AI sinh ra, AFF-AIOS triển khai một lớp **Docker Sandbox**. Mã nguồn sẽ được chạy trong một Container cô lập với hệ thống chính, giới hạn tài nguyên (CPU, RAM) và quyền truy cập mạng.

### 3.4.2. Khả năng quan sát và Truy vết (Observability & Tracing)
Hệ thống tích hợp cơ chế **Auto-Tracing** (sử dụng OpenTelemetry hoặc LangSmith). Mỗi yêu cầu được gắn một `trace_id` duy nhất, cho phép theo dõi toàn bộ luồng:
`Người dùng -> Planner -> Manager -> Coder -> Sandbox -> Kết quả`.

### 3.4.3. Quản lý ngân sách (Budget & Resource Management)
Mỗi Task và User được gán các hạn mức (Budget) về số lượng Token LLM và tài nguyên máy tính sử dụng, giúp ngăn chặn việc lãng phí tài nguyên hoặc lỗi lặp vô tận (infinite loops).

## 3.5. Triển khai và Vận hành (Deployment)

Hệ thống được triển khai bằng Docker Compose, phối hợp các dịch vụ:
1.  **API Service**: Chạy mã nguồn Python/FastAPI.
2.  **Redis Service**: Cung cấp hàng đợi tác vụ cho các Agent xử lý ngầm.
3.  **Local Registry**: Lưu trữ các Artifacts và Metadata của hệ thống.

Quy trình triển khai tuân thủ các **Release Gates**, đảm bảo các bài kiểm thử (Unit Test, Integration Test) phải vượt qua trước khi mã nguồn được cập nhật lên môi trường sản xuất.
