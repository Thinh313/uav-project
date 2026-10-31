(function () {
  'use strict';
  const M = window.AerisUIModel, $ = id => document.getElementById(id), ns = 'http://www.w3.org/2000/svg';
  let presentationGeneration = 0;
  let epoch = null, sequence = 0, lastNativeNs = -1, data = null, arrival = 0, view = 'survey', dirty = false;
  let editRevision = 0, editingGeometry = [], lastDraftKey = '', selectedReview = null, reviewKey = '', theme = 'night';
  let metresPerPixel = .08, mapCenter = [720, 370], messageTimer = null, mapDraftKey = '';
  const pending = new Map(), reviewCache = new Map(), reviewRequested = new Set();
  const MODE_NAMES = Object.freeze({ 0: 'Ổn định', 3: 'AUTO', 4: 'GUIDED', 5: 'LOITER', 9: 'LAND', 17: 'BRAKE' });
  const metricCache = new Map(); let identityKey = '';
  function text(id, value) { const node = $(id), next = value == null ? '—' : String(value); if (node.textContent !== next) node.textContent = next; }
  function attribute(node, name, value) { if (node.getAttribute(name) !== value) node.setAttribute(name, value); }
  function hidden(id, value) { if ($(id).hidden !== value) $(id).hidden = value; }
  function disabled(id, value) { if ($(id).disabled !== value) $(id).disabled = value; }
  function message(value) {
    text('ui-message', value); hidden('ui-message', false);
    clearTimeout(messageTimer); messageTimer = setTimeout(() => { hidden('ui-message', true); }, 6000);
  }
  function ownerActive() { return !!(data && data.ownerActive === true || data && data.native && typeof data.native.run === 'string' && data.native.run.length > 0 && typeof data.native.epoch === 'string' && data.native.epoch.length > 0 && data.native.closed !== true); }
  function nativeLocked() { return ownerActive(); }
  function request(type, payload) {
    if (!M.TYPES.includes(type) || !epoch || !window.AerisWorkspace || typeof window.AerisWorkspace.post !== 'function') { message('Chưa có bridge Android. Bản khảo sát chưa được lưu.'); return false; }
    if (pending.size >= 2) { message('Đang chờ Android hoàn tất thao tác trước.'); return false; }
    if (++sequence > 2147483647) { message('Đã đạt giới hạn phiên giao diện. Không gửi thêm yêu cầu.'); return false; }
    const id = 'ui-' + epoch + '-' + sequence;
    const timeout = setTimeout(() => {
      if (pending.has(id)) { pending.delete(id); message('Android chưa xác nhận thao tác. Không tự gửi lại.'); renderControls(); }
    }, 5000);
    pending.set(id, { type, payload, timeout });
    try { window.AerisWorkspace.post(JSON.stringify({ version: 1, id, viewEpoch: epoch, type, payload })); }
    catch (error) { clearTimeout(timeout); pending.delete(id); message('Không gửi được yêu cầu tới Android. Bản khảo sát chưa được xác nhận lưu.'); }
    renderControls(); return true;
  }
  function receive(raw) {
    let result;
    try {
      if ((typeof raw === 'string' ? raw.length : JSON.stringify(raw).length) > 524288) throw new Error('Phản hồi vượt giới hạn.');
      if (typeof raw === 'string') raw = JSON.parse(raw);
      result = M.response(raw);
      const boot = result.id === 'BOOT' && result.type === 'LOAD';
      const push = result.id === 'PUSH' && result.type === 'STATE';
      if (boot) { if (epoch !== null) return; epoch = result.viewEpoch; }
      else if (result.viewEpoch !== epoch) return;
      let operation = null;
      if (!boot && !push) {
        operation = pending.get(result.id);
        if (!operation || operation.type !== result.type) return;
        clearTimeout(operation.timeout); pending.delete(result.id);
      }
      if (!result.ok) { message(typeof result.error === 'string' ? result.error : 'Android từ chối thao tác. Hồ sơ hiện có được giữ.'); renderControls(); return; }
      const next = result.data;
      if (next.nowElapsedNs < lastNativeNs || push && next.nowElapsedNs === lastNativeNs) return;
      const priorWorkspaceVersion = data && data.workspaceProjection && data.workspaceProjection.version;
      lastNativeNs = next.nowElapsedNs; data = next; arrival = performance.now();
      if (operation && operation.type === 'SAVE_DRAFT') {
        if (!next.workspace.draft || next.workspace.draft.revision !== operation.payload.revision + 1 || !/^[0-9a-f]{64}$/.test(next.workspace.draftSHA256 || '')) throw new Error('Thiếu xác nhận revision/SHA sau khi lưu.');
        dirty = false; lastDraftKey = '';
        message('Đã lưu khảo sát r' + next.workspace.draft.revision + ' trong workspace Android.');
      }
      if (operation && operation.type === 'REVIEWS') {
        const id = operation.payload.id, detail = next.selectedReview;
        if (detail && (detail.id !== id || detail.authorityRestorable !== false || detail.completionClaim !== false || detail.actualImages !== 0 || !Array.isArray(detail.trajectory) || detail.trajectory.length > 2048)) throw new Error('Hồ sơ chi tiết không khớp yêu cầu.');
        selectedReview = id;
        if (detail) {
          const summary = next.workspace.reviews.find(r => r.id === id);
          if (!summary || summary.nativeTerminalSHA256 !== detail.nativeTerminalSHA256) throw new Error('Neo journal hồ sơ không khớp.');
          reviewCache.set(reviewRecordKey(summary), detail);
          while (reviewCache.size > 4) reviewCache.delete(reviewCache.keys().next().value);
        }
        reviewKey = '';
      }
      const previousView = view; view = next.chosenView; renderState();
      if (boot || previousView !== view || priorWorkspaceVersion !== next.workspaceProjection.version) acknowledgePresentation();
    } catch (error) { message('Không áp dụng được dữ liệu Android: ' + String(error.message || error).slice(0, 180)); }
  }
  function acknowledgePresentation() {
    const generation = ++presentationGeneration, targetView = view, targetEpoch = epoch, targetWorkspaceVersion = data && data.workspaceProjection && data.workspaceProjection.version;
    requestAnimationFrame(() => requestAnimationFrame(() => {
      if (generation !== presentationGeneration || targetEpoch !== epoch || targetView !== view || !data || data.workspaceProjection.version !== targetWorkspaceVersion) return;
      // Presentation acknowledgement only, never a flight action/consent/input.
      request('STATE', { renderedView: targetView, renderedWorkspaceVersion: targetWorkspaceVersion });
    }));
  }
  window.AerisCockpit = Object.freeze({ receive });
  function loadDraft(draft, sha) {
    editRevision = draft ? draft.revision : 0;
    $('draft-name').value = draft ? draft.name : '';
    $('draft-type').value = draft ? draft.kind : 'polygon';
    $('draft-altitude').value = draft ? draft.altitudeM : 3;
    $('draft-width').value = draft ? draft.corridorWidthM : 10;
    editingGeometry = draft && Array.isArray(draft.geometry) ? draft.geometry.map(p => p.slice()) : [];
    $('draft-coordinates').value = editingGeometry.map(p => p.join(', ')).join('\n');
    text('draft-persisted', draft ? 'Đã lưu r' + draft.revision : 'Chưa lưu');
    text('draft-revision-label', draft ? 'r' + draft.revision + ' · SHA ' + sha.slice(0, 12) : 'Bản nháp chưa có hồ sơ');
    text('draft-error', ''); updateDraftShape();
  }
  function editChanged() {
    if (nativeLocked() || view !== 'survey') return;
    dirty = true; text('draft-persisted', 'Chưa lưu thay đổi');
    try { editingGeometry = M.parseCoordinates($('draft-coordinates').value); text('draft-error', ''); }
    catch (error) { text('draft-error', error.message); }
    updateDraftShape(); renderMap(); renderControls();
  }
  function updateDraftShape() {
    const corridor = $('draft-type').value === 'corridor';
    document.body.dataset.draftKind = corridor ? 'corridor' : 'polygon';
    $('corridor-width-row').hidden = !corridor;
    text('draft-point-count', editingGeometry.length + ' điểm');
    text('draft-example', corridor ? 'Tạo hành lang tham chiếu' : 'Tạo vùng tham chiếu');
  }
  function saveDraft() {
    if (nativeLocked() || view !== 'survey') { message('Không sửa khảo sát khi phiên bay còn quyền điều khiển.'); return; }
    try {
      const draft = M.validateDraft({ revision: editRevision, name: $('draft-name').value, kind: $('draft-type').value, datum: 'WGS84', altitudeDatum: 'RELATIVE_HOME', units: 'm', geometry: M.parseCoordinates($('draft-coordinates').value), altitudeM: Number($('draft-altitude').value), corridorWidthM: Number($('draft-width').value) });
      request('SAVE_DRAFT', draft);
    } catch (error) { text('draft-error', error.message); }
  }
  function renderControls() {
    const saving = Array.from(pending.values()).some(p => p.type === 'SAVE_DRAFT');
    ['draft-name', 'draft-type', 'draft-altitude', 'draft-width', 'draft-coordinates', 'draft-example', 'draft-undo'].forEach(id => { disabled(id, nativeLocked() || saving); });
    disabled('draft-save', !epoch || nativeLocked() || saving);
    text('draft-save-label', saving ? 'Đang lưu…' : 'Lưu khảo sát');
    document.querySelectorAll('[data-nav]').forEach(button => {
      const target = button.dataset.nav;
      const blocked = ownerActive() && target !== view && target !== 'fly'; if (button.disabled !== blocked) button.disabled = blocked;
      attribute(button, 'aria-current', target === view ? 'page' : 'false');
    });
  }
  function renderState() {
    if (document.body.dataset.view !== view) document.body.dataset.view = view;
    M.VIEWS.forEach(name => { hidden('view-' + name, name !== view); });
    hidden('native-bar-underlay', !['preflight', 'fly'].includes(view));
    hidden('native-home-underlay', view !== 'fly' || !M.observedHome(data)); hidden('native-left-pad-underlay', view !== 'fly'); hidden('native-right-pad-underlay', view !== 'fly');
    $('map-stage').classList.toggle('editing', view === 'survey' && !nativeLocked());
    const workspace = data.workspace, draft = workspace.draft;
    const key = draft ? draft.revision + ':' + workspace.draftSHA256 : 'empty';
    if (!dirty && key !== lastDraftKey) { lastDraftKey = key; loadDraft(draft, workspace.draftSHA256 || ''); }
    const name = draft ? draft.name : 'Chưa lưu khảo sát';
    text('preflight-draft-name', name); text('fly-draft-name', name);
    text('preflight-draft-revision', draft ? 'Revision ' + draft.revision + ' · WGS84 · độ cao so với Home' : 'Lưu khảo sát trước khi kiểm tra.');
    text('preflight-draft-sha', workspace.draftSHA256 || 'SHA chưa có');
    text('fly-draft-sha', workspace.draftSHA256 ? 'r' + draft.revision + ' · ' + workspace.draftSHA256.slice(0, 12) : 'SHA chưa có');
    $('fly-draft-sha').title = workspace.draftSHA256 || 'Chưa có SHA được Android xác nhận';
    renderPreflight(); renderReview(); renderControls(); renderMap();
  }
  function renderPreflight() {
    const native = data.native, f = native && native.flight;
    const ready = !!(native && native.preflightReady === true && native.closed !== true);
    text('preflight-status', ready ? 'Native đã đối chiếu' : 'Chưa đủ dữ liệu'); $('preflight-status').classList.toggle('ready', ready);
    text('preflight-firmware', f && f.firmwareObserved === true ? '4.7.1-dev · dbe79216' : 'Chưa xác định');
    text('preflight-parameters', f && Number.isInteger(f.typedParameterCount) ? f.typedParameterCount + ' / 39' : '— / 39');
    text('preflight-gps', f && Number.isInteger(f.GPSFix) ? 'Fix ' + f.GPSFix + ' · ' + (Number.isInteger(f.satellites) ? f.satellites : '—') + ' vệ tinh · ' + (M.finite(f.GPSHDOP100) ? 'HDOP ' + (f.GPSHDOP100 / 100).toFixed(2) : 'HDOP —') : 'Chưa có dữ liệu');
    text('preflight-ekf', f && Number.isInteger(f.EKFFlags) ? 'Cờ 0x' + f.EKFFlags.toString(16) : 'Chưa có dữ liệu');
    text('preflight-home', f && f.home && Number.isInteger(f.home.latE7) && Number.isInteger(f.home.lonE7) ? (f.home.latE7 / 1e7).toFixed(7) + ', ' + (f.home.lonE7 / 1e7).toFixed(7) : 'Chưa quan sát');
    text('preflight-reason', native && native.closed ? 'Phiên đã đóng. Lịch sử không khôi phục quyền điều khiển.' : ready ? 'Đối chiếu native đã đạt. Chọn Bay; cấp quyền bằng nút Android sau thao tác đưa cần về giữa.' : native && native.preflightReason ? 'Native chưa cho phép: ' + native.preflightReason : 'Kết nối nguồn SITL bằng nút Android bên dưới. Quyền điều khiển chỉ cấp từ Android.');
    const identities = $('context-identities');
    const source = data.sourceIdentity || {};
    const nextIdentityKey = JSON.stringify([native && native.run, native && native.epoch, native && native.boot, source]);
    if (nextIdentityKey === identityKey) return; identityKey = nextIdentityKey; identities.replaceChildren();
    [['Phiên', native && native.run], ['Epoch', native && native.epoch], ['Boot', native && native.boot], ['AP', source.binarySHA256], ['Mô hình', source.modelSHA256], ['Cấu hình', source.configSHA256]].forEach(([label, value]) => { const dt = document.createElement('dt'), dd = document.createElement('dd'); dt.textContent = label; dd.textContent = value || 'Chưa xác định'; identities.append(dt, dd); });
  }
  function metric(id, value, unit, decimals) {
    const node = $(id), formatted = M.finite(value) ? value.toFixed(decimals) : '—', cache = formatted + '|' + unit;
    if (metricCache.get(id) === cache) return; metricCache.set(id, cache); node.replaceChildren(document.createTextNode(formatted));
    if (unit) { const small = document.createElement('small'); small.textContent = unit; node.append(small); }
  }
  function renderTelemetry() {
    const hud = M.telemetry(data, data ? Math.max(0, performance.now() - arrival) : 0);
    metric('hud-altitude', hud.altitude, 'm', 1); metric('hud-speed', hud.speed, 'm/s', 1); metric('hud-distance', hud.distance, 'm', 1); metric('hud-satellites', hud.satellites, '', 0);
    const native = data && data.native;
    text('hud-age', hud.fresh ? 'Vị trí AP · ' + Math.round(hud.ageMs) + ' ms' : hud.reason);
    text('hud-status', hud.mode !== null ? MODE_NAMES[hud.mode] || 'Chế độ ' + hud.mode : native && native.closed ? 'Phiên đã đóng' : 'Chưa xác định');
    text('fly-mode', hud.mode !== null ? MODE_NAMES[hud.mode] || 'Chế độ ' + hud.mode : 'Chưa có telemetry đủ đối chiếu');
    text('fly-source', hud.fresh ? 'Nguồn AP thực trong SITL. Vị trí AP mới không tự chứng minh độ mới GNSS.' : hud.reason + '. Không suy ra vị trí từ tuyến dự kiến.');
    text('connection-label', native && native.closed ? 'Phiên đã đóng' : hud.fresh ? 'Liên kết AP · SITL' : native ? 'SITL · chờ đối chiếu' : 'Chưa kết nối');
    attribute($('battery-indicator'), 'aria-label', hud.voltage === null ? 'Điện áp pin chưa biết' : 'Điện áp pin ' + hud.voltage.toFixed(2) + ' vôn');
    const marker = $('aircraft-marker');
    if (!hud.position && !marker.hasAttribute('hidden')) marker.setAttribute('hidden', '');
    if (hud.position && marker.hasAttribute('hidden')) marker.removeAttribute('hidden');
    if (hud.position) {
      const p = M.project(hud.position, M.referenceHome, metresPerPixel, mapCenter), heading = native && native.flight && native.flight.headingCentiDeg;
      const direction = $('aircraft-direction'), hasHeading = M.finite(heading) && heading !== 65535;
      if (!hasHeading && !direction.hasAttribute('hidden')) direction.setAttribute('hidden', '');
      if (hasHeading && direction.hasAttribute('hidden')) direction.removeAttribute('hidden');
      if (p) attribute(marker, 'transform', 'translate(' + p.join(' ') + ') rotate(' + (M.finite(heading) && heading !== 65535 ? heading / 100 : 0) + ')');
    }
  }
  function reviewDetail(review) {
    const node = $('review-detail'); node.replaceChildren();
    const heading = document.createElement('h2'); heading.textContent = review.run || review.id || 'Hồ sơ'; node.append(heading);
    const status = document.createElement('p'); status.className = 'review-status' + (review.status === 'FAILED' ? ' failed' : ''); status.textContent = M.reviewStatus(review); node.append(status);
    const dl = document.createElement('dl');
    [['Khảo sát', 'Revision ' + review.surveyRevision], ['SHA khảo sát', review.surveySHA256], ['Neo journal native', review.nativeTerminalSHA256], ['Epoch / Boot', (review.epoch || '—') + ' / ' + (review.boot || '—')], ['Nhóm mặt đất native', Number.isInteger(review.groundDistinctFreshGroups) ? String(review.groundDistinctFreshGroups) + ' · chưa thay đối chiếu độc lập' : 'Chưa xác định'], ['Quỹ đạo quan sát', Array.isArray(review.trajectory) ? review.trajectory.length + ' điểm trong bản trình bày' : 'Chưa có'], ['Ảnh thực', '0 · không có nguồn camera']].forEach(([label, value]) => { const dt = document.createElement('dt'), dd = document.createElement('dd'); dt.textContent = label; dd.textContent = value == null ? 'Chưa xác định' : String(value); dl.append(dt, dd); }); node.append(dl);
    const scope = document.createElement('p'); scope.className = 'review-scope'; scope.textContent = 'Tuyến khảo sát là bản dự kiến cho bài huấn luyện manual / có trợ giúp. Hồ sơ này không khẳng định đã bay AUTO, hoàn thành độ phủ hoặc thu ảnh. Khi mở lại, chỉ hồ sơ được nạp; kết nối và quyền điều khiển không tự khôi phục.'; node.append(scope);
  }
  function reviewRecordKey(record) { return record.id + ':' + (record.nativeTerminalSHA256 || record.durableLinkSHA || record.status); }
  function selectedReviewRecord() {
    const summary = data && data.workspace.reviews.find(r => r.id === selectedReview);
    return summary ? reviewCache.get(reviewRecordKey(summary)) || summary : null;
  }
  function askReview(record, explicit) {
    const key = reviewRecordKey(record);
    if (!explicit && reviewRequested.has(key)) return;
    if (reviewRequested.size >= 64) { message('Đã đạt giới hạn yêu cầu hồ sơ của phiên giao diện.'); return; }
    reviewRequested.add(key); request('REVIEWS', { id: record.id });
  }
  function renderReview() {
    const records = data.workspace.reviews;
    if (!records.length) return;
    if (!records.some(r => r.id === selectedReview)) selectedReview = records[records.length - 1].id;
    const current = selectedReviewRecord();
    const key = records.map(r => reviewRecordKey(r) + ':' + r.status).join('|') + ':' + selectedReview + ':' + (current && Array.isArray(current.trajectory) ? current.trajectory.length : 'summary');
    if (key === reviewKey) return;
    reviewKey = key; const list = $('review-list'); list.replaceChildren();
    records.forEach(record => {
      const button = document.createElement('button'); button.type = 'button'; button.setAttribute('aria-label', (record.id === selectedReview ? 'Đang xem hồ sơ ' : 'Mở hồ sơ ') + (record.run || record.id)); button.setAttribute('aria-current', String(record.id === selectedReview));
      const title = document.createElement('strong'), hint = document.createElement('small'); title.textContent = record.run || record.id; hint.textContent = 'Khảo sát r' + record.surveyRevision + ' · ' + (record.status === 'FAILED' ? 'Đóng do lỗi' : record.status === 'PENDING_NATIVE_TERMINAL_OR_VERIFICATION' ? 'Chờ đóng / kiểm' : 'Chờ đối chiếu'); const selectedMark = document.createElementNS(ns, 'svg'), selectedPath = document.createElementNS(ns, 'path'); selectedMark.setAttribute('class', 'icon review-selection-mark'); selectedMark.setAttribute('viewBox', '0 0 24 24'); selectedMark.setAttribute('aria-hidden', 'true'); selectedPath.setAttribute('d', 'M5 12l4 4L19 6'); selectedMark.append(selectedPath); button.append(title, hint, selectedMark);
      button.addEventListener('click', () => askReview(record, true)); list.append(button);
    });
    reviewDetail(current);
    if (view === 'review' && !reviewCache.has(reviewRecordKey(current))) askReview(current, false);
  }

  function renderMap() {
    const path = $('planned-route'), points = $('route-points');
    const draft = data && data.workspace.draft, geometry = view === 'survey' ? editingGeometry : draft && draft.geometry || [];
    const projected = geometry.map(p => M.project(p, M.referenceHome, metresPerPixel, mapCenter)).filter(Boolean);
    const nextMapDraftKey = JSON.stringify([geometry, metresPerPixel, view === 'survey' ? $('draft-type').value : draft && draft.kind]);
    if (nextMapDraftKey !== mapDraftKey) {
    mapDraftKey = nextMapDraftKey; points.replaceChildren();
    path.setAttribute('d', projected.map((p, i) => (i ? 'L' : 'M') + p.join(' ')).join(' ') + (projected.length >= 3 && (view === 'survey' ? $('draft-type').value : draft.kind) === 'polygon' ? 'Z' : ''));
    projected.forEach((p, i) => { const g = document.createElementNS(ns, 'g'), circle = document.createElementNS(ns, 'circle'), label = document.createElementNS(ns, 'text'); g.setAttribute('transform', 'translate(' + p.join(' ') + ')'); circle.setAttribute('r', 10); label.setAttribute('y', 4); label.textContent = i + 1; g.append(circle, label); points.append(g); });
    }
    text('map-scale-label', (.08 / metresPerPixel).toFixed(1) + '×');
    attribute($('home-symbol'), 'transform', 'translate(' + mapCenter.join(' ') + ')');
    let trajectory = data && Array.isArray(data.trajectory) ? data.trajectory : [];
    if (view === 'review' && data) { const review = selectedReviewRecord(); trajectory = review && Array.isArray(review.trajectory) ? review.trajectory : []; }
    const trace = M.trajectoryPath(trajectory, M.referenceHome, metresPerPixel, mapCenter);
    attribute($('actual-track'), 'd', trace.path);
    text('trajectory-caption', trace.shown ? trace.shown + ' điểm trình bày đã định vị trong cửa sổ ARM' + (trace.excluded ? ' · ' + trace.excluded + ' điểm chưa đủ điều kiện hiển thị' : '') + (trace.outside ? ' · ' + trace.outside + ' điểm ngoài khung, vẫn giữ trong hồ sơ' : '') : 'Tuyến dự kiến; chưa có quỹ đạo ARM đủ đối chiếu');
    renderTelemetry();
  }
  function setTheme(next) {
    theme = next; document.body.dataset.theme = theme;
    const label = theme === 'night' ? 'Chuyển sang giao diện sáng' : 'Chuyển sang giao diện tối';
    $('theme').setAttribute('aria-label', label); $('theme').title = label; $('theme-icon').setAttribute('href', theme === 'night' ? '#i-sun' : '#i-moon');
  }
  document.querySelectorAll('[data-nav]').forEach(button => button.addEventListener('click', () => {
    const target = button.dataset.nav;
    if (target === view) return;
    if (dirty) { message('Lưu thay đổi khảo sát trước khi chuyển màn hình.'); return; }
    request('NAVIGATE', { view: target });
  }));
  ['draft-name', 'draft-type', 'draft-altitude', 'draft-width', 'draft-coordinates'].forEach(id => $(id).addEventListener(id === 'draft-type' ? 'change' : 'input', editChanged));
  $('draft-save').addEventListener('click', saveDraft);
  $('draft-example').addEventListener('click', () => {
    if (nativeLocked() || view !== 'survey') return;
    const local = $('draft-type').value === 'corridor' ? [[-10, -5], [0, 4], [10, 5]] : [[-10, -10], [10, -10], [10, 10], [-10, 10]];
    editingGeometry = local.map(p => M.unproject([mapCenter[0] + p[0] / metresPerPixel, mapCenter[1] - p[1] / metresPerPixel], M.referenceHome, metresPerPixel, mapCenter));
    $('draft-coordinates').value = editingGeometry.map(p => p.join(', ')).join('\n'); editChanged();
  });
  $('draft-undo').addEventListener('click', () => { if (nativeLocked() || view !== 'survey') return; editingGeometry.pop(); $('draft-coordinates').value = editingGeometry.map(p => p.join(', ')).join('\n'); editChanged(); });
  $('reference-map').addEventListener('click', event => {
    if (view !== 'survey' || nativeLocked() || editingGeometry.length >= 64) return;
    const rect = $('reference-map').getBoundingClientRect(), p = [(event.clientX - rect.left) * 1280 / rect.width, (event.clientY - rect.top) * 800 / rect.height];
    if (p[0] < 500 || p[0] > 1184 || p[1] < 88 || p[1] > 684) return;
    editingGeometry.push(M.unproject(p, M.referenceHome, metresPerPixel, mapCenter)); $('draft-coordinates').value = editingGeometry.map(p => p.join(', ')).join('\n'); editChanged();
  });
  $('theme').addEventListener('click', () => setTheme(theme === 'night' ? 'day' : 'night'));
  $('map-zoom-in').addEventListener('click', () => { metresPerPixel = Math.max(.02, metresPerPixel / 1.5); renderMap(); });
  $('map-zoom-out').addEventListener('click', () => { metresPerPixel = Math.min(5, metresPerPixel * 1.5); renderMap(); });
  $('map-fit').addEventListener('click', () => { metresPerPixel = .08; mapCenter = [720, 370]; renderMap(); });
  setTheme('night'); loadDraft(null, ''); renderControls(); renderMap();
  // Display-age only: no bridge requests, fake positions, input sampling or authority.
  setInterval(renderTelemetry, 200);
})();
