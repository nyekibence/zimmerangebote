# -*- coding: utf-8 -*-

from setuptools import setup

package_dir = {"": "src"}
packages = ["zimmerangebote"]
package_data = {"": ["*"]}
install_requires = ["pandas>=1.5.1,<2.0.0", "selenium>=4.6.0,<5.0.0"]
setup_kwargs = {
    "name": "zimmerangebote",
    "version": "0.1.0",
    "description": "An application that scrapes room offers",
    "author": "nyekibence",
    "author_email": "nyeki.bence96@gmail.com",
    "package_dir": package_dir,
    "packages": packages,
    "package_data": package_data,
    "install_requires": install_requires,
    "python_requires": ">=3.8,<4",
}

setup(**setup_kwargs)
