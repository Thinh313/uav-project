export type ConnectionContext=Readonly<{sessionId:string;generation:number;configSha256:string}>;
export type Binding=Readonly<{id:string;label:string;cameraKey:string;gimbalKey:string|null}>;
export type MockConfiguration=Readonly<{format:'aeris-mock-transport-config';version:1;origin:'SYNTHETIC_DECLARED_CONFIGURATION';aircraftSystem:number;autopilotComponent:1;sender:{system:255;component:190};links:readonly string[];bindings:readonly Binding[]}>;
export type Intent=Readonly<{bindingId:string;operation:'discover-camera'|'discover-gimbal'|'zoom'|'focus'|'capture'|'authority'|'gimbal';value:number|{pitchDeg:number;yawDeg:number}|null;context:ConnectionContext}>;
export type TransportEnvelope=Readonly<{context:ConnectionContext;linkId:string;bindingId:string;transactionId:string;bytes:Uint8Array}>;
export type ReceiveEvent=Readonly<{kind:'bytes';context:ConnectionContext;linkId:string;bytes:Uint8Array}>|Readonly<{kind:'link-down';context:ConnectionContext;linkId:string}>;
/** Future seam only: current implementation accepts MockTransport branded instances, no real adapter. */
export interface TransportContract{connect(context:ConnectionContext,links:readonly string[],receive:(e:ReceiveEvent)=>void):void;disconnect():void;send(envelope:TransportEnvelope):{status:'MOCK_SEND_ADMITTED_NOT_ACK'|'SEND_UNCERTAIN'};}
