"""Create successor progress/report and a digest-bound M1-MOCK handoff, once."""
import hashlib
import html
import json
import os
from pathlib import Path
import re
import sys
import time
from datetime import datetime, timezone

R = Path(__file__).resolve().parents[3]
os.chdir(R)
E = Path('evidence/betaintegrated01-m1mock')


def digest(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def write(p, data):
    with Path(p).open('x') as f:
        f.write(data)


def jwrite(p, data):
    write(p, json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def main():
    qa = json.loads((E / 'qa/FINAL-QA01.json').read_text())
    pre = json.loads((E / 'preservation-final01.json').read_text())
    entry = json.loads((E / 'entry01.json').read_text())
    assert pre['status'] == 'PASS_PRESERVED_AT_FINAL_OBSERVATION'
    assert qa['status'] == 'PASS_SCOPED_M1_MOCK_FOUNDATION'
    assert all(digest(p) == h for p, h in qa['sourceSHA256'].items())
    assert time.time() - entry['startEpoch'] < entry['wallBudgetSeconds']
    assert os.statvfs('.').f_bavail * os.statvfs('.').f_frsize > 10 * 2**30 + 256 * 2**20
    now = datetime.now(timezone.utc).isoformat()
    evidence = {
        'A01': ['qa/journal-followup02/results.json', 'journal/tests01/report.json'],
        'A02': ['qa/journal-followup02/results.json', 'qa/FINAL-QA01.json'],
        'A03': ['journal/tests01/report.json', 'qa/journal-followup02/results.json'],
        'A04': ['journal/tests01/report.json', 'journal/final-cold06.json'],
        'A05': ['qa/clock-qa04/results.json'],
        'A06': ['qa/clock-qa04/results.json', 'root-clock-read-time01.json'],
        'A07': ['qa/lifecycle02/results.json'],
        'A08': ['qa/lifecycle02/results.json'],
        'A09': ['admission01.json', 'journal/tests01/report.json'],
        'A10': ['qa/journal-followup02/results.json', 'qa/final-cold-replay01.json'],
        'A11': ['preservation-final01.json', 'qa/FINAL-QA01.json', 'clock_lifecycle/builder-verification.json'],
    }
    ac = json.loads(Path('planning/betaintegrated01/m1mock/AC-CONTRACT.json').read_text())
    rows = []
    for item in ac['criteria']:
        paths = evidence[item['id']]
        rows.append({'id': item['id'], 'title': item['title'], 'status': 'PASS_SCOPED_MOCK',
                     'evidence': [{'path': str(E / p), 'sha256': digest(E / p)} for p in paths]})
    verification = {
        'format': 'aeris-contractor-m1mock-verification', 'atUTC': now,
        'status': 'M1_MOCK_FOUNDATION_READY', 'criteria': rows,
        'actualM1Ready': False, 'BETA_SIMReady': False, 'scope': 'Pure Python and Java foundation; unwired',
        'sourcePins': qa['sourceSHA256'], 'contractSHA256': digest('planning/betaintegrated01/m1mock/AC-CONTRACT.json'),
        'independentQAReceiptSHA256': digest(E / 'qa/FINAL-QA01.json'),
        'preservationReceiptSHA256': digest(E / 'preservation-final01.json'),
        'qualificationLimits': [
            'Some broad initial builder fixtures predate final source. Final current-source QA and targeted repairs are separately pinned; no sum of overlapping test counts.',
            'Cold complete bytes are uncommitted without an external caller-owned successful-close anchor; publicationAllowed remains false.',
            'Descriptor observations and lifecycle resource-closed inputs are trusted wrapper inputs, not live attestation or LAND evidence.',
            'No AP-stage recorder integration, native socket wiring, Android UI/SAF/media/input, 30min pacing or hardware acceptance.',
            'No physical power-loss guarantee, source authentication or flight execution inferred from fsync/send.',
            'No human/visual QA performed in this component-only task.',
        ],
        'runtime': {'AP': 0, 'Android': 0, 'hostCompanion': 0, 'APKAPNativeArtifactBuild': 0, 'install': 0, 'sign': 0,
                    'purePythonFaultChildren': True, 'pureJDKUnitCompilationAndExecution': True},
        'cleanup': ['native/betaintegrated01/.build/clock-lifecycle-unit (16 class files)',
                    'native/betaintegrated01/.build/independent-qa01',
                    'native/betaintegrated01/.build/independent-edge01',
                    'native/betaintegrated01/.build/independent-qa02'],
        'remainingOwnedBuildFiles': [], 'elapsedSeconds': time.time() - entry['startEpoch'],
    }
    jwrite(E / 'verification-final01.json', verification)
    jwrite('planning/betaintegrated01/PROGRESS-M1-MOCK.json', {
        'atUTC': now, 'supersedesStatusOnly': 'planning/betaintegrated01/PROGRESS.json',
        'M0': 'COMPLETE_SOURCE_HANDOFF', 'M1Mock': 'FOUNDATION_READY', 'M1Actual': 'NOT_READY', 'BETA_SIM': 'NOT_READY',
        'verification': str(E / 'verification-final01.json'),
        'next': 'M1-BUILD/ACTUAL: selected provider/runtime closure, AP-stage/native-journal adapters, cadence/freshness and short smoke before30min',
        'historicalFilesRewritten': False,
    })
    report = '''# AERIS · M1-MOCK: journal, clock và lifecycle

Ngày 27/10/2026. Kết quả: **M1-MOCK FOUNDATION READY**. Đây là phần nền đã kiểm bằng mock/fault injection; **M1 thực và Beta giả lập hoàn chỉnh vẫn NOT READY**.

## Kết quả có ích cho sản phẩm

- Journal phân đoạn giữ thứ tự RX → INTENT → fsync → callback gửi → SENT/UNKNOWN, ràng buộc run/epoch/frame và chuỗi CRC/SHA. Luân chuyển chỉ ở ranh giới hợp lệ; receiver đọc lạnh phát hiện thiếu, đảo, sửa hoặc thêm dữ liệu sau seal.
- Dữ liệu timing/stage được ghi theo luồng; số bản ghi, kích thước, quota và bộ nhớ tổng hợp có giới hạn. Fault injection kiểm short-write, EIO, ENOSPC, file/directory fsync, send không xác định và tiến trình mock bị dừng đột ngột. Các prefix hợp lệ và hồ sơ lỗi được giữ.
- Clock dùng trạng thái pending/recent có giới hạn, không còn phụ thuộc bảng toàn phiên 1.024 phần tử. Bản kiểm độc lập cuối chạy 2.051 trao đổi và giữ 4.104 dòng sự kiện bền vững; kiểm stale, timeout, phản hồi muộn/trùng, sai peer/run/boot và clock regression.
- Lifecycle tách yêu cầu dừng, đóng tài nguyên và commit review; thời gian đã đóng bất biến. Chặn callback thế hệ cũ, lease hết hạn sống lại, khôi phục quyền từ lịch sử và tạo hai phiên kế tiếp từ cùng phiên đã đóng.
- ProviderDescriptor đối chiếu binary/model/config/endpoint theo profile và từ chối candidate thiếu hash. Đây là kiểm cấu trúc dữ liệu đầu vào, chưa phải xác minh runtime hay cấp quyền bay.

## Các lỗi QA đã sửa

Ca quan trọng nhất: close có thể lỗi ở directory fsync sau khi các byte session đã tồn tại, đồng thời không ghi được failure marker. Reader không thể suy ra commit từ chính các byte đó. Kết quả mặc định hiện là COMPLETE_BYTES_UNATTESTED; chỉ anchor do caller giữ sau close thành công mới đối chiếu được commit. Cả hai trạng thái vẫn không cho công bố gói hay kết luận AP đã thực thi. Anchor lấy lại từ chính gói chưa tin cậy không tạo ra bảo chứng độc lập.

Các ca khác đã sửa và kiểm lại: reader chấp nhận policy/eventKind sai kiểu, đọc lịch sử sau lỗi sink bị chặn, clock/lease hết hạn sống lại khi đồng hồ truy vấn lùi, và successor fork. Cho phép phiên mới dùng cùng AP boot khi AP chưa reboot; không tự tạo bằng chứng reboot. Hồ sơ thất bại ban đầu và lỗi helper kiểm thử được giữ nguyên.

## Kiểm chứng và phạm vi

11 tiêu chí đạt trong phạm vi mock. QA độc lập trên source cuối gồm 10 nhóm journal follow-up, 8 nhóm clock, 13 nhóm Java lifecycle/provider và 13 kiểm cold replay. Các nhóm có chồng lấp, không cộng thành số ca độc nhất. Đối chiếu clock → journal hiện tại đạt 48 CLOCK events qua 3 segment; lượt lớn 1.100 trao đổi dùng journal cũ chỉ là tham chiếu, không thay bằng chứng source cuối.

Không mất/trùng frame được chấp nhận trong corpus mock đã kiểm; chưa có kết luận toàn bộ frame của AP thực. Fsync/callback trong kiểm host không chứng nhận chịu mất điện vật lý hay drone đã nhận lệnh. Chưa có kiểm giao diện Android, ART, cảm giác điều khiển hoặc đánh giá người dùng trong nhiệm vụ này.

## Dung lượng và bảo toàn

Admission mock đạt sau 31 mẫu trong 30 giây; chính sách giữ nguyên: entry 20 GiB, floor 10 GiB cộng dự phòng 256 MiB và forecast 15 giây. Kiểm cuối quan sát khoảng 22,8 GiB trống. Bằng chứng trước báo cáo khoảng 13,3 MiB/800 file, trong ngân sách 256 MiB/2.000 file và cửa sổ 4 giờ.

17.117 định danh cũ, 1.620 mục bàn giao SIM-STABILITY03 và 48 file M0 không có sai lệch mới. 165 đường dẫn thiếu từ baseline cũ và 97 file tracked bị xóa từ trước được giữ nguyên hiện trạng; không tuyên bố codebase đầy đủ hoặc đường dẫn gốc hiện diện liên tục. Không sửa source/candidate đóng băng, canonical SOT hay lịch sử ENDURE; không nghiệm thu lại ENDURE.

Không mở AP, Android, emulator hoặc host companion; không build APK/AP/native library, cài đặt hay ký. Có thực thi Python mock và biên dịch/chạy Java thuần bằng JDK có sẵn. Đã dọn class do tác vụ tạo ở clock-lifecycle-unit (16 class) và ba thư mục independent-qa01, independent-edge01, independent-qa02; .build hiện trống. Không tạo bản sao dự án trong /tmp và không xóa bằng chứng.

## Bước tiếp theo

Chuẩn bị M1-BUILD/ACTUAL: ghép adapter journal của AP-stage và native, materialize/pin closure của provider mới, cấu hình clock sender phù hợp freshness, rồi smoke trước kiểm manual/assisted, mất link/reboot và 30 phút đủ frame ở 1×. Default freshness 250 ms không thể sao chép nguyên cadence observer cũ 333 ms; adapter phải chọn và kiểm cadence phù hợp. Chưa đổi speedup, cap 500 ms hay bỏ frame.

## Hồ sơ kiểm chứng

- [Nghiệm thu Contractor](../evidence/betaintegrated01-m1mock/verification-final01.json)
- [QA độc lập, source cuối](../evidence/betaintegrated01-m1mock/qa/FINAL-QA01.json)
- [Đối chiếu bảo toàn](../evidence/betaintegrated01-m1mock/preservation-final01.json)
- [Tiến độ kế tiếp, không ghi đè M0](../planning/betaintegrated01/PROGRESS-M1-MOCK.json)
- [API journal và giới hạn](../pilot/betaintegrated01/journal/README.md)
- [API clock/lifecycle](../planning/betaintegrated01/m1mock/clock_lifecycle/API.md)
'''
    md = Path('delivery/COMPLETION-BETA-CAMPAIGN01-M1-MOCK.md')
    write(md, report)
    def inline(text):
        text = html.escape(text)
        text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
        return re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    body = []
    for block in report.strip().split('\n\n'):
        if block.startswith('# '):
            body.append('<h1>' + inline(block[2:]) + '</h1>')
        elif block.startswith('## '):
            body.append('<h2>' + inline(block[3:]) + '</h2>')
        elif block.startswith('- '):
            body.append('<ul>' + ''.join('<li>' + inline(s[2:]) + '</li>' for s in block.splitlines()) + '</ul>')
        else:
            body.append('<p>' + inline(block) + '</p>')
    page = '<!doctype html><html lang="vi"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AERIS M1-MOCK</title><style>body{margin:0;background:#f5f5f3;color:#1b1d20;font:16px/1.7 system-ui,sans-serif}main{max-width:1000px;margin:auto;padding:48px 28px 80px}h1{font-size:clamp(26px,4vw,42px);line-height:1.2;letter-spacing:-.035em}h2{font-size:22px;margin-top:36px;border-top:1px solid #ccc;padding-top:24px}p,li{max-width:85ch}li{margin:.65em 0}a{color:inherit;text-underline-offset:3px}strong{font-weight:750}@media print{body{background:white}main{padding:0}}</style><main>' + ''.join(body) + '</main></html>'
    hp = md.with_suffix('.html')
    write(hp, page)
    seal_handoff()


def seal_handoff():
    verification = json.loads((E / 'verification-final01.json').read_text())
    entry = json.loads((E / 'entry01.json').read_text())
    md = Path('delivery/COMPLETION-BETA-CAMPAIGN01-M1-MOCK.md')
    hp = md.with_suffix('.html')
    page = hp.read_text()
    links = re.findall(r'href="([^"]+)"', page)
    checked = []
    for link in links:
        target = hp.parent / link
        assert target.is_file(), str(target)
        checked.append({'link': link, 'sha256': digest(target)})
    inventory = {}
    paths = [md, hp, Path('planning/betaintegrated01/PROGRESS-M1-MOCK.json')]
    for folder in ['pilot/betaintegrated01/journal', 'pilot/betaintegrated01/clock', 'native/betaintegrated01/src',
                   'planning/betaintegrated01/m1mock', str(E)]:
        paths.extend(p for p in Path(folder).rglob('*') if p.is_file())
    for p in sorted(set(paths)):
        if p.is_symlink():
            inventory[str(p)] = {'kind': 'SYMLINK_FIXTURE', 'linkTarget': os.readlink(p)}
        else:
            inventory[str(p)] = {'kind': 'REGULAR_FILE', 'bytes': p.stat().st_size, 'sha256': digest(p)}
    evidence_files = [p for p in E.rglob('*') if p.is_file()]
    assert len(evidence_files) + 1 <= 2000
    assert sum(p.stat().st_size for p in evidence_files) + 2**20 < 256 * 2**20
    seal = {'format': 'aeris-m1mock-handoff-seal', 'atUTC': datetime.now(timezone.utc).isoformat(),
            'status': 'M1_MOCK_FOUNDATION_READY', 'actualM1Ready': False, 'BETA_SIMReady': False,
            'inventory': inventory, 'reportLinksChecked': checked, 'reportVisualQA': 'NOT_PERFORMED_STRUCTURAL_ONLY',
            'evidenceFilesBeforeSeal': len(evidence_files), 'evidenceBytesBeforeSeal': sum(p.stat().st_size for p in evidence_files),
            'freeBytes': os.statvfs('.').f_bavail * os.statvfs('.').f_frsize, 'cleanup': verification['cleanup'],
            'elapsedSeconds': time.time() - entry['startEpoch'], 'noPhysicalPowerLossOrFlightClaim': True}
    jwrite(E / 'handoff-final01.json', seal)
    print(json.dumps({'status': seal['status'], 'sealedFiles': len(inventory), 'reportLinks': len(checked),
                      'evidenceFilesBeforeSeal': len(evidence_files), 'evidenceMiBBeforeSeal': seal['evidenceBytesBeforeSeal']/2**20,
                      'elapsedMinutes': seal['elapsedSeconds']/60, 'freeGiB': seal['freeBytes']/2**30}))


if __name__ == '__main__':
    if sys.argv[1:] == ['--seal-only']:
        seal_handoff()
    else:
        main()
