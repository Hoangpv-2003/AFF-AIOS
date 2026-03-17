# Quy Trình Lập Trình & Thiết Kế Hệ Thống Cùng AI (AAF-AIOS)

Tài liệu này hướng dẫn chi tiết phương pháp làm việc phối hợp giữa Con Người và các AI Agents trong việc thiết kế, lập trình và xây dựng các chức năng từ cấp độ tổng quan xuống các micro-features (chức năng siêu nhỏ) theo kiến trúc hiện có.

---

## 1. Triết Lý Thiết Kế: Nhìn Rộng, Cắt Nhỏ, Chạy Tự Động
Trong dự án AAF-AIOS, chúng ta không viết toàn bộ hệ thống ngay từ đầu. Chúng ta hoạt động theo nguyên tắc:
1. **Human (Con người)** đưa ra định hướng chiến lược (Roadmap, Domains).
2. **Planner Agent** phân tích thành các Sub-tasks hoặc Micro-features cực nhỏ.
3. **Manager Agent** điều phối công việc cho Coder Agent tạo base code.
4. **Reviewer Agent** thẩm định, chạy sandbox, lưu trace.
5. **System** tự động đóng gói thành Skill hoặc thư viện dùng chung, đẩy vào RAG Database để tái sử dụng.

---

## 2. Quy Trình Chi Tiết Các Giai Đoạn

### Giai Đoạn A: System Discovery (Khám phá & Căn chỉnh Kiến trúc)
**Công cụ hỗ trợ**: Kỹ năng `aaf-system-explorer` và `aaf-aios-architect`.
- **Mục tiêu**: Khi chuẩn bị làm một chức năng mới, tuyệt đối không code mù (blind code). AI cần phải "đọc hiểu" những gì hệ thống đang có.
- **Cách làm**: 
  - Gọi Agent và yêu cầu: *"Dùng aaf-system-explorer quét toàn bộ folder `app/api` và `app/core` để hiểu cách chúng ta setup Dependency Injection và Router."*
  - AI sẽ rút trích đúng Schema hoặc base class đang có (VD: `BaseAgent`) để viết code kế thừa, không bị lệch chuẩn Clean Architecture.

### Giai Đoạn B: Micro-Feature Decomposition (Chẻ nhỏ chức năng)
**Công cụ hỗ trợ**: Planner Agent.
- Thay vì yêu cầu *"Xây dựng tính năng đăng nhập"*, hãy yêu cầu:
  1. Yêu cầu 1: *"Viết Pydantic schemas cho UserLoginRequest và TokenResponse (Vào `app/schemas`)."*
  2. Yêu cầu 2: *"Cập nhật `app/core/security.py` thêm hàm hash chuỗi, tạo JWT token."*
  3. Yêu cầu 3: *"Tạo endpoint `POST /login` tại `app/api/v1/endpoints/auth.py` và nhúng các service kia vào."*
- **Sức mạnh của Agent**: Planner Agent có thể nhận yêu cầu tổng, tự sinh ra 3 yêu cầu con bên trên. Con người chỉ duyệt (Approve) và để Coder bắt tay thực hiện.

### Giai Đoạn C: Code Generation & Auto-Skill Registration
- **Code Core Logic**: Coder Agent sinh mã dựa trên các Micro-Features.
- **Thử nghiệm mã (Sandboxing)**: Reviewer Agent sinh file Unit Test (hoặc Pytest snippet), chạy thử trong hàm cô lập.
- **Tạo Skill**: Khái niệm tính năng (Feature) và Kỹ năng (Skill) đôi khi giao thoa. Nếu chức năng đó là *"Trích xuất dữ liệu từ PDF"*, nó không chỉ thuộc về API mà nên sinh thành một file Python đứng độc lập trong `app/skills/dynamic/` và đăng ký vào `app/skills/registry.py`. Đóng gói thành `.skill` (kèm SKILL.md) sẽ giúp Manager Agent tự nhìn thấy tính năng này cho các task sau.

### Giai Đoạn D: RAG Storage & Auto-Tracing (Tự Đánh Giá & Ghi Nhớ)
- **Tracing**: Mỗi yêu cầu từ người dùng (Vd: *"Fix lỗi database timeout"*) được gắn 1 `trace_id`. Toàn bộ log API gọi DB, log thought processes của Coder Agent đều đẩy qua OpenTelemetry.
- **Khép vòng RAG**: Sau khi dev xong chức năng, Reviewer Agent đẩy `{Prompt: 'Làm sao tạo JWT ở AAF', Solution: 'Gửi code security.py'}` vào VectorDB. Lần sau Manager Agent sẽ giải quyết bài toán dạng hash bảo mật chỉ trong 1 nốt nhạc mà không cần "suy nghĩ" lại.

---

## 3. Best Practices Cho Lập Trình Viên Khi Lệnh Cho Hệ Thống
1. **Cực kỳ cụ thể vị trí**: "Anh muốn em tạo hàm X, đặt ở layer `app/infrastructure`, tuân thủ interface Y ở `app/domain/`."
2. **Sử dụng Skill thay vì Nhắc lại Prompt**: Nếu một quy trình lặp lại quá 3 lần (Vd: Khởi tạo Entity, DTO, Repository cho database MongoDB), hãy bảo AI *"Viết cho anh một Skill tên là aaf-mongo-crud-generator, lưu lại ở dạng SKILL.md để anh dùng lần sau."*
3. **Tuân thủ Boundary**: Không cho Coder Agent nhảy thẳng từ Router xuống truy vấn SQL. Yêu cầu Agent tạo đúng Repository và Service layer.

## Tóm lại
Với AAF-AIOS, lập trình viên chuyển vai trò từ "Thợ gõ phím" sang "Kiến trúc sư trưởng". Các Agent trở thành công cụ đắc lực giải quyết chi tiết. Càng tạo nhiều Skill rõ ràng (`SKILL.md`), hệ thống càng tích lũy lượng "Kiến thức nội bộ" nhanh và code càng ít lỗi.

---

## Glossary
- `task`: yêu cầu công việc ở mức người dùng hoặc hệ thống gửi vào pipeline.
- `plan`: kết quả decomposition từ Planner, gồm steps và phụ thuộc.
- `run`: một lần thực thi pipeline hoặc một bước của pipeline có trạng thái và kết quả riêng.
- `trace`: chuỗi sự kiện có correlation id để theo dõi end-to-end.
- `skill`: artifact có thể tái sử dụng (code + metadata + approval state).
- `approval`: quyết định của con người/hệ thống để cho phép activate skill.

## Contract Lifecycle
1. Giai đoạn đầu dùng schema hậu tố `Draft` để giảm rủi ro khóa contract quá sớm.
2. Sau khi spike agent-contract ổn định và integration tests pass, tạo schema `Stable` (không hậu tố).
3. Duy trì compatibility window cho `Draft` trong một release cycle.
4. Loại bỏ `Draft` khi telemetry xác nhận usage về 0.
