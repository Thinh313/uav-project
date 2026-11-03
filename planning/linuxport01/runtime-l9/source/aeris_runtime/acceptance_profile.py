"""Source-bound dwell profiles; new760 records600s plus original160s allowance."""
def assisted_contract(maximum_seconds):
 if type(maximum_seconds)is not int or maximum_seconds not in(180,760,1960):raise ValueError('RECORDING_PROFILE180_760_OR1960')
 minimum,target={180:(5,5),760:(600,602),1960:(1800,1802)}[maximum_seconds]
 return {'format':'aeris-pipeline06-assisted-dwell','version':1,'recordingMaximumSeconds':maximum_seconds,'minimumObservedNs':minimum*1_000_000_000,'dwellTargetNs':target*1_000_000_000,'setupLandingAndClosureAdditional':True,'originalSafetyAndCaseBudgetUnchanged':maximum_seconds!=760,'originalSafetyGuardsUnchanged':True}
