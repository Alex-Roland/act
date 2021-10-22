from setuptools import setup
from act.act import version_info

setup(
    name='act',
    version=version_info().VERSION,
    description='Search ACLs for a matching IP',
    author='Alex Roland',
    author_email='alex.roland@peacefulnetworks.com',
    url='https://github.com/Alex-Roland/act',
    license='MIT',
    entry_points={
        'console_scripts': [
            'act=act:main'
        ]
    }
)