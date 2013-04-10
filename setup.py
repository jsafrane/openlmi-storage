from distutils.core import setup
setup(
    name='openlmi-storage',
    description='Anaconda Storage Provider',
    author='Jan Safranek',
    author_email='jsafrane@redhat.com',
    url='https://fedorahosted.org/openlmi/',
    version='0.5.1.pre1',
    package_dir={'': 'src'},
    packages=['openlmi.storage', 'openlmi.storage.util'],
    classifiers=[
        'License :: OSI Approved :: GNU Lesser General Public License v2 or later (LGPLv2+)',
        'Operating System :: POSIX :: Linux',
        'Topic :: System :: Systems Administration',
        ]
    )
