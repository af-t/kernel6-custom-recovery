#
# Copyright (C) 2022 The LineageOS Project
# Copyright (C) 2024 OrangeFox Recovery Project
#
# SPDX-License-Identifier: Apache-2.0
#

DEVICE_PATH := device/infinix/X6885

# Bootloader
TARGET_BOOTLOADER_BOARD_NAME := X6885

include device/infinix/mt6789-common/BoardConfigCommon.mk

# Init
TARGET_INIT_VENDOR_LIB := libinit_Infinix-X6885
TARGET_RECOVERY_DEVICE_MODULES += libinit_Infinix-X6885

# Assert
TARGET_OTA_ASSERT_DEVICE := X6885

# Display - LCD 1080x2400 (stock density 420; pixel format is the stock value
# for this panel, Il103's RGBX is X6886-specific)
TARGET_RECOVERY_PIXEL_FORMAT := BGRA_8888
OF_SCREEN_H := 2400

# Device version
TW_DEVICE_VERSION := X6885
