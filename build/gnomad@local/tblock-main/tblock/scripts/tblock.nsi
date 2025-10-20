!include "MUI2.nsh"
!include "LogicLib.nsh"
!include "WinVer.nsh"
!include "x64.nsh"

!define PRODUCT_NAME "TBlock"
!define PRODUCT_DESCRIPTION "An anticapitalist ad-blocker that uses the hosts file"
!define COPYRIGHT "Copyright (c) 2021-2023 Twann"
!define PRODUCT_VERSION "2.6.1"
!define SETUP_VERSION 2.6.1

Name "TBlock"
OutFile "tblock_setup_${PRODUCT_VERSION}.exe"
InstallDir "$PROGRAMFILES\TBlock"
RequestExecutionLevel admin

VIProductVersion "${PRODUCT_VERSION}.1"
VIAddVersionKey "ProductName" "${PRODUCT_NAME}"
VIAddVersionKey "ProductVersion" "${PRODUCT_VERSION}"
VIAddVersionKey "FileDescription" "${PRODUCT_DESCRIPTION}"
VIAddVersionKey "LegalCopyright" "${COPYRIGHT}"
VIAddVersionKey "FileVersion" "${SETUP_VERSION}"

!define MUI_ICON "assets\icons\tblock.ico"
!define MUI_HEADERIMAGE
;!define MUI_HEADERIMAGE_BITMAP "header.bmp"
;!define MUI_WELCOMEFINISHPAGE_BITMAP "wizard.bmp"
!define MUI_FINISHPAGE_NOAUTOCLOSE

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "LICENSE"
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

Section "!tblock" Section1
	SetOutPath "$INSTDIR"
	File "tblock.exe"
	WriteUninstaller "$INSTDIR\uninstall-tblock.exe"
	ExecWait 'setx PATH "%PATH%;$INSTDIR"'
SectionEnd
Section "tblockc" Section2
	SetOutPath "$INSTDIR"
	File "tblockc.exe"
	WriteUninstaller "$INSTDIR\uninstall-tblock.exe"
	ExecWait 'setx PATH "%PATH%;$INSTDIR"'
SectionEnd
Section "tblockd" Section3
	SetOutPath "$INSTDIR"
	File "tblockd.exe"
	WriteUninstaller "$INSTDIR\uninstall-tblock.exe"
	ExecWait 'setx PATH "%PATH%;$INSTDIR"'
	;ExecWait 'powershell -Command "New-Service -Name tblockd -BinaryPathName $INSTDIR\tblockd.exe"'
SectionEnd

!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
!insertmacro MUI_DESCRIPTION_TEXT ${Section1} "Install the ad-blocker itself"
!insertmacro MUI_DESCRIPTION_TEXT ${Section2} "Install the built-in filter list converter"
!insertmacro MUI_DESCRIPTION_TEXT ${Section3} "Install the built-in daemon"
!insertmacro MUI_FUNCTION_DESCRIPTION_END

Section "Uninstall"
	Delete "$INSTDIR\tblock.exe"
	Delete "$INSTDIR\tblockc.exe"
	Delete "$INSTDIR\tblockd.exe"
	Delete "$INSTDIR\uninstall-tblock.exe"
	;ExecWait 'powershell -Command "Remove-Service -Name "tblockd"'
	;ExecWait 'sc delete "tblock"'
SectionEnd

!insertmacro MUI_LANGUAGE "English"
