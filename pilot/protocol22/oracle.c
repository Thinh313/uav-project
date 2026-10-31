#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#define MAVLINK_MAX_PAYLOAD_LEN 255
#define MAVLINK_STX 253
#define MAVLINK_COMMAND_24BIT 1
#define MAVLINK_CRC_EXTRA 1
#define MAVLINK_ALIGNED_FIELDS 1
#define MAVLINK_ENDIAN MAVLINK_LITTLE_ENDIAN
#define MAVLINK_MESSAGE_CRCS {{0,50,9,9,0,0,0},{76,152,33,33,3,30,31},{77,143,3,10,3,8,9},{259,92,235,237,0,0,0},{260,146,5,14,0,0,0},{262,12,18,23,0,0,0},{263,133,255,255,0,0,0},{269,109,213,217,0,0,0},{270,59,19,22,0,0,0},{280,70,33,33,0,0,0},{281,48,13,13,0,0,0},{285,137,40,49,3,38,39},{287,1,23,23,3,20,21}}
#include "protocol.h"
#include "minimal/mavlink_msg_heartbeat.h"
#include "common/mavlink_msg_command_long.h"
#include "common/mavlink_msg_command_ack.h"
#include "common/mavlink_msg_camera_information.h"
#include "common/mavlink_msg_camera_settings.h"
#include "common/mavlink_msg_camera_capture_status.h"
#include "common/mavlink_msg_camera_image_captured.h"
#include "common/mavlink_msg_video_stream_information.h"
#include "common/mavlink_msg_video_stream_status.h"
#include "common/mavlink_msg_gimbal_manager_information.h"
#include "common/mavlink_msg_gimbal_manager_status.h"
#include "common/mavlink_msg_gimbal_device_attitude_status.h"
#include "common/mavlink_msg_gimbal_manager_set_pitchyaw.h"
static double num(){char b[128];if(scanf("%127s",b)!=1)exit(2);return strtod(b,0);}
static unsigned long long wide(){char b[128];if(scanf("%127s",b)!=1)exit(2);return strtoull(b,0,10);}
int main(){unsigned id,sys,comp,seq;if(scanf("%u %u %u %u",&id,&sys,&comp,&seq)!=4)return 2;mavlink_message_t msg;mavlink_status_t st={0};st.current_tx_seq=seq;switch(id){
case 0:{
uint8_t type=(uint8_t)num();
uint8_t autopilot=(uint8_t)num();
uint8_t base_mode=(uint8_t)num();
uint32_t custom_mode=(uint32_t)num();
uint8_t system_status=(uint8_t)num();
uint8_t mavlink_version=(uint8_t)num();
mavlink_msg_heartbeat_pack_status(sys,comp,&st,&msg,type,autopilot,base_mode,custom_mode,system_status);break;}
case 76:{
uint8_t target_system=(uint8_t)num();
uint8_t target_component=(uint8_t)num();
uint16_t command=(uint16_t)num();
uint8_t confirmation=(uint8_t)num();
float param1=(float)num();
float param2=(float)num();
float param3=(float)num();
float param4=(float)num();
float param5=(float)num();
float param6=(float)num();
float param7=(float)num();
mavlink_msg_command_long_pack_status(sys,comp,&st,&msg,target_system,target_component,command,confirmation,param1,param2,param3,param4,param5,param6,param7);break;}
case 77:{
uint16_t command=(uint16_t)num();
uint8_t result=(uint8_t)num();
uint8_t progress=(uint8_t)num();
int32_t result_param2=(int32_t)num();
uint8_t target_system=(uint8_t)num();
uint8_t target_component=(uint8_t)num();
mavlink_msg_command_ack_pack_status(sys,comp,&st,&msg,command,result,progress,result_param2,target_system,target_component);break;}
case 259:{
uint32_t time_boot_ms=(uint32_t)num();
uint8_t vendor_name[32]={0};
for(int i=0;i<32;i++)vendor_name[i]=(uint8_t)num();
uint8_t model_name[32]={0};
for(int i=0;i<32;i++)model_name[i]=(uint8_t)num();
uint32_t firmware_version=(uint32_t)num();
float focal_length=(float)num();
float sensor_size_h=(float)num();
float sensor_size_v=(float)num();
uint16_t resolution_h=(uint16_t)num();
uint16_t resolution_v=(uint16_t)num();
uint8_t lens_id=(uint8_t)num();
uint32_t flags=(uint32_t)num();
uint16_t cam_definition_version=(uint16_t)num();
char cam_definition_uri[140]={0};
char in_cam_definition_uri[512];if(scanf("%511s",in_cam_definition_uri)!=1)return 2;if(strcmp(in_cam_definition_uri,"_")!=0)strncpy(cam_definition_uri,in_cam_definition_uri,140);
uint8_t gimbal_device_id=(uint8_t)num();
uint8_t camera_device_id=(uint8_t)num();
mavlink_msg_camera_information_pack_status(sys,comp,&st,&msg,time_boot_ms,vendor_name,model_name,firmware_version,focal_length,sensor_size_h,sensor_size_v,resolution_h,resolution_v,lens_id,flags,cam_definition_version,cam_definition_uri,gimbal_device_id,camera_device_id);break;}
case 260:{
uint32_t time_boot_ms=(uint32_t)num();
uint8_t mode_id=(uint8_t)num();
float zoomLevel=(float)num();
float focusLevel=(float)num();
uint8_t camera_device_id=(uint8_t)num();
mavlink_msg_camera_settings_pack_status(sys,comp,&st,&msg,time_boot_ms,mode_id,zoomLevel,focusLevel,camera_device_id);break;}
case 262:{
uint32_t time_boot_ms=(uint32_t)num();
uint8_t image_status=(uint8_t)num();
uint8_t video_status=(uint8_t)num();
float image_interval=(float)num();
uint32_t recording_time_ms=(uint32_t)num();
float available_capacity=(float)num();
int32_t image_count=(int32_t)num();
uint8_t camera_device_id=(uint8_t)num();
mavlink_msg_camera_capture_status_pack_status(sys,comp,&st,&msg,time_boot_ms,image_status,video_status,image_interval,recording_time_ms,available_capacity,image_count,camera_device_id);break;}
case 263:{
uint32_t time_boot_ms=(uint32_t)num();
uint64_t time_utc=(uint64_t)wide();
uint8_t camera_id=(uint8_t)num();
int32_t lat=(int32_t)num();
int32_t lon=(int32_t)num();
int32_t alt=(int32_t)num();
int32_t relative_alt=(int32_t)num();
float q[4]={0};
for(int i=0;i<4;i++)q[i]=(float)num();
int32_t image_index=(int32_t)num();
int8_t capture_result=(int8_t)num();
char file_url[205]={0};
char in_file_url[512];if(scanf("%511s",in_file_url)!=1)return 2;if(strcmp(in_file_url,"_")!=0)strncpy(file_url,in_file_url,205);
mavlink_msg_camera_image_captured_pack_status(sys,comp,&st,&msg,time_boot_ms,time_utc,camera_id,lat,lon,alt,relative_alt,q,image_index,capture_result,file_url);break;}
case 269:{
uint8_t stream_id=(uint8_t)num();
uint8_t count=(uint8_t)num();
uint8_t type=(uint8_t)num();
uint16_t flags=(uint16_t)num();
float framerate=(float)num();
uint16_t resolution_h=(uint16_t)num();
uint16_t resolution_v=(uint16_t)num();
uint32_t bitrate=(uint32_t)num();
uint16_t rotation=(uint16_t)num();
uint16_t hfov=(uint16_t)num();
char name[32]={0};
char in_name[512];if(scanf("%511s",in_name)!=1)return 2;if(strcmp(in_name,"_")!=0)strncpy(name,in_name,32);
char uri[160]={0};
char in_uri[512];if(scanf("%511s",in_uri)!=1)return 2;if(strcmp(in_uri,"_")!=0)strncpy(uri,in_uri,160);
uint8_t encoding=(uint8_t)num();
uint8_t camera_device_id=(uint8_t)num();
uint16_t vfov=(uint16_t)num();
mavlink_msg_video_stream_information_pack_status(sys,comp,&st,&msg,stream_id,count,type,flags,framerate,resolution_h,resolution_v,bitrate,rotation,hfov,name,uri,encoding,camera_device_id,vfov);break;}
case 270:{
uint8_t stream_id=(uint8_t)num();
uint16_t flags=(uint16_t)num();
float framerate=(float)num();
uint16_t resolution_h=(uint16_t)num();
uint16_t resolution_v=(uint16_t)num();
uint32_t bitrate=(uint32_t)num();
uint16_t rotation=(uint16_t)num();
uint16_t hfov=(uint16_t)num();
uint8_t camera_device_id=(uint8_t)num();
uint16_t vfov=(uint16_t)num();
mavlink_msg_video_stream_status_pack_status(sys,comp,&st,&msg,stream_id,flags,framerate,resolution_h,resolution_v,bitrate,rotation,hfov,camera_device_id,vfov);break;}
case 280:{
uint32_t time_boot_ms=(uint32_t)num();
uint32_t cap_flags=(uint32_t)num();
uint8_t gimbal_device_id=(uint8_t)num();
float roll_min=(float)num();
float roll_max=(float)num();
float pitch_min=(float)num();
float pitch_max=(float)num();
float yaw_min=(float)num();
float yaw_max=(float)num();
mavlink_msg_gimbal_manager_information_pack_status(sys,comp,&st,&msg,time_boot_ms,cap_flags,gimbal_device_id,roll_min,roll_max,pitch_min,pitch_max,yaw_min,yaw_max);break;}
case 281:{
uint32_t time_boot_ms=(uint32_t)num();
uint32_t flags=(uint32_t)num();
uint8_t gimbal_device_id=(uint8_t)num();
uint8_t primary_control_sysid=(uint8_t)num();
uint8_t primary_control_compid=(uint8_t)num();
uint8_t secondary_control_sysid=(uint8_t)num();
uint8_t secondary_control_compid=(uint8_t)num();
mavlink_msg_gimbal_manager_status_pack_status(sys,comp,&st,&msg,time_boot_ms,flags,gimbal_device_id,primary_control_sysid,primary_control_compid,secondary_control_sysid,secondary_control_compid);break;}
case 285:{
uint8_t target_system=(uint8_t)num();
uint8_t target_component=(uint8_t)num();
uint32_t time_boot_ms=(uint32_t)num();
uint16_t flags=(uint16_t)num();
float q[4]={0};
for(int i=0;i<4;i++)q[i]=(float)num();
float angular_velocity_x=(float)num();
float angular_velocity_y=(float)num();
float angular_velocity_z=(float)num();
uint32_t failure_flags=(uint32_t)num();
float delta_yaw=(float)num();
float delta_yaw_velocity=(float)num();
uint8_t gimbal_device_id=(uint8_t)num();
mavlink_msg_gimbal_device_attitude_status_pack_status(sys,comp,&st,&msg,target_system,target_component,time_boot_ms,flags,q,angular_velocity_x,angular_velocity_y,angular_velocity_z,failure_flags,delta_yaw,delta_yaw_velocity,gimbal_device_id);break;}
case 287:{
uint8_t target_system=(uint8_t)num();
uint8_t target_component=(uint8_t)num();
uint32_t flags=(uint32_t)num();
uint8_t gimbal_device_id=(uint8_t)num();
float pitch=(float)num();
float yaw=(float)num();
float pitch_rate=(float)num();
float yaw_rate=(float)num();
mavlink_msg_gimbal_manager_set_pitchyaw_pack_status(sys,comp,&st,&msg,target_system,target_component,flags,gimbal_device_id,pitch,yaw,pitch_rate,yaw_rate);break;}
default:return 2;}uint8_t b[280];unsigned n=mavlink_msg_to_send_buffer(b,&msg);for(unsigned i=0;i<n;i++)printf("%02x",b[i]);puts("");return 0;}
