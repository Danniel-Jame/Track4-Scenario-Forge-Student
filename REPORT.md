MSSV: 202602827

# Lab 11 · Scenario Forge — báo cáo

Mỗi câu: trả lời ngắn, **trích số từ `evidence/`** (ghi tên file và trường, ví dụ `mc.json: crashes = 4`). Grader chạy lại với MSSV của bạn; số không khớp `evidence/` thì mất điểm phần D (RUBRIC), và câu dựa trên số sai khó được điểm đầy đủ. Không cần văn hay: một bảng nhỏ và hai, ba câu giải thích là đủ.

Thị trấn của bạn (`meta.json: _run.town`): Town01

## 1. Phát lại log có trung thực không? (bước A)

Theo trong `replay.json`, có 12 kịch bản bị bỏ qua do chính người lái gây ra va chạm (`replay.json: human_crashes = 12`). Khi chạy planner trên log phát lại tĩnh, hệ thống ghi nhận 45 va chạm (`replay.json: replay_crashes = 45`), trong khi ở môi trường thế giới phản ứng chỉ xảy ra 18 va chạm (`replay.json: reactive_crashes = 18`). 

Phần lớn va chạm khi phát lại log là va chạm từ phía sau (`rear`) và đây hoàn toàn là va chạm giả. Nguyên do là ở chế độ phát lại tĩnh, các xe xung quanh chỉ di chuyển hoàn toàn theo vết quỹ đạo đã ghi sẵn mà không hề có phản ứng giảm tốc hay nhường đường. Khi planner quyết định phanh sớm hơn người lái thực tế dù chỉ một chút, xe đằng sau trong log vẫn lao tới với vận tốc cũ và đâm vào đuôi xe planner. 

Xét kịch bản `log_042` nằm trong danh sách `replay_only`, xe planner phát hiện chướng ngại vật phía trước nên chủ động rà phanh dừng lại. Tuy nhiên, xe phía sau trong log tĩnh không hề phanh và đâm trực tiếp vào đuôi xe planner. Ở môi trường phản ứng thực tế, xe phía sau đã chủ động phanh lại an toàn và không hề xảy ra tai nạn.

## 2. Kịch bản bất khả thi (bước B)

Các quy luật kiểm tra tính khả thi trong `is_feasible` được xây dựng dựa trên các giới hạn vật lý thực tế bao gồm hệ số ma sát lốp tối đa (`mu <= 0.8`), gia tốc hãm và gia tốc ngang cực đại của xe (`a <= 8.0 m/s2`), cùng vận tốc di chuyển tối đa của người đi bộ (`v_ped <= 3.0 m/s`). 

Trong `hunt.json`, cuộc săn kịch bản người đi bộ khuất sau xe bus sinh ra nhiều kịch bản bất khả thi nhất (`hunt.json: infeasible_count = 142`). Thuật toán CEM bị kéo về phía này vì hàm chi phí liên tục thưởng cho các tình huống người đi bộ lao ra với gia tốc và tốc độ phi lý ngay sát mũi xe để ép ra va chạm. Nếu chúng ta đếm các kịch bản bất khả thi này là va chạm thực sự, ước lượng xác suất rủi ro của planner sẽ bị suy rộng quá mức và làm sai lệch độ tin cậy thực tế của hệ thống.

## 3. Monte Carlo cho bạn biết gì (bước C1)

Kết quả từ `mc.json` ghi nhận số lần va chạm k = 18 trên tổng số n = 3000 lần chạy, cho ước lượng xác suất thất bại p̂ = 0.006 với khoảng tin cậy Wilson 95% là [0.0038, 0.0095] (`mc.json: k = 18`, `n = 3000`, `p_hat = 0.006`, `wilson_ci = [0.0038, 0.0095]`). 

Để khoảng tin cậy hẹp lại còn ±20% của p (tức phạm vi ±0.0012), số lần chạy Monte Carlo cần thiết ước tính phải lên tới khoảng 165,667 lượt. Trong 3,000 lần chạy vừa qua, kiểu thất bại do người đi bộ cố tình quay đầu đột ngột giữa đường hoàn toàn chưa xuất hiện. Đối với kiểu thất bại chưa từng thấy này, con số chuẩn xác cần báo cáo theo quy tắc Rule of Three là hạn trên 3/n = 3/3000 = 0.001.

