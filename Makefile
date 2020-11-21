SHELL:=/bin/bash
ROOT=$(shell pwd)
NAME=$(shell basename $(ROOT))

ifndef VERBOSE
.SILENT:
endif

OUTDIR=
SYSDIR=sys
SRCDIR=src
RESDIR=res

ifeq ($(OUTPUT),)
	export OUTPUT=$(ROOT)/../Clue-out
endif

ifeq ($(PUBLISH),)
	export PUBLISH=~/AMSD/Web/clue/repos/addons
endif

OUTDIR=$(OUTPUT)/$(NAME)
DISTRO_VER=$(shell xmlstarlet sel -t -v "//addon/@version" $(ROOT)/$(SRCDIR)/addon.xml)
DISTRO_REL=$(shell echo "$(DISTRO_VER)" | cut -f1 -d".")
DISTRO_MAJ=$(shell echo "$(DISTRO_VER)" | cut -f2 -d".")
DISTRO_MIN=$(shell echo "$(DISTRO_VER)" | cut -f3 -d".")
NEXT_MIN=$(shell python -c "print int($(DISTRO_MIN)) + 1")
NEXT_VER="${DISTRO_REL}.${DISTRO_MAJ}.${NEXT_MIN}"


info:
	echo -e "\tName:         $(NAME)"
	echo -e "\tVersion ID:   $(DISTRO_VER)"
	echo -e "\tPackage File: $(OUTPUT)/targets/$(NAME).zip"


# Deploy resources (sources and/or system files) into the remote test RPi device,
# having Kodi v18* or CLue 2.0 linux OS with all components and packages.
deploy:
ifneq ($(RPIHOST),)
ifeq ($(shell [[ -d $(ROOT)/$(SRCDIR) ]] && echo -n yes),yes)
	/usr/bin/rsync -a -zvh --progress --delete -e ssh $(ROOT)/$(SRCDIR)/ root@$(RPIHOST):/clue/.kodi/addons/$(NAME)
