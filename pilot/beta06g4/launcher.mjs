/** Earlier local lifetime bound; parent Python monotonic window remains primary. */
export function validateRootLauncher({controllerPid,remainingMs},actualParentPid){
 if(!Number.isSafeInteger(controllerPid)||controllerPid<=1||controllerPid!==actualParentPid)throw Error('EXACT_ROOT_CONTROLLER_PARENT_REQUIRED');
 if(!Number.isSafeInteger(remainingMs)||remainingMs<=0||remainingMs>2700000)throw Error('PARENT_REMAINING_DURATION_BOUND');
 return{controllerPid,remainingMs,primaryDeadline:'ORIGINAL_PARENT_PYTHON_MONOTONIC_WINDOW_NO_REANCHOR'};
}
export function launcherFromEnv(env,actualParentPid){
 const p=env.BETA06_ROOT_CONTROLLER_PID,t=env.BETA06_PARENT_HOST_REMAINING_MS;
 if(!/^[1-9][0-9]{0,9}$/.test(p??'')||!/^[1-9][0-9]{0,9}$/.test(t??''))throw Error('ROOT_LIFETIME_ENV_REQUIRED');
 return validateRootLauncher({controllerPid:Number(p),remainingMs:Number(t)},actualParentPid);
}
