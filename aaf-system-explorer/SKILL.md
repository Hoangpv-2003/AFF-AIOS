---
name: aaf-system-explorer
description: The ultimate skill for exploring, querying, and reading the entire AAF-AIOS system structure and contents. This skill allows Agents to avoid blind-coding by performing a full context read before modifying the repository. Use this to trace the codebase, discover available endpoints, find related architectures, and fetch existing rules or schemas before designing new micro-features. Trigger this when asked to "analyze the code", "find related data", "read all files in directory", or "search for existing implementations of X".
---

# AAF-System-Explorer Skill

A robust retrieval and discovery skill for navigating the `C:\AI\AAF - AIOS` repository system.

## 1. Mục Đích Của Skill (Purpose)
- **Chống mã hoá mù (Anti-Blind-Coding)**: Đảm bảo bất kỳ Agent nào khởi tạo cũng phải đọc bối cảnh trước khi ghi đè hoặc sinh file mới.
- **Khám phá Bối cảnh (Context Discovery)**: Hỗ trợ rà soát cấu trúc thư mục, tệp lệnh, các đoạn code hiện có tại các tầng như `app/api`, `app/core`, hay `app/infrastructure`.
- **Ánh xạ Mã (Code Tracing)**: Tìm kiếm references (chiếu ứng) để biết một hàm hay schema được gọi ở đâu trong toàn bộ dự án.

## 2. Cách Vận Hành (How to Operate)

Khi User hoặc System yêu cầu khám phá một vấn đề trong mã nguồn:
1. **List System Scope (Quét tầm phủ)**: Sử dụng công cụ tương đương lệnh `list_dir` tại root (`C:\AI\AAF - AIOS`) hoặc các thư mục con cụ thể như `app/skills/` để lướt xem danh sách các file hiện hữu.
2. **Grep and Search (Tìm kiếm nội dung)**: Sử dụng công cụ tương đương lệnh `grep_search` hoặc các bộ máy tìm kiếm (như ripgrep/Vector DB sau này) để định vị từ khóa liên quan như "BaseAgent", "UserSchema", "Dependency Injection".
3. **Deep Read (Đọc sâu)**: Dùng công cụ `view_file` mở các file tìm được để tổng hợp logic.
4. **Synthesize (Tổng hợp)**: Trả về một bản báo cáo ngắn gọn (Report) về nơi file đó tồn tại, nó phụ thuộc vào ai và ai gọi đến nó, kèm theo gợi ý cho bước code tiếp theo.

## 3. Best Practices (Quy Chuẩn Khi Dùng Skill Này)

### A. Phân tích tác động (Impact Analysis)
Trước khi Agent quyết định chỉnh sửa `app/api/router.py`:
- Kích hoạt **aaf-system-explorer** tìm kiếm: "Có file nào đang gọi router này không?"
- Đọc `app/main.py` để xem Router được Include thế nào.
- Chỉ khi đảm bảo an toàn, Agent mới viết mã chỉnh sửa.

### B. Tìm mẫu có sẵn (Pattern Matching)
Nếu cần thêm chức năng Database thao tác bảng `Products`:
- Dùng skill này quét tìm file `app/infrastructure/database/base.py` hoặc các code thao tác `Users` có sẵn để mô phỏng tương tự (Mimic existing patterns).

### C. Yêu Cầu Xác Nhận Trước Khi Truy Cập (User Confirmation Required)
**QUY TẮC BẮT BUỘC:** Việc truy cập nội dung các file hoặc quét danh sách thư mục (ngoại trừ các đường dẫn public/base đã được ủy quyền) yêu cầu **phải có sự xác nhận rõ ràng từ phía người dùng (User)** trước khi thực thi lệnh.
- Khi Agent cần đọc file hoặc liệt kê thư mục, Agent **phải dừng lại và hỏi người dùng**: *"Tôi cần truy cập đường dẫn `X` để hoàn thành tác vụ này. Cậu xác nhận cho phép tôi đọc nội dung đường dẫn này chứ?"*
- Chỉ khi người dùng nói "Đồng ý", "Cấp phép", "Tiếp tục" hoặc tương tự, Agent mới được phép gọi các tool như `list_dir` hoặc `view_file` vào đường dẫn đó.

### D. Khám Phá Tri Thức Tự Động RAG (Dự kiến trong Roadmap Phase 3)
Kỹ năng này chịu trách nhiệm tích hợp với `Vector DB` của hệ thống:
1. Lấy `query` từ người dùng (VD: "Làm sao kết nối Pinecone?").
2. Query thẳng vào Vector DB API của hệ thống (khi Phase 3 hoàn tất).
3. Đem dữ liệu nạp lại vào ngữ cảnh lập trình.
4. Triển khai theo RAG thay vì tự chế (hallucinate).

## 4. Trigger Trực Tiếp Bằng Câu Lệnh (Prompts)
- "Quét thư mục `X` và liệt kê toàn bộ interface bên trong."
- "Kiểm tra xem file `Y` có ai reference tới nó trong project `C:\AI\AAF - AIOS` không."
- "Dùng aaf-system-explorer đọc hiểu luồng code `Z` từ API xuôi xuống Database."
- "Tìm toàn bộ file chứa từ khoá liên quan tới `Trace` hay `OpenTelemetry`."

---
*Lưu ý cho LLM Agent*: Đừng vội sinh code, hãy luôn gọi skill này đầu tiên để tạo nền tảng vững chắc (Solid Context).
