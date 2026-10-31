import copy
import math
import unittest
from engine import advance, contact, digest, forward, replay, seal, speed_envelope
from corpus import context, sensor, policy_fixture, pwm_fixture


class Contracts(unittest.TestCase):
    def trace(self):
        h = {'version':1,'assurance':'MOCK_ONLY','units':'SI','world':'NED','body':'FRD',
             'datum':'VIRTUAL_HOME_NED_METRES','clock':'MOCK_MONOTONIC_S',
             'target':'42/1','session':'s75','boot':'b75',
             'profileSha256':'a'*64,'modelSha256':'b'*64,'sceneSha256':'c'*64}
        samples = [{'t':i*.02,'target':'42/1','session':'s75','boot':'b75',
                    'position':[0,0,-5],'velocity':[0,0,0],'quaternion':[1,0,0,0],'kind':'MODEL_STATE'} for i in range(3)]
        return h,seal(h,samples)

    def test_positive(self):
        h,t = self.trace(); self.assertEqual(replay(t,t['head'],h)['frames'],3)

    def test_ack_cannot_be_execution(self):
        h,t = self.trace(); t['rows'][0]['sample']['kind']='COMMAND_ACK'
        bad=seal(h,[r['sample'] for r in t['rows']])
        with self.assertRaisesRegex(ValueError,'ACK_NOT'):replay(bad,bad['head'],h)

    def test_datum_rejected_even_resealed(self):
        for key,value in [('units','feet'),('world','ENU'),('body','FLU'),('datum','AMSL'),('clock','UNIX_SECONDS'),('version',2),('assurance','HERA_VALIDATED')]:
            with self.subTest(key=key):
                h,t=self.trace();h[key]=value;bad=seal(h,[r['sample'] for r in t['rows']])
                with self.assertRaises(ValueError):replay(bad,bad['head'],h)

    def test_missing_pin(self):
        h,t=self.trace();h['modelSha256']='missing';bad=seal(h,[r['sample'] for r in t['rows']])
        with self.assertRaises(ValueError):replay(bad,bad['head'],h)

    def test_missing_identity(self):
        h,t=self.trace();h['boot']='';bad=seal(h,[r['sample'] for r in t['rows']])
        with self.assertRaises(ValueError):replay(bad,bad['head'],h)

    def test_no_empty_pass(self):
        h,t=self.trace();bad=seal(h,[])
        with self.assertRaises(ValueError):replay(bad,bad['head'],h)

    def test_bool_count_not_integer(self):
        h,t=self.trace();t['count']=True
        with self.assertRaises(ValueError):replay(t,t['head'],h)

    def test_resealed_coordinate_requires_external_digest(self):
        h,t=self.trace();samples=[r['sample'] for r in t['rows']];samples[1]['position'][0]=99
        bad=seal(h,samples)
        with self.assertRaisesRegex(ValueError,'EXPECTED_DIGEST'):replay(bad,t['head'],h)

    def test_invalid_numbers(self):
        for value in [float('nan'),float('inf'),True,'1']:
            with self.subTest(value=str(value)):
                with self.assertRaises(ValueError):contact([value,0,0],[1,0,0],.5,{'kind':'sphere','center':[0,0,0],'radius':1})

    def test_quaternion_invalid(self):
        for q in [[0,0,0,0],[2,0,0,0],[1,0,0],['1',0,0,0]]:
            with self.subTest(q=q):
                with self.assertRaises(ValueError):forward(q)

    def test_quaternion_sign_equivalence(self):
        q=[math.sqrt(.5),0,0,math.sqrt(.5)]
        self.assertEqual(forward(q),forward([-v for v in q]))

    def test_positive_yaw_ned(self):
        q=advance([1,0,0,0],[0,0,math.pi/2],.1)
        self.assertGreater(forward(q)[1],0)

    def test_dt_domain(self):
        for dt in [0,-.01,.11]:
            with self.assertRaises(ValueError):advance([1,0,0,0],[0,0,1],dt)

    def test_unsupported_shape(self):
        with self.assertRaisesRegex(ValueError,'UNSUPPORTED_SHAPE'):contact([0,0,0],[1,0,0],.5,{'kind':'visual-mesh'})

    def test_plane_normal(self):
        with self.assertRaises(ValueError):contact([0,0,0],[1,0,0],.5,{'kind':'plane','normal':[2,0,0],'offset':0})

    def test_radius_domain(self):
        for radius in [0,-1]:
            with self.assertRaises(ValueError):contact([0,0,0],[1,0,0],radius,{'kind':'sphere','center':[2,0,0],'radius':1})

    def test_negative_sensor_distance(self):
        with self.assertRaises(ValueError):speed_envelope(4,sensor()|{'clearanceM':-1},context(),policy_fixture())

    def test_unknown_sensor_is_unavailable_not_stop_evidence(self):
        r=speed_envelope(4,sensor()|{'healthy':False},context(),policy_fixture())
        self.assertEqual(r['status'],'UNAVAILABLE');self.assertNotIn('radialSpeedMps',r);self.assertFalse(r['executed'])

    def test_zero_margin_motion(self):
        r=speed_envelope(4,sensor()|{'clearanceM':1.},context(),policy_fixture())
        self.assertEqual(r['radialSpeedMps'],0)

    def test_cap_stopping_inequality(self):
        for room in [0,.0001,.1,1,10,100]:
            p=policy_fixture();v=speed_envelope(100,sensor()|{'clearanceM':room+p['marginM']},context(),p)['radialSpeedMps']
            self.assertLessEqual(v*p['dt']+v*v/(2*p['decelerationMps2']),room+1e-12)

    def test_missing_sensor_identity(self):
        s=sensor();del s['boot'];r=speed_envelope(4,s,context(),policy_fixture());self.assertEqual(r['status'],'UNAVAILABLE')

    def test_empty_scene_does_not_synthesize_collision(self):
        shape={'kind':'sphere','center':[100,100,100],'radius':1}
        self.assertIsNone(contact([0,0,0],[1,1,1],.5,shape))

    def test_motor_mix_pitch_yaw_not_roll(self):
        # Independent wrench sum using known reference geometry; no model/qa import.
        rotors=[(.5/math.sqrt(2),.5/math.sqrt(2)),(-.5/math.sqrt(2),-.5/math.sqrt(2)),
                (.5/math.sqrt(2),-.5/math.sqrt(2)),(-.5/math.sqrt(2),.5/math.sqrt(2))]
        for pattern,signs in [('coupled-positive',(1,1)),('coupled-negative',(-1,-1)),
                              ('coupled-pitch-positive-yaw-negative',(1,-1)),('coupled-pitch-negative-yaw-positive',(-1,1))]:
            thrust=[22*((p-1000)/1000)**2 for p in pwm_fixture(.6,pattern,0)]
            roll=sum(-y*T for (_,y),T in zip(rotors,thrust))
            pitch=sum(x*T for (x,_),T in zip(rotors,thrust))
            yaw=.025*sum(s*T for s,T in zip([1,1,-1,-1],thrust))
            self.assertLess(abs(roll),1e-12);self.assertGreater(pitch*signs[0],.01);self.assertGreater(yaw*signs[1],.001)

    def test_old_roll_mix_fails_pitch_requirement(self):
        u=.6;p=.015;y=.015
        thrust=[22*v*v for v in [u+p+y,u-p+y,u-p-y,u+p-y]]
        pitch=.5/math.sqrt(2)*sum(s*T for s,T in zip([1,-1,1,-1],thrust))
        roll=-.5/math.sqrt(2)*sum(s*T for s,T in zip([1,-1,-1,1],thrust))
        self.assertGreater(abs(roll),.1)
        self.assertLess(abs(pitch),abs(roll)*.1) # cross term is small; dominant maneuver is roll


if __name__=='__main__':
    unittest.main(verbosity=2)
