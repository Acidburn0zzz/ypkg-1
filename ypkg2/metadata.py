#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  This file is part of ypkg2
#
#  Copyright 2015-2016 Ikey Doherty <ikey@solus-project.com>

#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

from . import console_ui

import os
import pisi.util
import pisi.metadata
import pisi.specfile
import pisi.package
import stat
from collections import OrderedDict

FileTypes = OrderedDict([
    ("/usr/lib/pkgconfig", "data"),
    ("/usr/lib64/pkgconfig", "data"),
    ("/usr/lib32/pkgconfig", "data"),
    ("/usr/lib", "library"),
    ("/usr/share/info", "info"),
    ("/usr/share/man", "man"),
    ("/usr/share/doc", "doc"),
    ("/usr/share/gtk-doc", "doc"),
    ("/usr/share/locale", "localedata"),
    ("/usr/include", "header"),
    ("/usr/bin", "executable"),
    ("/bin", "executable"),
    ("/usr/sbin", "executable"),
    ("/sbin", "executable"),
    ("/etc", "config"),
])


def get_file_type(t):
    """ Return the fileType for a given file. Defaults to data """
    for prefix in FileTypes:
        if t.startswith(prefix):
            return FileTypes[prefix]
    return "data"


def readlink(path):
    return os.path.normpath(os.readlink(path))


def create_files_xml(context, package):
    console_ui.emit_info("Package", "Emitting files.xml for {}".
                         format(package.name))

    files = pisi.files.Files()

    # TODO: Remove reliance on pisi.util functions completely.

    for path in sorted(package.emit_files()):
        if path[0] == '/':
            path = path[1:]

        full_path = os.path.join(context.get_install_dir(), path)
        fpath, hash = pisi.util.calculate_hash(full_path)

        if os.path.islink(fpath):
            fsize = long(len(readlink(full_path)))
            st = os.lstat(fpath)
        else:
            fsize = long(os.path.getsize(full_path))
            st = os.stat(fpath)

        # We don't support this concept right now in ypkg.
        permanent = None
        ftype = get_file_type("/" + path)

        if (stat.S_IMODE(st.st_mode) & stat.S_ISUID):
            # Preserve compatibility with older eopkg implementation
            console_ui.emit_warning("Package", "{} has suid bit set".
                                    format(full_path))

        path = path.decode("latin1").encode('utf-8')
        file_info = pisi.files.FileInfo(path=path, type=ftype,
                                        permanent=permanent, size=fsize,
                                        hash=hash, uid=str(st.st_uid),
                                        gid=str(st.st_gid),
                                        mode=oct(stat.S_IMODE(st.st_mode)))
        files.append(file_info)

    # Temporary!
    files.write("files.xml")
    return files


def create_packager(name, email):
    packager = pisi.specfile.Packager()
    packager.name = unicode(name)
    packager.email = str(email)
    return packager


def metadata_from_package(context, package, files):
    meta = pisi.metadata.MetaData()
    spec = context.spec

    packager = create_packager("FIXME", "FIXME@NOTFIXED.FIXIT??")

    component = "fixme"
    summary = "also fix me"
    description = "seriously, just fix me"

    # We have no histroy?!?!
    # this just copies fields, it doesn't fix every necessary field
    meta.source.name = spec.pkg_name
    meta.source.homepage = spec.pkg_homepage
    meta.source.packager = packager

    meta.package.source = meta.source
    meta.package.source.name = spec.pkg_name
    meta.package.source.packager = packager
    meta.package.name = package.name

    update = pisi.specfile.Update()
    update.comment = "GRAB THE CORRECT COMMENT!!"
    update.name = packager.name
    update.email = packager.email
    update.date = "MAKE ME A DATE!!"
    update.release = str(spec.pkg_release)
    update.version = spec.pkg_version
    meta.package.history.append(update)

    meta.package.summary['en'] = summary
    meta.package.description['en'] = description

    meta.package.partOf = component
    for license in spec.pkg_license:
        meta.package.license.append(str(license))

    for pat in package.emit_files_by_pattern():
        path = pisi.specfile.Path()
        path.path = pat
        path.fileType = get_file_type(pat)
        meta.package.files.append(path)

    # TODO: Add everything else...
    meta.source.version = spec.pkg_version
    meta.source.release = spec.pkg_release
    meta.package.version = spec.pkg_version
    meta.package.release = spec.pkg_release

    return meta


def my_error_cb():
    print("Got called, dafuq")


def create_meta_xml(context, package, files):
    console_ui.emit_info("Package", "Emtiting metadata.xml for {}".
                         format(package.name))

    meta = metadata_from_package(context, package, files)
    config = context.pconfig

    iSize = sum([x.size for x in files.list])
    meta.package.installedSize = iSize

    meta.package.buildHost = config.values.build.build_host

    meta.package.distribution = config.values.general.distribution
    meta.package.distributionRelease = \
        config.values.general.distribution_release
    meta.package.architecture = config.values.general.architecture
    meta.package.packageFormat = pisi.package.Package.default_format

    # print(metadata)
    # TEMP!!
    # metadata.errors = my_error_cb
    meta.write("metadata.xml")
    return meta