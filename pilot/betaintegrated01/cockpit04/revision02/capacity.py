"""Single combined case external policy. Runtime physical/guard policies unchanged."""
from pilot.betaintegrated01.cockpit04.capacity import journal_policy as accepted_journal_policy,transport_policy as accepted_transport_policy
from pilot.betaintegrated01.runtime02.journal.admission import DISK_POLICY
GIB=2**30
MIB=2**20
SCENARIO='M1_COCKPIT04_BRAKE_ASSIST_1802_THEN_NATIVE_LINK_CUT'


def duration(seconds):
    if type(seconds)is not int or seconds!=1960:raise ValueError('ONE_COMBINED_1960_ONLY')
    return seconds


def journal_policy(seconds):
    return accepted_journal_policy(duration(seconds))


def transport_policy(seconds):
    return accepted_transport_policy(duration(seconds))


def task_budget(free_bytes=None):
    if free_bytes is not None and(type(free_bytes)is not int or free_bytes<0):raise ValueError('ACTUAL_FREE_BYTES')
    categories={'hostMainJournalQuota':6*GIB,'APRawSingleCase':1960*1200*10*64+10*64,
      'APHeadersSealsTermination':16*MIB,'transportSingleCase':256*MIB,
      'nativeAVDAllocatedGrowth':512*MIB,'nativeExportGlobalHardCeiling':192*MIB,
      'metadataCheckpointsLogsAPK':64*MIB,'retainedUnit':128*MIB}
    peak=sum(categories.values());required=max(DISK_POLICY['entryBytes'],peak+DISK_POLICY['floorBytes']+DISK_POLICY['reserveBytes'])
    assert peak<10*GIB
    return {'format':'aeris-cockpit04-combined-single-original-capacity','version':2,
      'scenario':SCENARIO,'maximumSeconds':1960,'nativeMaximumSeconds':2000,
      'caseCount':1,'APStarts':1,'shortSmokeAndHeldForwardLossCases':'DEFERRED_NOT_CLAIMED',
      'categories':categories,'taskHardPeakBytes':peak,'taskHardCeilingBytes':10*GIB,
      'requiredFreeBytes':required,'entryBytes':DISK_POLICY['entryBytes'],
      'floorBytes':DISK_POLICY['floorBytes'],'reserveBytes':DISK_POLICY['reserveBytes'],
      'admitted':None if free_bytes is None else free_bytes>=required,
      'perCaseFreshEntry20Required':True,'initialAdmissionDoesNotAdmitFutureCases':True,
      'hostRawCopies':1,'hostRawDuplicateOrExport':False,'coldVerification':'READ_ONLY_IN_PLACE',
      'nativeJournalHardQuotaBytes':160*MIB,'nativeTarAndSingleExportCapBytes':168*MIB,
      'nativeExportGlobalHardCeilingBytes':192*MIB,
      'AVDAllocatedGrowthParts':{'nativeOriginal':160*MIB,'systemOther':352*MIB},
      'profileConfig02AndTyped39BitsUnchanged':True,
      'profile02TaskBudgetSupersededOnlyByThisExternalResourcePolicy':True,
      'maximumFormatDurationGuaranteed':False,'quotaMayFailPreservingPrefix':True,
      'externalEnforcementRequired':['Root currentallocateddelta/caseledger','ONEselectedrunexport<=168MiB and cumulative<=192MiB','AVDpositiveallocatedgrowth<=512MiB','metadata64MiB/unit128MiB'],
      'planningEstimateOnly':'QA observed81709bytes/1.051s=~77739B/s=75.9KiB/s;1802s~133.6MiB beforewarmup.160MiB is finite margin not guaranteed1960s; host~5.40GiB estimate below6GiB not format guarantee',
      'combinedAcceptance':'Separate new scenario: manual thenUP/BRAKE/neutralrelease/newlease;freshBRAKEairborne+neutrallease1802s thennativecut;notheldforwardatcut/no userLAND; independent rawclock+authority+ground required'}
