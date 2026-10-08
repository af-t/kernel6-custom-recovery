#
# Copyright (C) 2022 The LineageOS Project
# Copyright (C) 2024 OrangeFox Recovery Project
#
# SPDX-License-Identifier: Apache-2.0
#

DEVICE_PATH := device/infinix/X6886

# Bootloader
TARGET_BOOTLOADER_BOARD_NAME := X6886

include device/infinix/mt6789-common/BoardConfigCommon.mk

# Init
TARGET_INIT_VENDOR_LIB := libinit_Infinix-X6886
TARGET_RECOVERY_DEVICE_MODULES += libinit_Infinix-X6886

# Assert
TARGET_OTA_ASSERT_DEVICE := X6886

# Display - AMOLED 1224x2720 (Il103-proven values)
TARGET_RECOVERY_PIXEL_FORMAT := RGBX_8888
OF_SCREEN_H := 2720

# Device version
TW_DEVICE_VERSION := X6886
