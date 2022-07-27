from setuptools import setup

setup(
    name='act',
    version='2.5.0',
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
