from setuptools import setup

setup(
    name='netbox-interface-sync',
    version='0.1',
    description='Syncing interfaces with the interfaces from device type for NetBox devices',
    author='Victor Golovanenko',
    author_email='drygdryg2014@yandex.com',
    license='GPL-3.0',
    install_requires=[],
    packages=["netbox_interface_sync"],
    package_data={"netbox_interface_sync": ["templates/netbox_interface_sync/*.html"]},
    zip_safe=False
)
