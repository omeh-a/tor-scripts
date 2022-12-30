# Makefile for Buildroot to grab. To build this yourself, just use the one in /src
# Based off of https://github.com/cirosantilli/buildroot/tree/out-of-tree-2016.05

TESTERWAIT_VERSION = 1.0
TESTERWAIT_SITE = ~/tor-scripts/tester_wait/src
TESTERWAIT_SITE_METHOD = local

define TESTERWAIT_BUILD_CMDS
	$(MAKE) CC="$(TARGET_CC)" LD="$(TARGET_LD)" -C $(@D)
endef

define TESTERWAIT_INSTALL_TARGET_CMDS
	$(INSTALL) -D -m 0755 $(@D)/tester_wait $(TARGET_DIR)/usr/bin
endef

$(eval $(generic-package))