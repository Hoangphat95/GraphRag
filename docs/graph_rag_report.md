# Báo cáo triển khai hệ thống Graph-RAG trong `graph_rag_enterprise_2`

## Mục tiêu báo cáo

Báo cáo này ghi lại lại toàn bộ hệ thống theo đúng project `graph_rag_enterprise_2`, không dùng nhầm các file của project khác. Nội dung tập trung vào 2 phần chính:

1. Các bước xây dựng hệ thống từ đầu đến cuối, kèm file liên quan, việc đã làm và kết quả thu được.
2. Luồng xử lý của chatbot, nêu rõ từng bước nằm ở file nào, file đó làm gì, và đầu ra mong đợi là gì.

---

## 1. Các bước đã thực hiện để tạo hệ thống end-to-end

### 1.1. Thiết kế schema và cấu hình nền tảng

- **File chính**: [graph_rag_enterprise_2/cypher/graph_schema.json](graph_rag_enterprise_2/cypher/graph_schema.json#L1), [graph_rag_enterprise_2/config/settings.py](graph_rag_enterprise_2/config/settings.py#L1)
- **Việc đã làm**:
	- Xác định schema đồ thị: các node, relationship, thuộc tính và quy ước đặt tên.
	- Khai báo các thông số vận hành như endpoint, model, ngưỡng truy hồi, thông tin kết nối dịch vụ.
- **Kết quả**:
	- Hệ thống có cấu trúc dữ liệu thống nhất để nạp vào Neo4j.
	- Các module phía sau có nguồn cấu hình chung để chạy đồng bộ.

### 1.2. Chuẩn bị và nạp dữ liệu vào đồ thị

- **File chính**: [graph_rag_enterprise_2/db/kg_loader.py](graph_rag_enterprise_2/db/kg_loader.py#L1), [graph_rag_enterprise_2/db/neo4j_client.py](graph_rag_enterprise_2/db/neo4j_client.py#L1)
- **Việc đã làm**:
	- Viết loader để đọc dữ liệu nguồn, chuẩn hóa dữ liệu và ánh xạ vào node/edge trong graph.
	- Tạo client để kết nối và thực thi truy vấn trên Neo4j.
	- Kiểm tra lại việc insert dữ liệu theo schema đã thiết kế.
- **Kết quả**:
	- Dữ liệu được nạp vào Neo4j thành công.
	- Đồ thị có thể truy vấn được bằng Cypher.

### 1.3. Xây dựng lớp hiểu ý định người dùng

- **File chính**: [graph_rag_enterprise_2/llm/intent_classifier.py](graph_rag_enterprise_2/llm/intent_classifier.py#L1)
- **Việc đã làm**:
	- Tạo mô hình hoặc wrapper để phân loại câu hỏi của người dùng theo intent.
	- Xác định câu hỏi thuộc nhóm nào: truy vấn kiến thức, tra cứu thông tin, cần sinh Cypher, hoặc trả lời tổng quát.
- **Kết quả**:
	- Chatbot biết chọn đường xử lý phù hợp thay vì trả lời một cách cứng nhắc.

### 1.4. Thiết kế planner và sinh Cypher

- **File chính**: [graph_rag_enterprise_2/planner/query_planner.py](graph_rag_enterprise_2/planner/query_planner.py#L1), [graph_rag_enterprise_2/cypher/cypher_generator.py](graph_rag_enterprise_2/cypher/cypher_generator.py#L1)
- **Việc đã làm**:
	- Viết logic lập kế hoạch truy vấn từ intent và thực thể nhận diện được.
	- Sinh câu lệnh Cypher đúng với schema đồ thị.
	- Rà soát để tránh Cypher quá dài hoặc sai kiểu dữ liệu.
- **Kết quả**:
	- Có thể tạo truy vấn graph hợp lệ để lấy dữ liệu động từ Neo4j.

### 1.5. Xây dựng retriever lai

- **File chính**: [graph_rag_enterprise_2/retriever/hybrid_retriever.py](graph_rag_enterprise_2/retriever/hybrid_retriever.py#L1)
- **Việc đã làm**:
	- Kết hợp tìm kiếm theo vector embedding với truy vấn đồ thị.
	- Lấy ra các context liên quan nhất để đưa vào prompt cho LLM.
- **Kết quả**:
	- Hệ thống không phụ thuộc vào một nguồn duy nhất; vừa có semantic search vừa có graph grounding.

### 1.6. Tạo lớp sinh câu trả lời

- **File chính**: [graph_rag_enterprise_2/llm/llm_client.py](graph_rag_enterprise_2/llm/llm_client.py#L1), [graph_rag_enterprise_2/llm/answer_generator.py](graph_rag_enterprise_2/llm/answer_generator.py#L1)
- **Việc đã làm**:
	- Kết nối tới LLM.
	- Tạo prompt chứa câu hỏi người dùng, context đã truy hồi và các ràng buộc trả lời.
	- Sinh ra câu trả lời cuối cùng theo ngữ cảnh hệ thống.
- **Kết quả**:
	- Bot trả lời mạch lạc hơn, có bám vào dữ liệu đã truy hồi.

### 1.7. Tích hợp pipeline và orchestrator

- **File chính**: [graph_rag_enterprise_2/pipeline/rag_pipeline.py](graph_rag_enterprise_2/pipeline/rag_pipeline.py#L1), [graph_rag_enterprise_2/pipeline/orchestrator_v3.py](graph_rag_enterprise_2/pipeline/orchestrator_v3.py#L1)
- **Việc đã làm**:
	- Ghép toàn bộ các khối: nhận query, phân loại intent, truy hồi context, sinh prompt, gọi LLM, hậu xử lý.
	- Tạo điểm điều phối trung tâm để kiểm soát thứ tự xử lý.
- **Kết quả**:
	- Hệ thống hoạt động như một pipeline thống nhất, không rời rạc theo từng module riêng lẻ.

### 1.8. Tạo API phục vụ chatbot

- **File chính**: [graph_rag_enterprise_2/api/app.py](graph_rag_enterprise_2/api/app.py#L1)
- **Việc đã làm**:
	- Thiết kế endpoint để frontend hoặc client gửi câu hỏi vào hệ thống.
	- Trả về response có answer, nguồn tham chiếu và metadata xử lý.
- **Kết quả**:
	- Chatbot có giao diện gọi API rõ ràng để tích hợp với ứng dụng bên ngoài.

### 1.9. Bổ sung logging, metrics và tracing

- **File chính**: [graph_rag_enterprise_2/infra/metrics.py](graph_rag_enterprise_2/infra/metrics.py#L1), [graph_rag_enterprise_2/infra/tracing.py](graph_rag_enterprise_2/infra/tracing.py#L1)
- **Việc đã làm**:
	- Gắn log, theo dõi latency, số lượng context, thời gian gọi LLM.
	- Thêm tracing để theo dõi một request từ đầu đến cuối.
- **Kết quả**:
	- Có thể quan sát chất lượng vận hành và debug khi chatbot phản hồi chậm hoặc sai.

---

## 2. Luồng xử lý của chatbot

Phần này mô tả đúng theo pipeline đang chạy trong `graph_rag_enterprise_2`. Mỗi bước đều ghi rõ file nào chịu trách nhiệm, file đó làm gì và kết quả mong đợi là gì.

### Bước 1: Nhận câu hỏi từ người dùng

- **File**: [graph_rag_enterprise_2/api/app.py](graph_rag_enterprise_2/api/app.py#L1)
- **Làm gì**:
- Nhận request từ client qua API.
- Chuẩn hóa payload đầu vào như `query`, `session_id`, `user_id` nếu có.
- Chuyển request vào pipeline xử lý.
- **Kết quả**:
- Hệ thống nhận được truy vấn hợp lệ và tạo được một request nội bộ để xử lý tiếp.

### Bước 2: Điều phối toàn bộ pipeline

- **File**: [graph_rag_enterprise_2/pipeline/orchestrator_v3.py](graph_rag_enterprise_2/pipeline/orchestrator_v3.py#L1)
- **Làm gì**:
- Khởi tạo các thành phần lõi: `HybridRetriever`, `QueryPlanner`, `CypherBuilder`, `CypherValidator`, `Neo4jClient`, `ResultReasoner`, `AnswerGenerator`, `ContextManager`.
- Nhận query từ `app.py` và bắt đầu pipeline `run(query)`.
- Điều phối thứ tự xử lý: truy hồi dữ liệu, xử lý ngữ cảnh, lập kế hoạch, sinh Cypher, kiểm tra, truy vấn Neo4j, hậu xử lý và trả câu trả lời.
- **Kết quả**:
- Một request được dẫn qua pipeline theo đúng logic của hệ thống.

### Bước 3: Truy hồi dữ liệu ban đầu

- **File**: [graph_rag_enterprise_2/retriever/hybrid_retriever.py](graph_rag_enterprise_2/retriever/hybrid_retriever.py#L1)
- **Làm gì**:
- Dùng hybrid search để lấy các tín hiệu liên quan từ vector và graph.
- Trả về dữ liệu đã map để `QueryPlanner` sử dụng.
- **Kết quả**:
- Có danh sách mapped data và semantic signal cho các bước kế tiếp.

### Bước 4: Xử lý ngữ cảnh hội thoại cũ

- **File**: [graph_rag_enterprise_2/pipeline/orchestrator_v3.py](graph_rag_enterprise_2/pipeline/orchestrator_v3.py#L1), [graph_rag_enterprise_2/core/context_manager.py](graph_rag_enterprise_2/core/context_manager.py#L1)
- **Làm gì**:
- Chuẩn hóa câu hỏi về dạng đơn giản để phát hiện follow-up.
- Nếu người dùng hỏi tiếp kiểu “mẫu này”, “cái này”, “so sánh hai lốp vừa rồi” thì lấy size từ context trước.
- Bổ sung size cũ vào mapped data nếu cần để tránh mất ngữ cảnh.
- **Kết quả**:
- Query được hiểu đúng trong ngữ cảnh hội thoại nhiều lượt.

### Bước 5: Lập kế hoạch xử lý

- **File**: [graph_rag_enterprise_2/planner/query_planner.py](graph_rag_enterprise_2/planner/query_planner.py#L1)
- **Làm gì**:
- Trước hết dùng rule-based plan để phân loại các tín hiệu mạnh như giá, tốc độ, tải, so sánh, multi-hop.
- Nếu rule-based chưa ra quyết định và model ML khả dụng, gọi `IntentClassifier.predict(query)` làm fallback.
- Nếu confidence của ML đủ cao, chuyển intent sang plan tương ứng.
- **Kết quả**:
- Hệ thống xác định được nên đi theo plan nào: `SINGLE`, `PRICE`, `SPEED`, `COMPARE`, `MULTI_HOP`, `NO_MATCH`, ...

### Bước 6: Sinh Cypher

- **File**: [graph_rag_enterprise_2/cypher/cypher_builder.py](graph_rag_enterprise_2/cypher/cypher_builder.py#L1)
- **Làm gì**:
- Chuyển plan thành câu lệnh Cypher và params tương ứng.
- Chọn nhánh query phù hợp theo loại câu hỏi và size đã map.
- **Kết quả**:
- Có truy vấn graph cụ thể để gửi sang Neo4j.

### Bước 7: Kiểm tra tính hợp lệ của Cypher

- **File**: [graph_rag_enterprise_2/validation/cypher_validator.py](graph_rag_enterprise_2/validation/cypher_validator.py#L1)
- **Làm gì**:
- Kiểm tra Cypher và params trước khi chạy thật.
- Nếu Cypher lỗi, hệ thống fallback sang `CypherGenerator` để sinh lại.
- **Kết quả**:
- Tránh đưa query lỗi vào Neo4j.

### Bước 8: Thực thi truy vấn Neo4j

- **File**: [graph_rag_enterprise_2/db/neo4j_client.py](graph_rag_enterprise_2/db/neo4j_client.py#L1)
- **Làm gì**:
- Kết nối Neo4j và chạy Cypher.
- Nhận kết quả truy vấn dạng rows hoặc records.
- **Kết quả**:
- Hệ thống có dữ liệu thực từ graph để xử lý tiếp.

### Bước 9: Chuẩn hóa dữ liệu kết quả

- **File**: [graph_rag_enterprise_2/utils/normalizer.py](graph_rag_enterprise_2/utils/normalizer.py#L1)
- **Làm gì**:
- Chuẩn hóa các key kết quả như `max_speed`, `max_load`, `price`, `speed`, `load` để đầu ra thống nhất.
- Loại bỏ khác biệt tên cột giữa các nguồn dữ liệu.
- **Kết quả**:
- Dữ liệu đầu ra nhất quán để `ResultReasoner` và `AnswerGenerator` xử lý ổn định hơn.

### Bước 10: Rút ra câu trả lời theo rule hoặc reasoner

- **File**: [graph_rag_enterprise_2/reasoner/result_reasoner.py](graph_rag_enterprise_2/reasoner/result_reasoner.py#L1)
- **Làm gì**:
- Diễn giải dữ liệu theo từng loại plan như `PRICE`, `SPEED`, `COMPARE`, `MAX_LOAD`, ...
- Nếu câu hỏi đơn giản thì có thể trả lời trực tiếp theo rule.
- **Kết quả**:
- Có nội dung đã được suy luận, gần với câu trả lời cuối.

### Bước 11: Sinh câu trả lời cuối

- **File**: [graph_rag_enterprise_2/llm/prompt_answer.py](graph_rag_enterprise_2/llm/prompt_answer.py#L1), [graph_rag_enterprise_2/llm/llm_client.py](graph_rag_enterprise_2/llm/llm_client.py#L1), [graph_rag_enterprise_2/llm/answer_generator.py](graph_rag_enterprise_2/llm/answer_generator.py#L1)
- **Làm gì**:
- Gộp câu hỏi người dùng với context đã truy hồi và dữ liệu đã reason.
- Tạo prompt đúng format.
- Gọi model ngôn ngữ để sinh câu trả lời cuối cùng.
- **Kết quả**:
- Trả về câu trả lời có nội dung phù hợp, rõ ràng và bám vào dữ liệu từ graph.

### Bước 12: Ghi log, metrics, tracing và trả response

- **File**: [graph_rag_enterprise_2/infra/metrics.py](graph_rag_enterprise_2/infra/metrics.py#L1), [graph_rag_enterprise_2/infra/tracing.py](graph_rag_enterprise_2/infra/tracing.py#L1), [graph_rag_enterprise_2/api/app.py](graph_rag_enterprise_2/api/app.py#L1)
- **Làm gì**:
- Ghi lại thời gian xử lý, số lượng context, lỗi nếu có.
- Theo dõi request theo trace id.
- Đóng gói kết quả cuối cùng thành JSON response và trả về client.
- **Kết quả**:
- Có dữ liệu để giám sát và response cuối cùng sẵn sàng hiển thị cho người dùng.

### Tóm tắt luồng đúng

`app.py` nhận request → `orchestrator_v3.py` điều phối → `HybridRetriever` lấy tín hiệu ban đầu → `QueryPlanner` quyết định plan, có thể gọi `IntentClassifier.predict(...)` làm fallback → `CypherBuilder` sinh Cypher → `CypherValidator` kiểm tra → `Neo4jClient` chạy query → `ResultReasoner` diễn giải → `AnswerGenerator` sinh câu trả lời → `app.py` trả response.

---

## 3. Kết luận

Hệ thống trong `graph_rag_enterprise_2` đã được tổ chức thành một pipeline Graph-RAG khá đầy đủ: từ nạp dữ liệu, truy vấn graph, truy hồi vector, phân loại intent, sinh Cypher, gọi LLM, đến hậu xử lý và giám sát.

Điểm quan trọng nhất là báo cáo này đã được viết lại đúng theo project `graph_rag_enterprise_2`, không còn nhầm sang `graph_rag_enterprise` nữa.

---

## 4. Kiểm thử thực tế với dữ liệu Neo4j

Mình đã chạy lại bộ kiểm thử trong [graph_rag_enterprise_2/tests/run_chat_tests.py](graph_rag_enterprise_2/tests/run_chat_tests.py) với `.env` thật và ghi kết quả vào [graph_rag_enterprise_2/tests/chat_test_results.md](graph_rag_enterprise_2/tests/chat_test_results.md). Bộ câu hỏi test cũng đã được chỉnh lại để bám sát workbook `Data_mp_final.xlsx`, ưu tiên đúng 5 sheet dữ liệu thực tế mà bạn nêu: `LOP_XD_DRC`, `LOP_XM_DRC`, `LOP_XM_DPLUS`, `tire_variant`, và `variant_quality_standard`. Một số quan sát đáng tin cậy là:

- **Tra cứu theo size**: câu hỏi về `120/70-17` trả về được `DPLUS`, `max_load = 236 kg`, `max_speed = 150 km/h`.
- **Hỏi tải nặng**: câu hỏi `Nếu tôi cần lốp chịu tải >400 kg` trả về danh sách ứng viên thực tế trong DB, nổi bật nhất là `140/70-14` và `130/70-17` với tải trọng `265 kg`.
- **Hỏi giá / giảm giá**: một số câu vẫn chưa có giá đầy đủ trong dữ liệu hiện tại, nên hệ thống trả lời thẳng là chưa đủ dữ liệu thay vì bịa thông tin.
- **Hỏi theo ngữ cảnh**: các câu follow-up như “Lốp này...” vẫn có thể được nối ngữ cảnh size từ lượt trước.

Điểm cần nói rõ khi báo cáo: sau khi tắt chế độ mock của LLM và chạy lại với `.env` thật, file [graph_rag_enterprise_2/tests/chat_test_results.md](graph_rag_enterprise_2/tests/chat_test_results.md) đã ghi nhận câu trả lời thật từ pipeline. Một số câu vẫn trả về thông báo thiếu dữ liệu nếu bản ghi trong graph chưa đủ thuộc tính, nhưng không còn bị `MOCK_RESPONSE` do mock LLM nữa.

### Chuỗi xử lý của một truy vấn thật

1) `app.py` nhận request và chuyển vào `GraphRAGv3.run(query)`.
2) `HybridRetriever` nhận diện size / thuộc tính liên quan.
3) `QueryPlanner` chọn plan phù hợp như `PRICE`, `LOAD`, `MAX_LOAD`, `ATTRIBUTE_SEARCH`.
4) `CypherBuilder` sinh Cypher, `CypherValidator` kiểm tra, `Neo4jClient` truy vấn DB.
5) `ResultReasoner` và `AnswerGenerator` diễn giải dữ liệu rồi trả response cho client.

Nói ngắn gọn: test thực tế đã chứng minh pipeline chạy được từ đầu đến cuối bằng dữ liệu thật, nhưng chất lượng trả lời còn phụ thuộc mức độ đầy đủ của dữ liệu trong Neo4j.

## 5. Đoạn trình bày miệng về luồng xử lý

Khi người dùng gửi câu hỏi, bước đầu tiên là `app.py` nhận request và chuyển câu hỏi vào `orchestrator_v3.py`. Tại đây, hệ thống không trả lời ngay mà đi theo từng bước rõ ràng: trước hết `HybridRetriever` lấy các tín hiệu liên quan từ dữ liệu đã nạp, chẳng hạn như `size`, `giá`, `tốc độ` hoặc `tải`; sau đó `ContextManager` kiểm tra xem đây có phải là câu hỏi nối tiếp hay không để bổ sung lại ngữ cảnh cũ nếu cần. Tiếp theo, `QueryPlanner` phân tích câu hỏi và ưu tiên luật viết tay trước, tức là nếu câu hỏi đã đủ rõ thì nó sẽ quyết định luôn plan như `PRICE`, `SPEED`, `COMPARE`, `MULTI_HOP` hoặc `SINGLE`. Chỉ khi rule-based chưa xác định được plan phù hợp, hệ thống mới gọi `IntentClassifier.predict(...)` để đoán intent bằng mô hình ML, và chỉ dùng kết quả này nếu độ tin cậy đủ cao (>0.7). Khi đã có plan cuối cùng, `CypherBuilder` sinh câu lệnh Cypher, `CypherValidator` kiểm tra câu lệnh có hợp lệ, có đúng schema và có tham số đầy đủ hay không, rồi `Neo4jClient` chạy truy vấn để lấy dữ liệu thật từ graph. Dữ liệu trả về tiếp tục được chuẩn hóa, `ResultReasoner` diễn giải theo đúng loại câu hỏi, và `AnswerGenerator` tạo câu trả lời cuối cùng để trả lại cho người dùng. Cuối cùng, `app.py` gửi response về client, đồng thời metrics và tracing được ghi lại để theo dõi hiệu năng. Nói ngắn gọn, luồng xử lý của chatbot đi theo đúng chuỗi: nhận câu hỏi, lấy tín hiệu, hiểu ngữ cảnh, chọn plan, sinh và kiểm tra Cypher, truy vấn Neo4j, suy luận, rồi mới sinh câu trả lời.

