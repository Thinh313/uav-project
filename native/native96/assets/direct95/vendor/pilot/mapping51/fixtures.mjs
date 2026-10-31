const ns='http://www.opengis.net/kml/2.2';
export const kml=g=>`<?xml version="1.0" encoding="UTF-8"?><kml xmlns="${ns}"><Document>${g}</Document></kml>`;
export const polygon=coords=>`<Placemark><name>Vùng khảo sát mẫu</name><Polygon><outerBoundaryIs><LinearRing><coordinates>${coords}</coordinates></LinearRing></outerBoundaryIs></Polygon></Placemark>`;
export const line=coords=>`<Placemark><name>Tuyến giao thông mẫu</name><LineString><coordinates>${coords}</coordinates></LineString></Placemark>`;
export const SAMPLES={
 polygon:kml(polygon('106.807,10.854,0 106.809,10.854,0 106.809,10.8555,0 106.807,10.8555,0 106.807,10.854,0')),
 corridor:kml(line('106.807,10.854,0 106.810,10.854,0 106.811,10.856,0')),
 multiple:kml(polygon('106.807,10.854,0 106.809,10.854,0 106.809,10.8555,0 106.807,10.8555,0 106.807,10.854,0')+line('106.807,10.854 106.810,10.854 106.811,10.856')),
 absolute:kml(line('106.807,10.854,80 106.810,10.854,80').replace('<LineString>','<LineString><altitudeMode>absolute</altitudeMode>')),
};