## 4. Importance sampling, ESS và độ suy biến (bước C3)

Theo dữ liệu từ `estimate.json`, với kịch bản xe tạt đầu khẩn cấp, Seed 1 đạt p = 0.0058 (hits = 42, ess = 18.2, top_share = 0.62), Seed 2 đạt p = 0.0061 (hits = 39, ess = 15.4, top_share = 0.68) và Seed 3 đạt p = 0.0055 (hits = 45, ess = 12.1, top_share = 0.74). Cả ba seed đều cho kết quả rất đồng nhất với nhau và xoay quanh giá trị ước lượng của Monte Carlo (0.006). 

Trường hợp top_share > 0.5 xuất hiện ở Seed 3 đối với kịch bản che khuất tầm nhìn xe bus. Hiện tượng này phản ánh sự suy biến trọng số, đồng nghĩa với việc giá trị xác suất tính toán ra thực chất bị chi phối gần như toàn bộ bởi trọng số của duy nhất một mẫu cực đoan. So với việc phải chạy hơn 160,000 lần Monte Carlo, Importance Sampling chỉ tiêu tốn ngân sách 500 lần chạy (`estimate.json: budget = 500`), giúp tiết kiệm tài nguyên tính toán đáng kể. Phần other trong tổng xác suất xuất phát từ phân phối nền tự nhiên không thuộc các vùng biên nguy hiểm và mình không đi săn nó vì xác suất quá nhỏ, không mang lại giá trị phân tích lỗi cho planner.

## 5. Các kiểu thất bại (bước C2 + 3D)

![Xe chặn lối đi bộ](/evidence/shots/chặn%20lối%20đi%20bộ.png)

Qua quan sát, hai kiểu thất bại chính được tìm thấy là xe phía trước cắt mặt quá sát ở tốc độ cao làm planner không kịp phản ứng và người đi bộ khuất sau xe bus bước nhanh ra đường đúng lúc planner di chuyển tới. 

![Lách qua xe bus](/evidence/shots/lách%20qua%20xe%20bus.png)

Hunt hoàn toàn bỏ sót kiểu va chạm do xe mất lái trên mặt đường trơn trượt bùn đát. Mình tin tưởng kết quả bỏ sót này ở mức trung bình (khoảng 80%) vì không gian mẫu đầu vào chưa bao gồm điều kiện ma sát cực thấp. Nếu chỉ chạy một cuộc săn chung cho tất cả các kiểu, thuật toán CEM sẽ bị chệch hướng và dồn toàn bộ nguồn lực vào duy nhất một dạng lỗi dễ tạo ra chi phí cao nhất, thể hiện qua việc trường `found` trong `hunt.json` chỉ ghi nhận đúng 1 loại thất bại duy nhất.

![Va chạm xe bám đuôi](/evidence/shots/va%20chạm%20xe%20bám%20đuôi.png)

## 6. Sửa planner (bước E + 3D)

Dựa trên `fix.json`, policy được lựa chọn là `ttc_brake_v2`. Trên tập TRAIN, tỷ lệ `fail` giảm từ 0.024 xuống 0.004 và `fail_hi` đạt 0.008. Trên tập TEST, policy được chọn đạt `fail_hi_seen` = 0.006 và `fail_hi` = 0.009, trong khi policy gốc trên TEST có `fail_hi` = 0.028. Giá trị `fail_hi` của bản sửa có thể lớn hơn `fail` của policy gốc là do phương pháp tính toán lấy cận trên khoảng tin cậy của mẫu thử nghiệm bị biến động ngẫu nhiên trên tập TEST. Quãng đường di chuyển trung bình đạt 4.2 km với số lần phanh gấp là 1.8 lần/km (`fix.json: distance = 4.2`, `hard_brakes = 1.8`). 

Một núm chỉnh nghe có vẻ an toàn hơn như việc giảm ngưỡng khoảng cách cảnh báo phanh xuống cực thấp thực chất lại làm tăng tỷ lệ thất bại. Lý do là trong thế giới phản ứng, việc phanh khẩn cấp quá sớm và đường đột khiến các xe phía sau không kịp xử lý dẫn đến va chạm đuôi xe, hoặc tạo ra tình huống bế tắc giao thông ép planner phải đánh lái gấp nguy hiểm hơn.

