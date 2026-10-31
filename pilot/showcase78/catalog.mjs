import {CAPABILITIES} from '../aeris57/catalog.mjs';
const item=(id,title,scope,description,limitations,reports)=>({id,title,scope,description,limitations,reports:reports.map(x=>'delivery/COMPLETION-'+x+'.md')});
export const CATALOG=[...CAPABILITIES,
 item('research-partner','Phase One và cockpit nhiều payload','MOCK_REPLAY','Contract CYBER65 và cockpit66: chọn payload, routing, capability và quyền thao tác.','Phase One thật, gimbal thực, Android/HeraHub và ảnh thực chưa nghiệm thu.',['CYBER65','COCKPIT66']),
 item('dual','Hai operator và journal bền vững','MOCK_REPLAY','Hai phiên độc lập, bàn giao/tranh chấp/mất kết nối và lịch sử fsync. Restart không tự phục hồi quyền.','Phạm vi host/mock; hai trạm/radio thật và production authentication chưa kiểm.',['DUAL67','JOURNAL68']),
 item('custody','Rotation, archive và receiver độc lập','MOCK_REPLAY','Thế hệ đóng, xuất/nhập, quota có kiểm soát, receipt và restart trong workspace riêng.','Loopback/mock; chưa là dịch vụ receiver thương mại. Không tự dọn bằng chứng.',['ARCHIVE69','ROTATE70','HANDOFF71','RECEIVER72']),
 item('identity','Danh tính, chống replay và vòng đời khóa','MOCK_REPLAY','Contract source/receiver, nonce/epoch/TTL, rotation và revocation.','Chưa PKI hay xác thực mật mã production; không sinh khóa thật hoặc ký mới.',['AUTH73','KEY74']),
 item('sim-feedback','Feedback mô phỏng và lỗi mất cảm biến','SITL_AND_REPLAY','Corpus pitch+yaw, proximity và đối chứng ArduPilot internal quad; 4/4 lượt đủ điều kiện xác nhận lỗi mất cảm biến khi vẫn giữ cần tiến.','Lỗi an toàn còn mở. Chưa hiệu chuẩn Hera, collision response, tải treo, khí động học mưa hoặc motor failure; 15 nhóm dữ liệu Hera còn thiếu.',['SIMFEEDBACK75','SIMSITL76','SIMDROP77-VERIFIED']),
 item('showcase','Màn trình diễn và E2E hiện tại','LIVE_SITL','Flight Studio, input trực quan, kịch bản 12s, preflight → GUIDED/LOITER → LAND/disarm → review raw.','Demo engineering; âm tổng hợp, tay cần ảo, pacing 1× ổn định và sản phẩm Hera chưa nghiệm thu.',['SHOWCASE78'])
];
export const EXTRA_REPORTS=new Set(CATALOG.slice(CAPABILITIES.length).flatMap(c=>c.reports));
