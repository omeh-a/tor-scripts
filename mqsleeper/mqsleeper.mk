# Makefile for Buildroot to grab. To build this yourself, just use the one in /src
# Based off of https://github.com/cirosantilli/buildroot/tree/out-of-tree-2016.05

MQSLEEPER_VERSION = 1.0
MQSLEEPER_SITE = ./package/mqsleeper/src
MQSLEEPER_SITE_METHOD = local

define MQSLEEPER_BUILD_CMDS
	$(MAKE) CC="$(TARGET_CC)" LD="$(TARGET_LD)" -C $(@D)
endef

define MQSLEEPER_INSTALL_TARGET_CMDS
	$(INSTALL) -D -m 0755 $(@D)/mqsleeper $(TARGET_DIR)/usr/bin
endef

$(eval $(generic-package))
