/** Test-only synthetic 1x1 JPEG and assistant-authored metadata. Not camera/SITL observations. */
import { syntheticJpegBytes } from '../../../media/big02/geotag-fixtures.mjs';
import { sha256 } from './schema.mjs';
export { syntheticJpegBytes };
export function fixture(captureId='capture-001') {
  const originalBytes=syntheticJpegBytes();
  const context={gatewaySession:'fixture-session',stationId:'fixture-station',modelSha256:'1'.repeat(64),planSha256:'2'.repeat(64),
    flightRun:'fixture-flight',flightBoot:'fixture-flight-boot',payloadId:'fixture-payload',sourceRun:'fixture-source',
    sourceBoot:'fixture-source-boot',configId:'fixture-config',feed:'fixture-feed'};
  const sidecar={schemaVersion:1,kind:'FIELD01_SYNTHETIC_CAPTURE',sourceKind:'SYNTHETIC',actualImages:0,
    captureId,frameId:'fixture-frame',context,
    position:{latitudeDeg:10.5,longitudeDeg:106.5,altitudeMslM:12.5,relativeHomeM:2.5,datum:'MSL',
      method:'NEAREST_HOST_RECEIPT_REFERENCE_NO_SENSOR_SYNC',qualifiedForSurvey:false,sensorTimeUncertaintyMs:null,hostMonoMs:1000},
    timing:{sourceTimestampUs:900000,sourceToHostLowerMs:90,sourceToHostUpperMs:110,referenceHostMonoMs:1000,
      method:'BOUND_SOURCE_CLOCK_TO_HOST_RECEIPT',physicalExposureTime:'UNKNOWN'},
    file:{name:'original.jpg',mime:'image/jpeg',sizeBytes:originalBytes.length,sha256:sha256(originalBytes)}};
  const link={schemaVersion:1,captureId,modelSha256:context.modelSha256,planSha256:context.planSha256,
    flightRun:context.flightRun,flightBoot:context.flightBoot,payloadId:context.payloadId,sourceKind:'SYNTHETIC',actualImages:0};
  return {originalBytes,sidecar,link};
}
