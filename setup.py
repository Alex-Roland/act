from setuptools import setup

setup(
    name='ACL Check Tool',
    version='2.3.1',
    description='Search ACLs for a matching IP',
    author='Alex Roland',
    author_email='alex.roland@peacefulnetworks.com',
    url='https://github.com/Alex-Roland/acl-check-tool',
    license='MIT',
    entry_points={
        'console_scripts': [
            'act=act:main'
        ]
    }
)