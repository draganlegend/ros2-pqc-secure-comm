from setuptools import find_packages, setup


package_name = 'ros2_pqc_verifier'


setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', [f'resource/{package_name}']),
        (f'share/{package_name}', ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Mike Lee',
    maintainer_email='mike32874225@gmail.com',
    description='Verifier node for ros2-pqc-secure-comm.',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'verifier_node = ros2_pqc_verifier.verifier_node:main',
        ],
    },
)
