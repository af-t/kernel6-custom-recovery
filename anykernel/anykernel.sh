### AnyKernel3 - kernel6-custom-recovery (__VARIANT__)
## Flashes a complete prebuilt vendor_boot image, no on-device repack.

### AnyKernel setup
properties() { '
kernel.string=kernel6-custom-recovery __VARIANT__
do.devicecheck=1
do.modules=0
do.systemless=0
do.cleanup=1
do.cleanuponabort=0
device.name1=__DEVICE_A__
device.name2=__DEVICE_B__
supported.versions=
supported.patchlevels=
supported.vendorpatchlevels=
'; } # end properties


### AnyKernel install
BLOCK=vendor_boot;
IS_SLOT_DEVICE=1;
PATCH_VBMETA_FLAG=auto;

# import functions/variables and setup - see for reference (DO NOT REMOVE)
. tools/ak3-core.sh;

ui_print "Flashing vendor_boot (__VARIANT__) to $BLOCK...";
dd if=$AKHOME/vendor_boot.img of=$BLOCK bs=4096;
ui_print "Done. Requires vbmeta verification disabled (Magisk/KSU root implies it).";
## end install
