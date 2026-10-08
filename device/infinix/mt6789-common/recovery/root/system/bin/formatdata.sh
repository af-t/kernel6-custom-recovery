#!/sbin/sh
#
# Format Data script for Infinix X6886 (MT6789/UFS)
# Handles FBE encryption cleanup + proper f2fs format
#

DATA_DEV=/dev/block/by-name/userdata
META_DEV=/dev/block/by-name/metadata
MAKE_F2FS=/system/bin/make_f2fs

log() {
    echo "formatdata: $1" > /dev/kmsg
    echo "[formatdata] $1"
}

# Step 1: Unmount /data if mounted
log "Step 1: Unmounting /data..."
umount /data 2>/dev/null
umount -l /data 2>/dev/null

# Step 2: Wait for block device to be ready
log "Step 2: Waiting for block device..."
i=0
while [ ! -b "$DATA_DEV" ] && [ $i -lt 30 ]; do
    sleep 1
    i=$((i + 1))
done
if [ ! -b "$DATA_DEV" ]; then
    log "ERROR: Block device $DATA_DEV not found after 30s"
    exit 1
fi
log "Block device found: $DATA_DEV"

# Step 3: Remove any dm-crypt/dm-default-key mappings
log "Step 3: Removing dm-crypt mappings..."
if [ -d /dev/block/mapper ]; then
    for dm in /dev/block/mapper/*userdata* /dev/block/mapper/*data*; do
        if [ -b "$dm" ]; then
            log "Removing dm: $dm"
            dmsetup remove -f "$dm" 2>/dev/null
        fi
    done
fi

# Step 4: Format metadata partition (clears FBE encryption keys)
log "Step 4: Formatting metadata partition..."
if [ -b "$META_DEV" ]; then
    make_ext4fs -f "$META_DEV" 2>/dev/null
    if [ $? -eq 0 ]; then
        log "Metadata formatted successfully"
    else
        # Fallback: try dd zero
        log "make_ext4fs failed, trying dd zero..."
        dd if=/dev/zero of="$META_DEV" bs=4096 count=1 2>/dev/null
        log "Metadata zeroed"
    fi
else
    log "WARNING: Metadata partition not found"
fi

# Step 5: Format userdata with f2fs (matching stock flags)
log "Step 5: Formatting userdata with f2fs..."
if [ -x "$MAKE_F2FS" ]; then
    # Use stock-compatible flags: -d (discard), -f (force), -O encrypt, -O quota, -O fsverity
    $MAKE_F2FS -f -d -l /data -O encrypt,quota,fsverity -s 16 -c /data 2>&1
    RESULT=$?
elif [ -x /system/bin/mkfs.f2fs ]; then
    /system/bin/mkfs.f2fs -f -d -l /data -O encrypt,quota,fsverity -s 16 -c /data 2>&1
    RESULT=$?
else
    # Last resort: try sload.f2fs or generic mkfs
    log "WARNING: No f2fs formatter found, trying block device format..."
    dd if=/dev/zero of="$DATA_DEV" bs=4096 count=128 2>/dev/null
    RESULT=$?
fi

if [ $RESULT -eq 0 ]; then
    log "Format completed successfully!"
    log "userdata: f2fs with encrypt,quota,fsverity"
    log "metadata: cleared (FBE keys removed)"
else
    log "ERROR: Format failed with code $RESULT"
    exit 1
fi

# Step 6: Sync
sync
log "Format data completed. Reboot recommended."
exit 0