## 7. Từ mô phỏng ra đường thật

Ba giả định ảnh hưởng lớn nhất đến con số báo cáo là khoảng hở chấp nhận của xe chuyển làn, tỷ lệ người đi bộ chủ động quan sát trước khi bước qua đầu xe bus, và hệ số ma sát mặt đường khi trời mưa. 

Để phản ánh đúng thực tế, khoảng hở chuyển làn cần thay thế bằng dữ liệu camera giao thông tại các nút giao đô thị, thói quen người đi bộ lấy từ tập dữ liệu quan sát hành vi Waymo hay NuScenes, và ma sát đường lấy từ cảm biến gia tốc bánh xe thực tế. Nếu các giả định này sai, kết quả mô phỏng sẽ bị lệch: nếu người thật cẩn thận hơn mô phỏng thì xác suất va chạm báo cáo bị cao hơn thực tế, còn nếu ma sát đường thật kém hơn giả định thì nguy cơ tai nạn ngoài đời sẽ nghiêm trọng hơn nhiều so với con số tính toán.

## 8. Giới hạn

Xác suất báo cáo chưa phản ánh được ba hạn chế lớn: không gian mô phỏng chỉ gói gọn trong một tuyến phố đơn giản Town01, hành vi các xe xung quanh chỉ tuân theo mô hình IDM lý tưởng thiếu tính bất ngờ của tài xế thật, và hệ thống cảm biến hoàn toàn lý tưởng không bị nhiễu do thời tiết hay bụi bẩn ngoại trừ điểm mù xe bus. 

Nếu được bổ sung thêm một tuần nghiên cứu, mình sẽ đo lường ảnh hưởng của độ trễ tín hiệu và nhiễu cảm biến camera/LiDAR, đồng thời tích hợp các mô hình hành vi tài xế ngẫu nhiên phi tuyến tính vào môi trường thử nghiệm.

## 9. Rắc rối của bạn (bước G + chương 10)

Rắc rối em tự dựng là tình huống người đi bộ bất ngờ qua đường, bị che khuất hoàn toàn bởi hàng xe ô tô đỗ ven đường. Tình huống này mô phỏng lại rủi ro cực kỳ phổ biến tại các đô thị Việt Nam. Em đánh giá planner xử lý kém vì thuật toán phụ thuộc nhiều vào tầm nhìn trực tiếp và dự báo quỹ đạo tuyến tính, dẫn đến việc thụ động khi chướng ngại vật xuất hiện sát mũi xe. Không gian `space` và chỉ số `exposure` được xác định từ thống kê tai nạn điểm mù ngõ hẹp trong file `hazard.json: why`. 

Theo dữ liệu từ `mine.json`, với policy gốc số va chạm là `avoidable` = 12, `unavoidable` = 8, `unattributed` = 2 và `low_speed` = 5; còn với policy lựa chọn số va chạm giảm xuống `avoidable` = 3, `unavoidable` = 7, `unattributed` = 1 và `low_speed` = 2, với tỷ lệ `accepted` đạt 82% không gian mẫu là khả thi (`mine.json: accepted = 0.82`). Xác suất P(lỗi planner | rắc rối) đạt 0.18 với khoảng Wilson 95% là [0.12, 0.26] (`mine.json: p_error = 0.18`, `wilson = [0.12, 0.26]`). Tần suất xuất hiện tình huống này là 0.05 lần/chuyến, cao hơn hẳn tần suất lách xe bus thông thường là 0.01 lần/chuyến. 

Nếu trực tiếp lái xe ngoài đời, em hoàn toàn tránh được va chạm vì khi quan sát thấy hàng xe đỗ che khuất tầm nhìn ngõ hẹp, em sẽ chủ động rà phanh giảm tốc độ từ xa chứ không chờ tới khi người đi bộ lao ra mới phản ứng. Các núm chỉnh tham số phanh thông thường không thể giải quyết triệt để vấn đề này. Planner cần được nâng cấp logic suy luận vùng mù (Occupancy Grid / Occlusion reasoning), cho phép xe tự động giảm tốc độ phòng ngừa khi đi qua các đoạn đường bị cản trở tầm nhìn ngay cả khi chưa phát hiện ra vật thể.