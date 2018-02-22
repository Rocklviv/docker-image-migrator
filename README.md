# Python based CLI
DIM - python based cli that allows to migrate Docker images from Docker Registry V1 to Docker Registry V2 or AWS ECR.

### Requirements
Python packages:
  * docker-py~=1.10.0
  * python-terraform
  * cryptography~=2.1.4
  * urllib3~=1.21.1

Python:
  * 3.4+

In case when you need to migrate images to AWS ECR you need terraform module inplace to create AWS ECR.

### Installation
Clone repository
```
git clone https://github.com/Rocklviv/docker-image-migrator.git -b dev

```
Install CLI into system
```
python setup.py install
```

### Usage
CLI should be run from folder with *.tf files that includes/contain a Terraform AWS ECR module.
```
dim --src <registry-url> --dest localhost --is-ecr True
```

### Author
Denys Chekirda aka Rocklviv

### License
Copyright (C) 2018  Denys Chekirda aka Rocklviv

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.