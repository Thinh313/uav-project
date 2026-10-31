/** Vendor semantic seam; no Phase One SDK implementation or physical compatibility claimed. */
export type UnknownClientCamera={format:'aeris-camera-contract65';version:1;kind:'PHASE_ONE_CLIENT_CONFIGURATION';origin:'USER_INTAKE_UNKNOWN';brand:'Phase One';model:null;firmware:null;lens:null;api:null;calibration:null;controls:null;physicalSupport:'NOT_CHECKED'};
export type SemanticControl={operation:'capture';value:null}|{operation:'zoomPercent'|'focusPercent';value:number}|{operation:'gimbalAngle';value:{pitchDeg:number;yawDeg:number}};
export type Context={sessionId:string;generation:number;configSha256:string;authorityEpoch:number};
export type ExclusiveTicket=Context&{scope:string;owner:'pilot-a'|'payload-b';revision:number;expiresMs:number};
export interface PhaseOneAdapterSeam {readonly implemented:false;readonly sdk:null;readonly hardwareSupport:'NOT_CHECKED';}
export type CaptureStages={intent:'RECORDED_MOCK';send:'NOT_SENT'|'MOCK_SEND_ADMITTED_NOT_ACK'|'SEND_UNCERTAIN'|string;ack:'UNKNOWN'|'ACCEPTED'|'IN_PROGRESS'|'REJECTED';observation:'NONE'|'CONSISTENT_UNATTRIBUTED';syntheticExposureMetadata:boolean;fileDeclaration:'NONE'|'SYNTHETIC_DECLARATION_ONLY';exposureProven:false;physicalFileVerified:false;actualImages:0};
/** Real authenticated identity, receiver authority enforcement, clock trust and loss policy remain unimplemented. */
export type OperatorIdentitySeam={mode:'LOCAL_MOCK_ONLY_NOT_REMOTE_AUTHENTICATION';physicalStations:'NOT_CHECKED';lossAction:'UNSPECIFIED_NOT_EXECUTED'};
