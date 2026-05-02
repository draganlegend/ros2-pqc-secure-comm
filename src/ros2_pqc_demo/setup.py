from setuptools import find_packages, setup


package_name = 'ros2_pqc_demo'


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
    maintainer='Codex',
    maintainer_email='demo@example.com',
    description='Demo publisher and echo nodes for ros2-pqc-secure-comm.',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'raw_cmd_pub = ros2_pqc_demo.raw_cmd_pub:main',
            'verified_cmd_echo = ros2_pqc_demo.verified_cmd_echo:main',
        ],
    },
)
