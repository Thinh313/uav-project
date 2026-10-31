"""Explicit entry10 amendment; no resource/floor/forecast/runtime bypass."""
from importlib import import_module
from pilot.betaintegrated01.cockpit04.revision02.capacity import task_budget as frozen_budget
_admission=import_module('planning.betaintegrated01.cockpit05-entry10.host.admission')
GIB=2**30
MIB=2**20


def task_budget(free_bytes=None):
    if free_bytes is not None and(type(free_bytes)is not int or not 0<=free_bytes<2**63):raise ValueError('ACTUAL_FREE_BYTES_INTEGER')
    old=frozen_budget();peak=old['taskHardPeakBytes'];required=max(10*GIB,peak+10*GIB+256*MIB)
    reasons=[]
    if free_bytes is not None:
        if free_bytes<10*GIB:reasons.append('USER_ENTRY_BELOW10_GIB')
        if free_bytes<10*GIB+256*MIB:reasons.append('LIVE_FLOOR10_GIB_PLUS256_MIB_RESERVE')
        if free_bytes<required:reasons.append('WHOLE1960S_CASE_QUOTA_PLUS_FLOOR_RESERVE_DOES_NOT_FIT')
    return {**old,'format':'aeris-cockpit05-explicit-entry10-wholecase-capacity','version':3,
      'entryBytes':10*GIB,'requiredFreeBytes':required,'admitted':None if free_bytes is None else not reasons,
      'actualFreeBytes':free_bytes,'refusalReasons':reasons,'perCaseFreshEntry20Required':False,
      'perCaseFreshEntry10Required':True,'floorAndReserveBytes':10*GIB+256*MIB,
      'selectedRuntimeMigration':'NOT_WIRED; existing frozen runtime continues entry20 until isolated derivative selected',
      'entryAloneAdmitsWholeCase':False,'floorForecastRealPrimeUnchanged':True,
      'guardPolicy':dict(_admission.DISK_POLICY),'runtimeLaunched':False,
      'policyScope':'NEW_TEST_POLICY_AND_ISOLATED_GUARD_DERIVATIVE_ONLY_NOT_ACTUAL_RUNTIME_ACCEPTANCE'}


def ui_budget(free_bytes=None):
    if free_bytes is not None and(type(free_bytes)is not int or not 0<=free_bytes<2**63):raise ValueError('ACTUAL_FREE_BYTES_INTEGER')
    # Conservative decimal-GiB metadata/other buckets are larger than 32MiB.
    floor=10*GIB;reserve=256*MIB;avd=512*MIB;metadata=32*GIB//1000;other=GIB//10
    peak=avd+metadata+other;required=max(10*GIB,floor+reserve+peak)
    return {'format':'aeris-cockpit05-entry10-ui-only-capacity','version':1,'entryBytes':10*GIB,
      'floorBytes':floor,'reserveBytes':reserve,'AVDPositiveAllocatedGrowthBytes':avd,
      'metadataAllocatedCapBytes':32*MIB,'metadataBudgetConservativeBytes':metadata,'otherBudgetBytes':other,
      'taskHardPeakBytes':peak,'requiredFreeBytes':required,'actualFreeBytes':free_bytes,
      'admitted':None if free_bytes is None else free_bytes>=required,'maximumSeconds':900,
      'APOrFlightAuthorizedByThisBudget':False,'refusalReason':None if free_bytes is None or free_bytes>=required else'UI_WHOLEBUDGET_PLUS_FLOOR_RESERVE_DOES_NOT_FIT'}