endif
ifeq ($(shell [[ -d $(ROOT)/$(SYSDIR) ]] && echo -n yes),yes)
	/usr/bin/scp -r $(ROOT)/$(SYSDIR)/* root@$(RPIHOST):/clue/
endif
else
	echo "Your remote RPi device should have SSH service enabled, local public SSH key \
	already shared and RPIHOST local variable setted up with the host name or \
	IP address of the RPi device!"
endif


# Run testing process (for source files) for any remote host and location settled up
# using TESTPATH variable. IN case this variable is not set the test can be done
# for RPi host (identified by RPIHOST variable). Variable TESTPATH should have complete
# ssh location format: <user>@HOST/<base path>
test:
ifneq ($(TESTPATH),)
ifeq ($(shell [[ -d $(ROOT)/$(SRCDIR) ]] && echo -n yes),yes)
	/usr/bin/rsync -a -zvh --progress --delete -e ssh $(ROOT)/$(SRCDIR)/ $(TESTPATH)/.kodi/addons/$(NAME)
endif
else
ifneq ($(RPIHOST),)
ifeq ($(shell [[ -d $(ROOT)/$(SRCDIR) ]] && echo -n yes),yes)
	/usr/bin/rsync -a -zvh --progress --delete -e ssh $(ROOT)/$(SRCDIR)/ root@$(RPIHOST):/clue/.kodi/addons/$(NAME)
endif
else
	echo "For testing process you have to set TESTPATH variable to test on any Kodi\
	environment (syncronized over rsync with ssh) or RPIHOST variable to test on a RPi\
	device. Test process suppose to synchronize only sourse files, system files can be\
	tested using 'deploy' target - only on RPi devices!"
endif
endif

# Mark new revision (addon version) in the development copy
version:
	xmlstarlet edit -L -P -u "//addon/@version" -v "$(NEXT_VER)" $(ROOT)/$(SRCDIR)/addon.xml


# Build addon package in deployment format
build:
	mkdir -p $(OUTDIR) $(OUTDIR)/$(TARGETS)
	cp -rf ${SRCDIR}/* $(OUTDIR)/
	cp -rf LICENSE $(OUTDIR)/
	cd $(OUTPUT) && /usr/bin/zip -q -y -r $(NAME).zip $(NAME) && cd $(ROOT)
	mv -f $(OUTPUT)/$(NAME).zip $(OUTPUT)/targets/$(NAME).zip


# Publish the last build in the addon repository
publish:
ifeq ($(shell [[ -f $(OUTPUT)/targets/$(NAME).zip ]] && echo -n yes),yes)
ifneq ($(PUBLISH),)
	# deploy package resources, rebuild repository descriptor
ifeq ($(shell [[ -f $(PUBLISH)/addons.xml ]] && echo -n yes),yes)
	# define location and copy meta files
	$(shell [[ ! -d $(PUBLISH)/$(NAME) ]] && mkdir $(PUBLISH)/$(NAME))
	cp -f $(ROOT)/$(SRCDIR)/addon.xml $(PUBLISH)/$(NAME)/
	$(shell [[ -f $(ROOT)/$(SRCDIR)/icon.png ]] && cp -f  $(ROOT)/$(SRCDIR)/icon.png $(PUBLISH)/$(NAME)/)
	$(shell [[ -f $(ROOT)/$(SRCDIR)/fanart.jpg ]] && cp -f  $(ROOT)/$(SRCDIR)/fanart.jpg $(PUBLISH)/$(NAME)/)
	$(shell [[ -f $(ROOT)/$(SRCDIR)/changelog.txt ]] && cp -f $(ROOT)/$(SRCDIR)/changelog.txt $(PUBLISH)/$(NAME)/)
	cp -f $(OUTPUT)/targets/$(NAME).zip $(PUBLISH)/$(NAME)/$(NAME)-$(DISTRO_VER).zip
	sha256sum $(PUBLISH)/$(NAME)/$(NAME)-$(DISTRO_VER).zip > $(PUBLISH)/$(NAME)/$(NAME)-$(DISTRO_VER).zip.sha256
	python $(PUBLISH)/xmlgen.py
else
	echo "Repository location described by PUBLISH variable is not correct (doesn't \
	contain the expected structure and remote resources)!"
endif
else
	echo "Repository location is not specified in PUBLISH variable. Set it up and try again!"
endif
else
	echo "Repository location is not specified in PUBLISH variable. Set it up and try again!"
endif


# Commit and push updated files into versioning system (GitHUB). The 'message' input
# parameter is required.
gitrev:
ifneq ($(message),)
	git add .
	git commit -m "$(message)"
	git push
else
	@printf "\n* Please specify 'message' parameter!\n\n"
	exit 1
endif



# Create and push a new versioning tag equals with the addon release. The uploaded can be
# done later - manually or through a separate task and thus the tag is transformed into a
# addon release
gitrel:
	git tag "$(DISTRO_VER)"
	git push origin --tags

# Combine git commit and git release tasks into a single one, the only exception is that
# the commit doesn't require a message, if the message exist it will be used, if not a
# standard commit message will be composed using the addon version number
git:
ifeq ($(message),)
	$(MAKE) gitrev -e message="Release $(DISTRO_VER)"
else
	$(MAKE) gitrev
endif
	$(MAKE) gitrel


# Create a complete release: new build, publish it in the repository, update the versioning
release: version build publish git


# Clean-up the release
clean:
	rm -rf $(OUTDIR)


# Clean-up all build distributions, cache and stamps
cleanall:
	rm -rf $(OUTDIR)/* $(OUTDIR)/.stamp $(OUTDIR)/.ccache


# Display the help text
help:
	echo -e "\
\nSYNOPSIS\n\
       make info | deploy | test \n\
       version | build | publish | release \n\
       make gitrev | gittag | version \n\
       make clean | cleanall \n\
       make help \n\
\nDESCRIPTION\n\
    Executes one of the make targets defined through this Makefile flow, according \n\
    to the scope of this project.\n\n\
    info\n\
                  provides main details about current release: package name, version id\n\
                  and package file (should be found after execution of 'build' target)\n\
                  >> this is the default target wihin the CCM process\n\
    deploy\n\
                  deploys addon resources (sources and system files) on a remote test system\n\
                  (RPi device described by RPIHOST variable)\n\
    test\n\
                  runs testing process (for source files) for any remote host and location \n\
                  settled up using TESTPATH variable. In case this variable is not set the \n\
                  test can be done for RPi host (identified by RPIHOST variable).\n\
    version\n\
                  create local new version within local addon descriptor (addon.xml),\n\
                  the new version being the incremented value fo previous version\n\
                  (for the minor version number)\n\
    build\n\
                  build the addon package along to the new version and prepare the release\n\
                  package file within location $(OUTPUT)/targets/$(NAME).zip\n\
    publish\n\
                  install/publish the addon (already built) on the repository file\n\
                  system (it has to be already mounted to the development environment)\n\
    release\n\
                  Build the addon providing new local version, make release and publish it\n\
                  on the Clue repository (already mounted to the local file system). Then\n\
                  the released version is submitted in the versioning system (GitHUB) over a\n\
                  new release tag version\n\
    gitrev\n\
                  Commit the new release changes into versioning repository (GitHub)\n\
    gitrel\n\
                  Create a new release tag into versioning repository (GitHub) using current\n\
                  addon version (defined in the addon descriptor - addon.xml file)\n\
    git\n\
                  Combine git commit and git release targets into a single one, the only exception\n\
                  is that the commit doesn't require a message description; in case the message exist\n\
                  it will be used as such, otherwise a standard commit message will be composed using\n\
                  the addon version number\n\
    clean\n\
                  cleanup the build resources within the output location\n\
    cleanall\n\
                  Clean-up all resources from the output location (related or nor directly\n\
                  connected to the addon build process\n\
    help\n\
                  Shows this text\n\
\n\
    There are couple of system variables that should be be set in order to drive the execution\n\
    of particular tasks:\n\
    PUBLISH\n\
                  Indicates the remote file system mounted to the local development environment,\n\
                  in order to deploy releases in the repository container.\n\
    OUTPUT\n\
                  Describes the local file system location where the build process will be  \n\
                  executed. Default value is '$(ROOT)/../Clue-out'\n\
    RPIHOST\n\
                  Indicates the host name or the IP address of the test system in order to deploy\n\
                  addon resources through deploy or test task. The remote system should have SSH\n\
                  service enabled and active.\n\
    TESTPATH\n\
                  Describes the remote location for testing purposes. It should contain complete \n\
                  ssh location format: <user>@HOST/<base path>\n\
\n\
EXAMPLES\n\
       deploy the entire distribution on a testing environment ('deploy' task is default)\n\
       > make\n\
       > make deploy\n\n\
       build the entire distribution ('build' make task is default)\n\
       > make build\n\n\
       publish new release in the addon repository\n\
       > make publish\n\n\
       make complete addon release: build it, publish it and commit the changes on GitHub\n\
       > make release\n\n\
" | more