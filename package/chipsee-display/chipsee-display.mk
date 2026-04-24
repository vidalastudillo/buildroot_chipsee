################################################################################
#
# chipsee-display
#
################################################################################

CHIPSEE_DISPLAY_VERSION = 1.0
CHIPSEE_DISPLAY_SITE = $(BR2_EXTERNAL_CHIPSEE_BR_PATH)/package/chipsee-display
CHIPSEE_DISPLAY_SITE_METHOD = local
CHIPSEE_DISPLAY_DEPENDENCIES = host-python3

ifeq ($(BR2_PACKAGE_CHIPSEE_DISPLAY_CS10600RA4070),y)
CHIPSEE_DISPLAY_EDID_PROFILE = cs10600ra4070
else ifeq ($(BR2_PACKAGE_CHIPSEE_DISPLAY_CS12800RA4101),y)
CHIPSEE_DISPLAY_EDID_PROFILE = cs12800ra4101
endif

define CHIPSEE_DISPLAY_BUILD_CMDS
	$(TARGET_CC) $(TARGET_CFLAGS) $(TARGET_LDFLAGS) \
		-o $(@D)/broadcast-rgb $(@D)/broadcast-rgb.c
	$(HOST_DIR)/bin/python3 \
		$(BR2_EXTERNAL_CHIPSEE_BR_PATH)/board/gen_edid.py \
		$(CHIPSEE_DISPLAY_EDID_PROFILE) \
		--output $(@D)/edid_$(CHIPSEE_DISPLAY_EDID_PROFILE).bin
endef

define CHIPSEE_DISPLAY_INSTALL_TARGET_CMDS
	$(INSTALL) -D -m 0755 $(@D)/broadcast-rgb \
		$(TARGET_DIR)/usr/bin/broadcast-rgb
	$(INSTALL) -D -m 0644 \
		$(@D)/edid_$(CHIPSEE_DISPLAY_EDID_PROFILE).bin \
		$(TARGET_DIR)/lib/firmware/edid_$(CHIPSEE_DISPLAY_EDID_PROFILE).bin
endef

define CHIPSEE_DISPLAY_INSTALL_INIT_SYSV
	$(INSTALL) -D -m 0755 \
		$(BR2_EXTERNAL_CHIPSEE_BR_PATH)/package/chipsee-display/S20broadcast_rgb \
		$(TARGET_DIR)/etc/init.d/S20broadcast_rgb
endef

$(eval $(generic-package))
