#include <stdio.h>
#include "ardupilotmega/mavlink.h"
int main(void) {
    const uint16_t c[][8]={{1500,1500,1500,1500,65535,65535,65535,65535},
      {1800,1200,1500,1600,65535,65535,65535,65535},{0,0,0,0,65535,65535,65535,65535}};
    for (int i=0;i<3;i++) {
        mavlink_message_t msg;
        mavlink_get_channel_status(MAVLINK_COMM_0)->current_tx_seq=9;
        mavlink_msg_rc_channels_override_pack(255,190,&msg,42,1,c[i][0],c[i][1],c[i][2],c[i][3],
          c[i][4],c[i][5],c[i][6],c[i][7],0,0,0,0,0,0,0,0,0,0);
        uint8_t bytes[MAVLINK_MAX_PACKET_LEN];
        int length=mavlink_msg_to_send_buffer(bytes,&msg);
        for (int j=0;j<length;j++) printf("%02x",bytes[j]);
        puts("");
    }
}
