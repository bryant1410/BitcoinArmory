package=pyqt4
$(package)_version=4.11.3
$(package)_download_path=http://sourceforge.net/projects/pyqt/files/PyQt4/PyQt-$($(package)_version)
# Set $(package)_file_name to that of Linux to get this working for now
$(package)_file_name=PyQt-x11-gpl-$($(package)_version).tar.gz
$(package)_linux_file_name=PyQt-x11-gpl-$($(package)_version).tar.gz
$(package)_darwin_file_name=PyQt-mac-gpl-$($(package)_version).tar.gz
$(package)_mingw32_file_name=PyQt-win-gpl-$($(package)_version).zip
# Set $(package)_sha256_hash to that of Linux to get this working for now
$(package)_sha256_hash=853780dcdbe2e6ba785d703d059b096e1fc49369d3e8d41a060be874b8745686
$(package)_linux_sha256_hash=853780dcdbe2e6ba785d703d059b096e1fc49369d3e8d41a060be874b8745686
$(package)_darwin_sha256_hash=8b8bb3a2ef8b7368710e0bc59d6e94e1f513f7dbf10a3aaa3154f7b848c88b4d
$(package)_mingw32_sha256_hash=aa25a2e11464fd2ff26e1a3ad514aae6d89a61bb03ce4746d255a82cf909225d
$(package)_dependencies=python2 qt48 sip

define $(package)_config_cmds
  export QTDIR=$($(package)_prefix) && \
  export PATH="$($(package)_prefixbin):${PATH}" && \
  $($(package)_prefixbin)/python configure-ng.py --confirm-license --qmake $($(package)_prefix)/native/bin/qmake --sip-incdir $($(package)_prefix)/include/python2.7/ --bindir=$($(package)_staging_prefix_dir)/bin --static
endef

define $(package)_build_cmds
  $(MAKE)
endef

define $(package)_stage_cmds
  $(MAKE) install
endef
