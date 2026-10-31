from pathlib import Path
import json,os,shutil
R=Path(__file__).resolve().parents[2];root=R/'.local/field02';avds=root/'avd';avd=avds/'aeris-field02.avd';sdk=R/'.local/native86-android/sdk';image=sdk/'system-images/android-33/default/arm64-v8a'
assert (image/'system.img').is_file() and (sdk/'emulator/emulator').is_file();assert shutil.disk_usage(R).free>=29*2**30,'FIELD02_RUNTIME_HEADROOM';assert not avd.exists(),'NO_AVD_RECREATE_OR_WIPE';avd.mkdir(parents=True);(avds/'aeris-field02.ini').write_text('avd.ini.encoding=UTF-8\npath='+str(avd)+'\ntarget=android-33\n')
(avd/'config.ini').write_text('''avd.ini.encoding=UTF-8
avd.name=aeris-field02
abi.type=arm64-v8a
hw.cpu.arch=arm64
hw.cpu.ncore=2
hw.ramSize=2048
hw.lcd.width=1280
hw.lcd.height=800
hw.lcd.density=160
hw.gpu.enabled=yes
hw.gpu.mode=host
hw.keyboard=yes
hw.camera.back=none
hw.camera.front=none
hw.audioInput=no
hw.sdCard=no
disk.dataPartition.size=2147483648
disk.cachePartition.size=32M
fastboot.forceColdBoot=yes
showDeviceFrame=no
image.sysdir.1='''+str(image)+'\n')
report={'avd':str(avd),'systemImageReadOnlyPath':str(image),'serial':'emulator-5582','ports':[8872,8873],'forecastPhysicalBytes':1024**3,'logicalUserdataBytes':2*1024**3,'freeBytes':shutil.disk_usage(R).free,'noOldAvdMutation':True};(R/'evidence/field02/android-avd-prepare01.json').open('x').write(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
