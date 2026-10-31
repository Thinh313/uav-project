(function (global) {
  'use strict';
  const VIEWS = Object.freeze(['survey', 'preflight', 'fly', 'review']);
  const TYPES = Object.freeze(['LOAD', 'SAVE_DRAFT', 'NAVIGATE', 'STATE', 'REVIEWS']);
  const referenceHome = Object.freeze({ lat: 10.854, lon: 106.807 });
  function finite(value) { return typeof value === 'number' && Number.isFinite(value); }
  function coordinate(pair) { return Array.isArray(pair) && pair.length === 2 && finite(pair[0]) && finite(pair[1]) && Math.abs(pair[0]) <= 90 && Math.abs(pair[1]) <= 180; }
  function parseCoordinates(text) {
    if (typeof text !== 'string' || text.length > 8192) throw new Error('Danh sách tọa độ quá dài.');
    const lines = text.split(/\r?\n/).map(s => s.trim()).filter(Boolean);
    if (lines.length > 64) throw new Error('Tối đa 64 điểm cho một bản khảo sát.');
    return lines.map((line, i) => {
      const parts = line.split(/\s*,\s*|\s+/).filter(Boolean);
      if (parts.length !== 2 || !parts.every(s => /^[-+]?(?:\d+\.?\d*|\.\d+)$/.test(s))) throw new Error('Điểm ' + (i + 1) + ': nhập vĩ độ, kinh độ.');
      const p = parts.map(Number);
      if (!coordinate(p)) throw new Error('Điểm ' + (i + 1) + ': tọa độ ngoài WGS84.');
      return p;
    });
  }
  function validateDraft(input) {
    if (!input || typeof input !== 'object') throw new Error('Chưa có bản khảo sát.');
    const name = typeof input.name === 'string' ? input.name.trim() : '';
    if (!name || name.length > 80 || /[\u0000-\u001f]/.test(name)) throw new Error('Tên khảo sát cần từ 1 đến 80 ký tự.');
    if (!['polygon', 'corridor'].includes(input.kind)) throw new Error('Loại khảo sát không hợp lệ.');
    if (!Number.isSafeInteger(input.revision) || input.revision < 0) throw new Error('Revision chưa xác định. Hãy nạp lại workspace.');
    const geometry = input.geometry;
    if (!Array.isArray(geometry) || geometry.length < (input.kind === 'polygon' ? 3 : 2) || geometry.length > 64 || !geometry.every(coordinate)) throw new Error(input.kind === 'polygon' ? 'Vùng khảo sát cần 3 đến 64 điểm WGS84.' : 'Hành lang cần 2 đến 64 điểm WGS84.');
    const unique = new Set(geometry.map(p => p[0] + ',' + p[1]));
    if (unique.size < (input.kind === 'polygon' ? 3 : 2)) throw new Error('Các điểm khảo sát phải phân biệt.');
    if (!finite(input.altitudeM) || input.altitudeM < 1 || input.altitudeM > 5) throw new Error('Độ cao huấn luyện giới hạn 1 đến 5 m so với Home.');
    if (!finite(input.corridorWidthM) || input.corridorWidthM < 1 || input.corridorWidthM > 100) throw new Error('Bề rộng hành lang giới hạn 1 đến 100 m.');
    if (input.datum !== 'WGS84' || input.altitudeDatum !== 'RELATIVE_HOME' || input.units !== 'm') throw new Error('Chuẩn tọa độ hoặc đơn vị không khớp.');
    return { revision: input.revision, kind: input.kind, name, datum: 'WGS84', altitudeDatum: 'RELATIVE_HOME', units: 'm', geometry: geometry.map(p => p.slice()), altitudeM: input.altitudeM, corridorWidthM: input.corridorWidthM };
  }
  function wrapLongitude(value) { return ((value + 180) % 360 + 360) % 360 - 180; }
  function project(pair, home, metresPerPixel, center) {
    if (!coordinate(pair) || !coordinate([home.lat, home.lon]) || !finite(metresPerPixel) || metresPerPixel <= 0) return null;
    const r = Math.PI / 180 * 6378137;
    return [center[0] + wrapLongitude(pair[1] - home.lon) * r * Math.cos(home.lat * Math.PI / 180) / metresPerPixel, center[1] - (pair[0] - home.lat) * r / metresPerPixel];
  }
  function unproject(point, home, metresPerPixel, center) {
    const r = Math.PI / 180 * 6378137, cosine = Math.cos(home.lat * Math.PI / 180);
    if (Math.abs(cosine) < 1e-6) throw new Error('Biên tập tham chiếu tại cực chưa được hỗ trợ.');
    return [Number((home.lat - (point[1] - center[1]) * metresPerPixel / r).toFixed(7)), Number(wrapLongitude(home.lon + (point[0] - center[0]) * metresPerPixel / r / cosine).toFixed(7))];
  }
  function response(input) {
    if (!input || typeof input !== 'object' || input.version !== 1 || typeof input.id !== 'string' || input.id.length > 80 || !Number.isSafeInteger(input.viewEpoch) || input.viewEpoch <= 0 || !TYPES.includes(input.type) || typeof input.ok !== 'boolean') throw new Error('Phản hồi Android không đúng contract.');
    if (input.ok) {
      const d = input.data;
      if (!d || !VIEWS.includes(d.chosenView) || d.viewEpoch !== input.viewEpoch || !d.workspace || d.workspace.authorityRestorable !== false || d.noMedia !== true || !finite(d.nowElapsedNs) || d.nowElapsedNs < 0) throw new Error('Workspace hoặc định danh nguồn chưa hợp lệ.');
      if (!Array.isArray(d.workspace.reviews) || d.workspace.reviews.length > 32) throw new Error('Danh sách hồ sơ vượt giới hạn hiển thị.');
      const draft = d.workspace.draft;
      if (draft !== null) {
        if (!draft || draft.version !== 1 || typeof draft.id !== 'string' || draft.id.length > 100 || draft.trainingOnly !== true || draft.revision < 1 || !/^[0-9a-f]{64}$/.test(d.workspace.draftSHA256 || '')) throw new Error('Bản khảo sát chưa có revision/SHA hợp lệ.');
        validateDraft(draft);
      } else if (d.workspace.draftSHA256 !== null) throw new Error('SHA không có bản khảo sát đi kèm.');
      if (d.trajectory !== undefined && (!Array.isArray(d.trajectory) || d.trajectory.length > 2048)) throw new Error('Quỹ đạo trình bày vượt giới hạn.');
      if (d.native !== null && typeof d.native !== 'object') throw new Error('Nguồn native không hợp lệ.');
      if (d.workspace.reviews.some(r => !r || typeof r.id !== 'string' || r.id.length > 128 || !['FAILED', 'NATIVE_GROUND_OBSERVED_PENDING_EXTERNAL_VERIFICATION', 'UNKNOWN_PENDING_GROUND_VERIFICATION', 'PENDING_NATIVE_TERMINAL_OR_VERIFICATION'].includes(r.status) || r.authorityRestorable !== false || r.completionClaim !== false || r.actualImages !== 0 || r.trajectory && (!Array.isArray(r.trajectory) || r.trajectory.length > 2048))) throw new Error('Hồ sơ vượt contract hiển thị hoặc có tuyên bố chưa được kiểm.');
    }
    return input;
  }
  function telemetry(data, sinceArrivalMs) {
    const unknown = { fresh: false, altitude: null, speed: null, distance: null, satellites: null, mode: null, position: null, voltage: null, ageMs: null, reason: 'Chưa có nguồn' };
    if (!data || !data.native || !data.native.flight || !finite(sinceArrivalMs) || sinceArrivalMs < 0) return unknown;
    const f = data.native.flight, now = data.nowElapsedNs / 1e6;
    const observationAge = finite(data.nativeObservedElapsedNs) ? now - data.nativeObservedElapsedNs / 1e6 + sinceArrivalMs : Infinity;
    const positionAge = finite(f.positionMs) && f.positionMs >= 0 ? now - f.positionMs + sinceArrivalMs : Infinity;
    const heartbeatAge = finite(f.heartbeatMs) && f.heartbeatMs >= 0 ? now - f.heartbeatMs + sinceArrivalMs : Infinity;
    const ages = [observationAge, positionAge, heartbeatAge];
    if (!ages.every(a => finite(a) && a >= 0)) return { ...unknown, reason: 'Clock nguồn chưa hợp lệ' };
    const age = Math.max(...ages);
    if (!finite(age) || age < 0 || age > 1500 || !coordinate([f.lat, f.lon])) return { ...unknown, ageMs: finite(age) ? age : null, reason: age > 1500 ? 'Telemetry đã cũ' : 'Nguồn chưa xác định' };
    const validHome = f.home && Number.isInteger(f.home.latE7) && Number.isInteger(f.home.lonE7) && Number.isInteger(f.home.altMSLmm) && coordinate([f.home.latE7 / 1e7, f.home.lonE7 / 1e7]);
    const qualifiedPosition = f.firmwareObserved === true && [3, 4, 5, 6, 8].includes(f.GPSFix) && Number.isInteger(f.satellites) && f.satellites >= 6 && f.satellites <= 254 && validHome;
    if (!qualifiedPosition || data.native.closed === true) return { ...unknown, ageMs: age, reason: data.native.closed === true ? 'Phiên đã đóng' : 'Vị trí AP chưa đủ đối chiếu' };
    const p = [f.lat, f.lon]; let distance = null;
    if (f.home && Number.isInteger(f.home.latE7) && Number.isInteger(f.home.lonE7) && coordinate([f.home.latE7 / 1e7, f.home.lonE7 / 1e7])) {
      const h = { lat: f.home.latE7 / 1e7, lon: f.home.lonE7 / 1e7 }, xy = project(p, h, 1, [0, 0]); distance = Math.hypot(xy[0], xy[1]);
    }
    return { fresh: true, altitude: finite(f.relativeAltitudeM) ? f.relativeAltitudeM : null, speed: finite(f.horizontalSpeedMps) ? f.horizontalSpeedMps : null, distance, satellites: Number.isInteger(f.satellites) && f.satellites >= 0 && f.satellites <= 254 ? f.satellites : null, mode: Number.isInteger(f.mode) ? f.mode : null, position: p, voltage: finite(f.batteryWireMillivolts) && f.batteryWireMillivolts !== 65535 ? f.batteryWireMillivolts / 1000 : null, ageMs: age, reason: 'Vị trí AP mới · không suy ra độ mới GNSS' };
  }
  function trajectoryPath(input, home, metresPerPixel, center) {
    let path = '', shown = 0, excluded = 0, outside = 0, pen = false, previous = null;
    if (!Array.isArray(input)) return { path, shown, excluded, outside };
    input.slice(0, 2048).forEach(p => {
      if (!p || p.armedWindow !== true || p.positionQualified !== true || !finite(p.nativeRecordNs) || p.nativeRecordNs < 0 || !coordinate([p.lat, p.lon])) { pen = false; previous = null; excluded++; return; }
      if (previous !== null && (p.nativeRecordNs <= previous || p.nativeRecordNs - previous > 1500000000)) pen = false;
      const xy = project([p.lat, p.lon], home, metresPerPixel, center);
      if (!xy) { pen = false; previous = null; excluded++; return; }
      if (xy[0] < 0 || xy[0] > 1280 || xy[1] < 64 || xy[1] > 700) outside++;
      path += (pen ? 'L' : 'M') + xy.join(' ') + ' '; pen = true; previous = p.nativeRecordNs; shown++;
    });
    excluded += Math.max(0, input.length - 2048);
    return { path: path.trim(), shown, excluded, outside };
  }
  function observedHome(data) {
    const f = data && data.native && data.native.flight;
    return !!(f && f.home && Number.isInteger(f.home.latE7) && Number.isInteger(f.home.lonE7) && Number.isInteger(f.home.altMSLmm) && coordinate([f.home.latE7 / 1e7, f.home.lonE7 / 1e7]) && typeof f.homeHash === 'string' && /^[0-9a-f]{64}$/.test(f.homeHash));
  }
  function reviewStatus(review) {
    if (review && review.status === 'PENDING_NATIVE_TERMINAL_OR_VERIFICATION' && review.completionClaim === false && review.authorityRestorable === false && review.actualImages === 0) return 'Chờ đóng / kiểm hồ sơ';
    if (!review || review.completionClaim !== false || review.coverageClaim !== false || review.authorityRestorable !== false || review.actualImages !== 0) return 'Hồ sơ chưa đủ thông tin để đối chiếu';
    if (review.status === 'FAILED') return 'Đã đóng do lỗi · hồ sơ được giữ';
    if (review.status === 'NATIVE_GROUND_OBSERVED_PENDING_EXTERNAL_VERIFICATION') return 'Đã đóng · chờ đối chiếu độc lập';
    return 'Đã đóng · chưa xác nhận trạng thái mặt đất';
  }
  global.AerisUIModel = Object.freeze({ VIEWS, TYPES, referenceHome, finite, coordinate, parseCoordinates, validateDraft, project, unproject, response, telemetry, trajectoryPath, observedHome, reviewStatus });
})(typeof window === 'object' ? window : globalThis);
