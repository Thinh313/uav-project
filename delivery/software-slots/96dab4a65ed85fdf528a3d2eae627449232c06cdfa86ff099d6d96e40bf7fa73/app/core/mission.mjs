/** Executable specification for a synthetic flat rectangular survey, in metres. */
export const DEFAULT_SETTINGS = Object.freeze({
  width: 360, height: 220, altitude: 60, speed: 6, sideOverlap: 80,
  frontOverlap: 80, sensorWidth: 13.2, sensorHeight: 8.8, focalLength: 8.8,
  imageWidth: 5472, minInterval: 1
});
const ranges = {
  width: [30, 3000], height: [30, 3000], altitude: [5, 120], speed: [0.5, 20],
  sideOverlap: [0, 95], frontOverlap: [0, 95], sensorWidth: [1, 100],
  sensorHeight: [1, 100], focalLength: [1, 200], imageWidth: [100, 20000], minInterval: [0.05, 60]
};
export function validateSettings(settings) {
  if (!settings || typeof settings !== 'object' || Array.isArray(settings)) throw new Error('Thông số nhiệm vụ không hợp lệ.');
  for (const [key, [low, high]] of Object.entries(ranges)) {
    const value = settings[key];
    if (typeof value !== 'number' || !Number.isFinite(value) || value < low || value > high)
      throw new Error(`${key}: cần số từ ${low} đến ${high}.`);
  }
  if (!Number.isInteger(settings.imageWidth)) throw new Error('imageWidth: cần số nguyên.');
  if (Object.keys(settings).some(key => !(key in ranges))) throw new Error('Có trường thông số chưa được hỗ trợ.');
  return { ...settings };
}
export function planSurvey(input) {
  const s = validateSettings(input);
  const footprintWidth = s.altitude * s.sensorWidth / s.focalLength;
  const footprintHeight = s.altitude * s.sensorHeight / s.focalLength;
  const nominalLineSpacing = footprintWidth * (1 - s.sideOverlap / 100);
  const nominalTriggerSpacing = footprintHeight * (1 - s.frontOverlap / 100);
  const usableWidth = Math.max(0, s.width - footprintWidth);
  const lineCount = usableWidth === 0 ? 1 : Math.ceil(usableWidth / nominalLineSpacing - 1e-10) + 1;
  const shotsPerLine = Math.ceil(s.height / nominalTriggerSpacing - 1e-10) + 1;
  if (lineCount > 2000 || lineCount * shotsPerLine > 20000) throw new Error('Nhiệm vụ vượt giới hạn 20.000 ảnh hoặc 2.000 tuyến của bản diễn tập.');
  const lineSpacing = lineCount > 1 ? usableWidth / (lineCount - 1) : 0;
  const triggerSpacing = s.height / (shotsPerLine - 1);
  const triggerInterval = triggerSpacing / s.speed;
  const transects = Array.from({ length: lineCount }, (_, i) => {
    const x = lineCount === 1 ? s.width / 2 : footprintWidth / 2 + i * lineSpacing;
    return { index: i + 1, start: { x, y: i % 2 ? s.height : 0 }, end: { x, y: i % 2 ? 0 : s.height } };
  });
  const waypoints = transects.flatMap(t => [t.start, t.end]);
  const distance = waypoints.slice(1).reduce((sum, p, i) => sum + Math.hypot(p.x - waypoints[i].x, p.y - waypoints[i].y), 0);
  const warnings = triggerInterval + 1e-10 < s.minInterval ? ['Tốc độ hiện tại yêu cầu chụp nhanh hơn chu kỳ camera. Giảm tốc hoặc giảm chồng ảnh.'] : [];
  return {
    settings: s, area: s.width * s.height, footprintWidth, footprintHeight,
    nominalLineSpacing, lineSpacing, nominalTriggerSpacing, triggerSpacing, triggerInterval,
    lineCount, shotsPerLine, photoCount: lineCount * shotsPerLine, transects, waypoints,
    distance, nominalSeconds: distance / s.speed,
    gsdCm: footprintWidth / s.imageWidth * 100, feasible: warnings.length === 0, warnings,
    model: 'flat-local-rectangle-v1', operational: false
  };
}
export function missionPackage(settings) {
  const plan = planSurvey(settings);
  if (!plan.feasible) throw new Error(plan.warnings[0]);
  return { format: 'aeris-rehearsal', version: 1, operational: false, model: plan.model, settings: plan.settings };
}
export function importMission(text) {
  if (typeof text !== 'string' || text.length > 256 * 1024) throw new Error('Gói nhiệm vụ phải nhỏ hơn 256 KB.');
  let data;
  try { data = JSON.parse(text); } catch { throw new Error('Không đọc được JSON nhiệm vụ.'); }
  if (!data || data.format !== 'aeris-rehearsal' || data.version !== 1 || data.operational !== false || data.model !== 'flat-local-rectangle-v1')
    throw new Error('Chỉ đọc gói diễn tập AERIS v1; chưa hỗ trợ QGC .plan.');
  if (Object.keys(data).some(k => !['format', 'version', 'operational', 'model', 'settings'].includes(k)))
    throw new Error('Gói có trường chưa được hỗ trợ.');
  return missionPackage(data.settings);
}
