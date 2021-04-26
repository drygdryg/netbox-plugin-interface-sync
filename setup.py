from setuptools import setup

with open('README.md', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='netbox-interface-sync',
    version='0.1.3',
    description='Syncing interfaces with the interfaces from device type for NetBox devices',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Victor Golovanenko',
    author_email='drygdryg2014@yandex.com',
    license='GPL-3.0',
    install_requires=[],
    packages=["netbox_interface_sync"],
    package_data={"netbox_interface_sync": ["templates/netbox_interface_sync/*.html"]},
    zip_safe=False
)
