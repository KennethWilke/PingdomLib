from distutils.core import setup

setup(
    name='PingdomLib',
    version='1.7',
    author='Kenneth Wilke',
    author_email='kenneth.wilke@rackspace.com',
    packages=['pingdomlib'],
    url='https://github.com/KennethWilke/PingdomLib',
    license='ISC license',
    classifiers=['Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: ISC License (ISCL)',
        'Operating System :: OS Independent',
        'Topic :: System :: Monitoring'],
    description='A documented python library to consume the full pingdom API',
    long_description=open('README.txt').read(),
    install_requires=[
        "requests >= 2.2.1",
        "wsgiref >= 0.1.2",
    ],
)
