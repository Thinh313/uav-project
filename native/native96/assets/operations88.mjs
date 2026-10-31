export function headingText88(v){return Number.isFinite(v)?String(Math.round((v%360+360)%360)%360).padStart(3,'0')+'°':'—';}
export function outcome88(code=''){
 if(/WAIT_FOR_FRESH_GROUND|GROUND_REVIEW_ACK/.test(code))return{title:'Chờ xác nhận hạ cánh an toàn',detail:'Giữ kênh giám sát. Chỉ xác nhận khi quan sát mới chứng minh đã hạ cánh và disarm; không đóng phiên đang bay.',action:'Xem giám sát'};
 if(/POST_ARM_HOME|Home.*arm/i.test(code))return{title:'Cần xác nhận lại Home',detail:'Xác nhận Home sau arm đã hết hạn hoặc thay đổi. Không gửi AUTO từ phiên duyệt cũ; kết thúc phiên an toàn rồi kiểm lại.',action:'Kiểm trạng thái phiên'};
 if(/UNKNOWN|COMMIT|DEADLINE|timeout|Socket|BRIDGE_UNAVAILABLE/i.test(code))return{title:'Chưa xác nhận kết quả thao tác',detail:'Không bấm gửi lại. Đọc trạng thái và hồ sơ để xác định lệnh đã được thực hiện hay chưa.',action:'Đọc trạng thái'};
 if(/REVOKED|BACKGROUND|TRANSPORT|LEASE|FRESH|STALE|MẤT PHIÊN/i.test(code))return{title:'Phiên điều khiển mất hiệu lực',detail:'Quyền đã thu hồi. Theo dõi phản ứng của autopilot ở bảng giám sát; chỉ mở phiên mới sau khi xác nhận an toàn.',action:'Mở giám sát sự cố'};
 if(/QUOTA|reserve|dung lượng/i.test(code))return{title:'Chưa đủ dung lượng lưu hồ sơ',detail:'Giữ toàn bộ dữ liệu. Xuất và kiểm nhập lại trước khi chọn chuyển workspace; không tự dọn.',action:'Mở workspace'};
 return{title:'Thao tác chưa được xác nhận',detail:'Kiểm tra điều kiện và trạng thái hiện tại trước khi tiếp tục. Mã kỹ thuật được giữ trong hồ sơ.',action:'Kiểm trạng thái phiên'};
}
