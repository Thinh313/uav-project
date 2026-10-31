"""New single-original workflow; finite quotas, conditional completion, no old gate waiver."""
from pilot.betaintegrated01.runtime02.journal import Policy
from pilot.betaintegrated01.runtime02.journal.admission import DISK_POLICY
GIB=2**30
MIB=2**20
DURATIONS=(60,90,1960)


def duration(value):
    if type(value)is not int or value not in DURATIONS:raise ValueError('COCKPIT04_DURATION_ALLOWLIST')
    return value


def journal_policy(seconds):
    duration(seconds)
    return Policy(segment_bytes=(16 if seconds==1960 else 8)*MIB,
                  quota_bytes=6*GIB if seconds==1960 else 384*MIB,
                  max_record_bytes=2048,max_segments=448 if seconds==1960 else 64,
                  termination_reserve_bytes=16384)


def transport_policy(seconds):
    duration(seconds)
    return Policy(segment_bytes=MIB,quota_bytes=(256 if seconds==1960 else 32)*MIB,
                  max_record_bytes=16384,max_segments=320 if seconds==1960 else 40,
                  termination_reserve_bytes=32768)


def task_budget(free_bytes=None):
    categories={'hostMainJournalQuota':6*GIB,'hostSmokeLossJournalQuotas':2*384*MIB,
      'APRawAllCases':(1960+90+90)*1200*10*64+3*10*64,'APHeadersSealsTermination':16*MIB,
      'transportAllCases':(256+32+32)*MIB,'nativeAVDAllocatedGrowth':512*MIB,
      'nativeExportsAllCases':192*MIB,'metadataCheckpointsLogsAPK':64*MIB,'retainedUnit':128*MIB}
    peak=sum(categories.values())
    assert peak<9.5*GIB and peak<=10*GIB
    required=max(DISK_POLICY['entryBytes'],peak+DISK_POLICY['floorBytes']+DISK_POLICY['reserveBytes'])
    if free_bytes is not None and(type(free_bytes)is not int or free_bytes<0):raise ValueError('ACTUAL_FREE_BYTES')
    return {'format':'aeris-cockpit04-single-original-capacity','version':1,'categories':categories,
            'taskHardPeakBytes':peak,'taskHardCeilingBytes':10*GIB,'requiredFreeBytes':required,
            'entryBytes':DISK_POLICY['entryBytes'],'floorBytes':DISK_POLICY['floorBytes'],
            'reserveBytes':DISK_POLICY['reserveBytes'],'admitted':None if free_bytes is None else free_bytes>=required,
            'perCaseFreshEntry20Required':True,'caseOrder':['smoke90','loss90','nativeRestartRecovery','long1960_LAST'],
            'initialAdmissionDoesNotAdmitFutureCases':True,'hostRawCopies':1,'hostRawDuplicateOrExport':False,'coldVerification':'READ_ONLY_IN_PLACE',
            'maximumFormatDurationGuaranteed':False,'quotaMayFailPreservingPrefix':True,
            'nativeExportCapsBytes':{'smoke':28*MIB,'long':136*MIB,'loss':28*MIB},
            'externalEnforcementRequired':['Root totalallocateddelta/caseledger','Nativeexportcumulative192MiB','AVDpositiveallocatedgrowth512MiB','metadata64MiB/unit128MiB'],
            'planningEstimateOnly':'73s~2.96MB/s hostjournal implies~5.40GiB at1960s; not a hard bound or acceptance'}
