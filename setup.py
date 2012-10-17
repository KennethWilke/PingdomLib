from distutils.core import setup

setup(
    name='PingdomLib',
    version='0.1.4',
    author='Kenneth Wilke',
    author_email='kenneth.wilke@rackspace.com',
    packages=['pingdomlib'],
    url='https://github.com/KennethWilke/PingdomLib',
    license='ISC license',
    classifiers=['Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: ISC License (ISCL)',
        'Operating System :: OS Independent',
        'Topic :: System :: Monitoring'],
    description='A python library to consume the pingdom API',
    long_description=open('README.txt').read(),
    install_requires=[
        "requests >= 0.14.1",
        "wsgiref >= 0.1.2",
    ],
)
